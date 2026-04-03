# 🎯 ApplyGenius — Autonomous Job Application Agent

> Transform a 3–5 hour job application process into **seconds**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 Resume Parsing | PyMuPDF extracts structured text from your PDF |
| 🌐 Job Scraping | BeautifulSoup + Playwright scrape any job URL |
| 🤖 ReAct Agent | LangChain ReAct loop with FAISS vector store |
| 📊 Match Score | AI calculates ATS compatibility percentage |
| ✅ Skill Matching | Identifies matched AND missing skills |
| 📝 PDF Generation | Professional tailored resume + cover letter via ReportLab |
| 📤 Direct Apply | Opens job URL + sends confirmation email |
| 📋 Dashboard | Google Sheets-backed application tracker |
| 📧 Email Alerts | Gmail SMTP confirmation on every application |

---

## 🏗️ Architecture

```
User Input (PDF + URL)
        │
        ▼
┌─────────────────────────────────────────────────┐
│                 Flask Backend                   │
│                                                 │
│  1. PyMuPDF ──► Resume Text                     │
│  2. BeautifulSoup ──► Job JSON                  │
│  3. FAISS Vector Store ──► Resume Chunks        │
│                                                 │
│  4. LangChain ReAct Agent                       │
│     ┌─────────────────────────────────┐         │
│     │  Thought → Action → Observation │         │
│     │  Tools: ResumeSearch, WebSearch │         │
│     └─────────────────────────────────┘         │
│                                                 │
│  5. Match Score + Skill Gap Analysis            │
│  6. ReportLab ──► Tailored Resume PDF           │
│  7. ReportLab ──► Cover Letter PDF              │
│  8. Google Sheets ──► Application Log           │
│  9. Gmail SMTP ──► Confirmation Email           │
└─────────────────────────────────────────────────┘
        │
        ▼
   Frontend UI (HTML + CSS + JS)
   - Score Ring Animation
   - Skills Comparison
   - Document Preview & Download
   - Applications Dashboard
```

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone <your-repo>
cd autonomous-job-agent
bash setup.sh
```

### 2. Get Free NVIDIA API Key
1. Go to **https://build.nvidia.com**
2. Sign up (free)
3. Navigate to **API Keys** → Create Key
4. Copy and paste into `backend/.env` as `NVIDIA_API_KEY`

> 💡 NVIDIA NIM supports **40 requests/second** on the free tier using `meta/llama-3.1-70b-instruct`

### 3. Setup Google Sheets (Database)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project → Enable **Google Sheets API** + **Google Drive API**
3. Create **Service Account** → Download JSON credentials
4. Save as `backend/credentials.json`
5. Create a Google Sheet → Copy the Sheet ID from the URL
6. Share the sheet with your service account email
7. Add `GOOGLE_SHEETS_ID=<your-id>` to `backend/.env`

### 4. Configure Email (Optional)
1. Enable 2FA on your Gmail account
2. Go to: Google Account → Security → App Passwords
3. Generate App Password → Copy 16-char code
4. Add to `backend/.env`:
   ```
   EMAIL_SENDER=your@gmail.com
   EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

### 5. Run the App
```bash
bash run.sh
```

Then open: **http://localhost:3000**

---

## 📁 File Structure

```
autonomous-job-agent/
├── backend/
│   ├── app.py              # Flask API server
│   ├── agent.py            # LangChain ReAct agent
│   ├── resume_parser.py    # PyMuPDF PDF parser
│   ├── job_scraper.py      # BeautifulSoup/Playwright scraper
│   ├── pdf_generator.py    # ReportLab PDF generation
│   ├── sheets_db.py        # Google Sheets database
│   ├── email_service.py    # Gmail SMTP email service
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment template
│
├── frontend/
│   ├── index.html          # Main UI (single page app)
│   ├── styles.css          # Deep Space design system
│   └── app.js              # Frontend logic
│
├── setup.sh                # One-click setup
├── run.sh                  # Start app
└── README.md               # This file
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Analyze resume vs job |
| `POST` | `/api/generate` | Generate PDFs |
| `POST` | `/api/send-confirmation` | Send email |
| `GET` | `/api/download/<file>` | Download PDF |
| `GET` | `/api/applications` | Get all applications |
| `POST` | `/api/cover-letter-text` | Get cover letter text |

---

## 🎨 UI Flow

```
Form (Personal Details + Resume + Job URL)
        │
        ▼
    [Analyze Button]
        │
        ▼
Loading Animation (5-step progress)
        │
        ▼
Results Panel
   ├── Score Ring (animated, 0-100%)
   ├── Matched Skills (green tags)
   ├── Missing Skills (red tags)
   └── Job Description Preview
        │
        ├── Score ≥ 70%? ──► Generate Docs → Preview → Download → Apply → Email
        └── Score < 70%? ──► Skill Gap Resources with course links
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | NVIDIA NIM (meta/llama-3.1-70b-instruct) — free, 40 req/s |
| **Agent** | LangChain ReAct + FAISS vector store |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 (local) |
| **PDF Parse** | PyMuPDF (fitz) |
| **Web Scrape** | BeautifulSoup4 + Playwright |
| **PDF Gen** | ReportLab |
| **Database** | Google Sheets (via gspread) |
| **Email** | Gmail SMTP |
| **Backend** | Flask + Flask-CORS |
| **Frontend** | Vanilla HTML/CSS/JS (no framework) |
| **Fonts** | Syne (display) + DM Sans (body) |

---

## ⚙️ Environment Variables

```env
# Required
NVIDIA_API_KEY=              # From https://build.nvidia.com
GOOGLE_SHEETS_ID=            # Google Sheet ID
GOOGLE_CREDENTIALS_FILE=     # Path to service account JSON

# Optional
EMAIL_SENDER=                # Gmail address
EMAIL_APP_PASSWORD=          # Gmail App Password
```

---

## 🔧 Troubleshooting

**CORS errors:** Make sure Flask is running on port 5000 and CORS is enabled (it is by default).

**Scraping fails:** Paste job description manually in the "Job Description" field as fallback.

**LLM errors:** Verify `NVIDIA_API_KEY` is correct and has available credits.

**Google Sheets errors:** Ensure service account has Editor access to the sheet.

**PDF download fails:** Check `backend/outputs/` directory exists and is writable.

---

## 📈 Day-by-Day Implementation Status

| Day | Status | Feature |
|---|---|---|
| Day 1 | ✅ | Architecture, project setup, team roles |
| Day 2 | ✅ | PyMuPDF parsing, BeautifulSoup scraping, LLM JSON extraction |
| Day 3 | ✅ | ReAct agent, FAISS vector store, skill matching |
| Day 4 | ✅ | ReportLab PDFs, Google Sheets tracking, end-to-end pipeline |
| Day 5 | ✅ | Dashboard UI, email notifications, polish |
| Day 6 | 🎯 | Live demo, Q&A defense |
