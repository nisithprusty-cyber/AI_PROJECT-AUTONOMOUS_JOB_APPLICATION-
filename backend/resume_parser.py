"""
Resume Parser Module
Uses PyMuPDF (fitz) to extract text from PDF resumes
"""
import fitz  # PyMuPDF
import re
import os


def parse_resume(pdf_path: str) -> str:
    """
    Parse a PDF resume and extract clean text.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume file not found: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    full_text = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        full_text.append(text)
    
    doc.close()
    
    combined = "\n".join(full_text)
    cleaned = clean_resume_text(combined)
    return cleaned


def clean_resume_text(text: str) -> str:
    """Clean and normalize extracted resume text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove null characters
    text = text.replace('\x00', '')
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split('\n')]
    lines = [line for line in lines if line]  # Remove empty lines
    return '\n'.join(lines)


def extract_sections(text: str) -> dict:
    """
    Attempt to extract structured sections from resume text.
    Returns dict with keys: skills, experience, education, summary
    """
    sections = {
        "skills": "",
        "experience": "",
        "education": "",
        "summary": "",
        "full_text": text
    }
    
    section_patterns = {
        "skills": r"(?i)(skills|technical skills|core competencies|technologies)[\s\S]*?(?=\n[A-Z]{2,}|\Z)",
        "experience": r"(?i)(experience|work experience|employment|work history)[\s\S]*?(?=\n[A-Z]{2,}|\Z)",
        "education": r"(?i)(education|academic|qualifications)[\s\S]*?(?=\n[A-Z]{2,}|\Z)",
        "summary": r"(?i)(summary|profile|objective|about)[\s\S]*?(?=\n[A-Z]{2,}|\Z)",
    }
    
    for section, pattern in section_patterns.items():
        match = re.search(pattern, text)
        if match:
            sections[section] = match.group(0)[:1000]
    
    return sections


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) > 1:
        text = parse_resume(sys.argv[1])
        print(text[:500])
