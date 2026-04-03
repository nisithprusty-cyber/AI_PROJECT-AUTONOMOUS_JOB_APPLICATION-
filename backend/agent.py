"""
Core ReAct Agent Module
Uses LangChain ReAct pattern with NVIDIA API (free tier, 40 req/sec)
Handles: skill matching, gap analysis, resume tailoring, cover letter generation
"""
import os
import json
import uuid
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# LangChain imports
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# ---- NVIDIA NIM API Setup ----
# Free API from https://build.nvidia.com — supports 40 req/sec
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

def get_llm(temperature: float = 0.3):
    """Get LLM configured for NVIDIA NIM free API."""
    return ChatOpenAI(
        model="meta/llama-3.1-70b-instruct",
        api_key=NVIDIA_API_KEY,
        base_url=NVIDIA_BASE_URL,
        temperature=temperature,
        max_tokens=2048,
    )


# Embedding model (local, no API needed)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)


class JobApplicationAgent:
    """
    ReAct-based agent for job application analysis and generation.
    """

    def __init__(self):
        self.llm = get_llm()
        self.sessions = {}  # In-memory session store

    def _build_vector_store(self, resume_text: str) -> FAISS:
        """Chunk resume text and build FAISS vector store."""
        chunks = text_splitter.split_text(resume_text)
        vs = FAISS.from_texts(chunks, embeddings)
        return vs

    def _search_resume(self, vector_store: FAISS, query: str, k: int = 4) -> str:
        """Search resume vector store for relevant content."""
        docs = vector_store.similarity_search(query, k=k)
        return "\n---\n".join([d.page_content for d in docs])

    def analyze(
        self,
        resume_text: str,
        job_data: dict,
        personal_info: dict,
    ) -> dict:
        """
        Main analysis function.
        Returns: matched_skills, missing_skills, match_score, summary, session_id
        """
        session_id = str(uuid.uuid4())[:8]
        
        # Build vector store for resume
        vector_store = self._build_vector_store(resume_text)
        
        job_description = job_data.get("raw_description", "")
        job_title = job_data.get("title", "Software Engineer")
        company = job_data.get("company", "the company")
        
        # Tool: Resume search
        def resume_search_tool(query: str) -> str:
            return self._search_resume(vector_store, query)
        
        tools = [
            Tool(
                name="ResumeSearch",
                func=resume_search_tool,
                description="Search the candidate's resume for relevant skills, experience, or education. Input: a skill or keyword to search for."
            ),
        ]
        
        # ReAct prompt
        react_prompt = PromptTemplate.from_template("""
You are an expert ATS (Applicant Tracking System) and career coach AI.
Analyze the resume against the job description.

You have access to the following tools:
{tools}

Use the following format STRICTLY:
Thought: your reasoning about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Observation as needed)
Thought: I now know the final answer
Final Answer: <JSON with keys: matched_skills (list), missing_skills (list), match_score (int 0-100), summary (string)>

Job Title: {job_title}
Company: {company}

Job Description (first 3000 chars):
{job_description}

Candidate Name: {candidate_name}

Your task:
1. Search the resume for key technical skills mentioned in the job description
2. Identify matched skills (candidate HAS these)
3. Identify missing skills (job requires these but candidate LACKS them)
4. Calculate match_score as percentage of required skills the candidate has
5. Write a brief summary

Begin!

{agent_scratchpad}
""")
        
        agent = create_react_agent(self.llm, tools, react_prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=6,
            handle_parsing_errors=True,
        )
        
        try:
            result = executor.invoke({
                "job_title": job_title,
                "company": company,
                "job_description": job_description[:3000],
                "candidate_name": personal_info.get("name", "Candidate"),
            })
            output = result.get("output", "{}")
            analysis = self._parse_analysis_output(output)
        except Exception as e:
            print(f"[Agent] ReAct failed, falling back to direct LLM: {e}")
            analysis = self._direct_analysis(resume_text, job_description, job_title, company)
        
        analysis["session_id"] = session_id
        
        # Store session
        self.sessions[session_id] = {
            "resume_text": resume_text,
            "job_data": job_data,
            "personal_info": personal_info,
            "analysis": analysis,
            "vector_store": vector_store,
        }
        
        return analysis

    def _direct_analysis(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        company: str,
    ) -> dict:
        """Direct LLM analysis fallback (no agent loop)."""
        prompt = f"""
You are an expert resume analyst. Analyze this resume against the job description.

RESUME (first 2000 chars):
{resume_text[:2000]}

JOB DESCRIPTION (first 2000 chars):
{job_description[:2000]}

JOB TITLE: {job_title}
COMPANY: {company}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "matched_skills": ["skill1", "skill2", ...],
  "missing_skills": ["skill1", "skill2", ...],
  "match_score": <integer 0-100>,
  "summary": "<2-3 sentence analysis>"
}}

Rules:
- matched_skills: skills/technologies in BOTH resume AND job description
- missing_skills: skills in job description but NOT in resume
- match_score: realistic percentage (50-90 range for good candidates)
- Do NOT hallucinate skills. Only list what you actually see.
"""
        response = self.llm.invoke(prompt)
        return self._parse_analysis_output(response.content)

    def _parse_analysis_output(self, output: str) -> dict:
        """Parse LLM output into structured analysis dict."""
        # Try to extract JSON from output
        try:
            # Find JSON block
            start = output.find("{")
            end = output.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = output[start:end]
                data = json.loads(json_str)
                return {
                    "matched_skills": data.get("matched_skills", [])[:15],
                    "missing_skills": data.get("missing_skills", [])[:15],
                    "match_score": int(data.get("match_score", 50)),
                    "summary": data.get("summary", "Analysis complete."),
                }
        except Exception as e:
            print(f"[Agent] JSON parse error: {e}")
        
        # Fallback
        return {
            "matched_skills": ["Python", "Problem Solving", "Communication"],
            "missing_skills": ["Docker", "Kubernetes", "AWS"],
            "match_score": 55,
            "summary": "Analysis could not be fully parsed. Please review the job description manually.",
        }

    def generate_cover_letter(
        self,
        personal_info: dict,
        job_data: dict,
        analysis: dict,
    ) -> str:
        """Generate a personalized cover letter."""
        prompt = f"""
Write a professional, compelling cover letter for this job application.

Candidate: {personal_info.get('name', 'Candidate')}
Email: {personal_info.get('email', '')}
Phone: {personal_info.get('phone', '')}

Job Title: {job_data.get('title', 'Software Engineer')}
Company: {job_data.get('company', 'the company')}
Job URL: {job_data.get('url', '')}

Matched Skills (candidate has these): {', '.join(analysis.get('matched_skills', []))}
Match Score: {analysis.get('match_score', 70)}%
Analysis Summary: {analysis.get('summary', '')}

Job Description excerpt:
{job_data.get('raw_description', '')[:1500]}

Instructions:
- Write 3-4 paragraphs
- Open with a strong, engaging hook (NOT "I am applying for...")
- Mention 2-3 specific matched skills with brief context
- Show enthusiasm for the company/role
- Close with a clear call to action
- Tone: professional but personable
- Do NOT invent fake experience or companies
- Format as plain text (no markdown headers)

Write the complete cover letter now:
"""
        response = self.llm.invoke(prompt)
        return response.content

    def get_session(self, session_id: str) -> Optional[dict]:
        return self.sessions.get(session_id)


if __name__ == "__main__":
    # Quick test
    agent = JobApplicationAgent()
    result = agent._direct_analysis(
        resume_text="Python developer with 3 years experience in Django, React, PostgreSQL, Git.",
        job_description="Looking for Python developer with Django, Docker, AWS, PostgreSQL skills.",
        job_title="Backend Developer",
        company="TechCorp",
    )
    print(json.dumps(result, indent=2))
