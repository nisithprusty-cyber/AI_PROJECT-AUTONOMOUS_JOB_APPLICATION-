"""
Centralized Configuration
All settings, constants, and environment loading in one place
"""
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================
# API KEYS & EXTERNAL SERVICES
# =============================================

# NVIDIA NIM — free tier, 40 req/sec
# Get yours: https://build.nvidia.com
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")

# OpenAI fallback (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# =============================================
# GOOGLE SHEETS
# =============================================
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")  # JSON string alternative

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEETS_WORKSHEET_NAME = "Applications"
SHEETS_HEADERS = [
    "Session ID",
    "Candidate Name",
    "Email",
    "Job Title",
    "Company",
    "Job URL",
    "Match Score (%)",
    "Status",
    "Date Applied",
    "Last Updated",
]

# =============================================
# EMAIL (Gmail SMTP)
# =============================================
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# =============================================
# FILE PATHS
# =============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_stores")

# Ensure dirs exist
for d in [UPLOAD_FOLDER, OUTPUT_FOLDER, VECTOR_STORE_DIR]:
    os.makedirs(d, exist_ok=True)

# =============================================
# AGENT SETTINGS
# =============================================
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "6"))

# Embedding model (local, no API cost)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# RAG settings
CHUNK_SIZE = 400
CHUNK_OVERLAP = 60
RETRIEVAL_K = 5

# =============================================
# MATCH SCORE THRESHOLD
# =============================================
MATCH_THRESHOLD = int(os.getenv("MATCH_THRESHOLD", "70"))  # >= this → qualify for application

# =============================================
# WEB SCRAPING
# =============================================
SCRAPER_TIMEOUT = 15  # seconds
SCRAPER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
MAX_JOB_DESCRIPTION_LENGTH = 5000

# =============================================
# FLASK
# =============================================
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
FLASK_PORT = int(os.getenv("PORT", "5000"))
FLASK_HOST = os.getenv("HOST", "0.0.0.0")
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload

# =============================================
# PDF GENERATION
# =============================================
RESUME_COLORS = {
    "primary": "#1a1a2e",
    "accent": "#e94560",
    "text": "#2d2d2d",
    "muted": "#6c757d",
    "white": "#ffffff",
    "light_bg": "#f8f9fa",
}

# =============================================
# VALIDATION
# =============================================
def validate_config() -> dict:
    """Check which services are configured. Returns status dict."""
    status = {
        "nvidia_api": bool(NVIDIA_API_KEY),
        "google_sheets": bool(GOOGLE_SHEETS_ID) and (
            bool(GOOGLE_CREDENTIALS_JSON) or os.path.exists(GOOGLE_CREDENTIALS_FILE)
        ),
        "email": bool(EMAIL_SENDER) and bool(EMAIL_APP_PASSWORD),
        "openai_fallback": bool(OPENAI_API_KEY),
    }

    warnings = []
    if not status["nvidia_api"]:
        warnings.append("⚠️  NVIDIA_API_KEY not set. Get free key at https://build.nvidia.com")
    if not status["google_sheets"]:
        warnings.append("⚠️  Google Sheets not configured. App will use mock data.")
    if not status["email"]:
        warnings.append("⚠️  Email not configured. Confirmation emails will be skipped.")

    return {"status": status, "warnings": warnings}


if __name__ == "__main__":
    cfg = validate_config()
    print("Configuration Status:")
    for k, v in cfg["status"].items():
        icon = "✅" if v else "❌"
        print(f"  {icon} {k}")
    if cfg["warnings"]:
        print("\nWarnings:")
        for w in cfg["warnings"]:
            print(f"  {w}")
