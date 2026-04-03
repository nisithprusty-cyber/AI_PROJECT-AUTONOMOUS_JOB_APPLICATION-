"""
Vector Store Manager
Handles FAISS vector store creation, persistence, and querying
Used by the ReAct agent for RAG-based resume search
"""
import os
import json
import pickle
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# ---- Embedding model (local, no API cost) ----
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
STORE_DIR = "vector_stores"

_embeddings_instance = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Lazy-load embeddings (singleton)."""
    global _embeddings_instance
    if _embeddings_instance is None:
        print("[VectorStore] Loading embedding model...")
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("[VectorStore] Embedding model loaded.")
    return _embeddings_instance


class ResumeVectorStore:
    """
    Manages FAISS vector store for a candidate's resume.
    Supports creation from text, persistence to disk, and semantic search.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.store_path = os.path.join(STORE_DIR, session_id)
        self.vector_store: Optional[FAISS] = None
        self.embeddings = get_embeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=60,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        os.makedirs(STORE_DIR, exist_ok=True)

    def build_from_text(self, resume_text: str, metadata: dict = None) -> "ResumeVectorStore":
        """
        Chunk resume text and build FAISS vector store.

        Args:
            resume_text: Full text of the resume
            metadata: Optional metadata dict (name, email, etc.)

        Returns:
            self (for chaining)
        """
        metadata = metadata or {}
        chunks = self.text_splitter.split_text(resume_text)

        if not chunks:
            raise ValueError("No text chunks produced from resume.")

        print(f"[VectorStore] Building store with {len(chunks)} chunks...")

        docs = [
            Document(
                page_content=chunk,
                metadata={**metadata, "chunk_index": i, "session_id": self.session_id},
            )
            for i, chunk in enumerate(chunks)
        ]

        self.vector_store = FAISS.from_documents(docs, self.embeddings)
        print(f"[VectorStore] Store built successfully.")
        return self

    def save(self) -> str:
        """Persist vector store to disk."""
        if not self.vector_store:
            raise RuntimeError("No vector store to save.")
        os.makedirs(self.store_path, exist_ok=True)
        self.vector_store.save_local(self.store_path)
        print(f"[VectorStore] Saved to {self.store_path}")
        return self.store_path

    def load(self) -> bool:
        """Load vector store from disk. Returns True if successful."""
        if os.path.exists(self.store_path):
            try:
                self.vector_store = FAISS.load_local(
                    self.store_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                print(f"[VectorStore] Loaded from {self.store_path}")
                return True
            except Exception as e:
                print(f"[VectorStore] Failed to load: {e}")
        return False

    def search(self, query: str, k: int = 5, score_threshold: float = 0.3) -> List[str]:
        """
        Semantic search over resume chunks.

        Args:
            query: Search query (e.g., "Python experience", "machine learning skills")
            k: Number of results to return
            score_threshold: Minimum relevance score (0-1)

        Returns:
            List of relevant text chunks
        """
        if not self.vector_store:
            return []

        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            # Filter by score threshold (lower L2 distance = more similar)
            filtered = [doc.page_content for doc, score in results if score < (1 - score_threshold) * 2]
            return filtered if filtered else [doc.page_content for doc, _ in results[:2]]
        except Exception as e:
            print(f"[VectorStore] Search error: {e}")
            # Fallback to basic search
            docs = self.vector_store.similarity_search(query, k=k)
            return [d.page_content for d in docs]

    def search_formatted(self, query: str, k: int = 4) -> str:
        """Search and return formatted string for LLM consumption."""
        results = self.search(query, k=k)
        if not results:
            return "No relevant resume content found."
        return "\n---\n".join(results)

    def get_all_skills_context(self) -> str:
        """Get resume sections most likely to contain skills."""
        queries = [
            "technical skills programming languages frameworks",
            "work experience projects achievements",
            "education certifications degrees",
            "tools technologies databases cloud",
        ]
        all_results = set()
        for q in queries:
            results = self.search(q, k=3)
            all_results.update(results)
        return "\n---\n".join(list(all_results)[:8])

    def delete(self):
        """Remove vector store from disk."""
        import shutil
        if os.path.exists(self.store_path):
            shutil.rmtree(self.store_path)
            print(f"[VectorStore] Deleted {self.store_path}")


# ---- Convenience function ----
def build_resume_store(resume_text: str, session_id: str, persist: bool = False) -> ResumeVectorStore:
    """One-liner to build a resume vector store."""
    store = ResumeVectorStore(session_id)
    store.build_from_text(resume_text)
    if persist:
        store.save()
    return store


if __name__ == "__main__":
    # Quick smoke test
    sample = """
    John Doe | john@example.com | +1-555-0100 | San Francisco, CA
    
    SKILLS
    Python, Django, FastAPI, React, TypeScript, PostgreSQL, Redis, Docker, AWS, Git
    
    EXPERIENCE
    Senior Software Engineer — TechCorp (2021–Present)
    - Built microservices with Django and FastAPI handling 10k req/day
    - Reduced API latency by 40% through Redis caching
    - Led migration from monolith to Docker-based microservices
    
    Software Engineer — StartupXYZ (2019–2021)
    - Developed React frontend for SaaS dashboard (50k users)
    - Designed PostgreSQL schema for multi-tenant architecture
    
    EDUCATION
    BS Computer Science — Stanford University, 2019
    """

    store = build_resume_store(sample, "test_session_001")
    results = store.search_formatted("Python web development experience")
    print("Search results:\n", results)
    print("\nAll skills context:\n", store.get_all_skills_context()[:500])
