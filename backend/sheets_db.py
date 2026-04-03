"""
Google Sheets Database Module
Stores and retrieves application tracking data in Google Sheets
"""
import os
import json
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Google Sheets imports
import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Column headers for the spreadsheet
HEADERS = [
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

SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_ID", "")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")


class GoogleSheetsDB:
    """Google Sheets-backed application tracker."""

    def __init__(self):
        self.client = None
        self.sheet = None
        self._connect()

    def _connect(self):
        """Connect to Google Sheets."""
        try:
            creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
            
            if creds_json:
                # Credentials stored as env var (JSON string)
                creds_dict = json.loads(creds_json)
                creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            elif os.path.exists(CREDENTIALS_FILE):
                # Credentials from file
                creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            else:
                print("[Sheets] No credentials found. Using mock DB.")
                self.sheet = None
                return
            
            self.client = gspread.authorize(creds)
            
            if SPREADSHEET_ID:
                spreadsheet = self.client.open_by_key(SPREADSHEET_ID)
            else:
                # Create new spreadsheet
                spreadsheet = self.client.create("Job Applications Tracker")
                print(f"[Sheets] Created spreadsheet: {spreadsheet.id}")
                print(f"[Sheets] Add GOOGLE_SHEETS_ID={spreadsheet.id} to your .env")
            
            # Get or create worksheet
            try:
                self.sheet = spreadsheet.worksheet("Applications")
            except gspread.WorksheetNotFound:
                self.sheet = spreadsheet.add_worksheet("Applications", rows=1000, cols=len(HEADERS))
                self._init_headers()
            
            print("[Sheets] Connected successfully")
            
        except Exception as e:
            print(f"[Sheets] Connection failed: {e}")
            self.sheet = None

    def _init_headers(self):
        """Initialize header row in sheet."""
        if self.sheet:
            self.sheet.update("A1", [HEADERS])
            # Format header row
            self.sheet.format("A1:J1", {
                "backgroundColor": {"red": 0.1, "green": 0.1, "blue": 0.18},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            })

    def log_application(self, data: dict) -> bool:
        """Log a new application to Google Sheets."""
        if not self.sheet:
            print("[Sheets] Mock: logged application:", data)
            return True
        
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [
                data.get("session_id", ""),
                data.get("name", ""),
                data.get("email", ""),
                data.get("job_title", ""),
                data.get("company", ""),
                data.get("job_url", ""),
                data.get("match_score", 0),
                data.get("status", "Generated"),
                now,
                now,
            ]
            self.sheet.append_row(row)
            print(f"[Sheets] Logged application for {data.get('name')} at {data.get('company')}")
            return True
        except Exception as e:
            print(f"[Sheets] Failed to log: {e}")
            return False

    def update_status(self, session_id: str, status: str) -> bool:
        """Update application status by session ID."""
        if not self.sheet:
            print(f"[Sheets] Mock: updated status for {session_id} to {status}")
            return True
        
        try:
            # Find row by session ID (column A)
            all_rows = self.sheet.get_all_values()
            for i, row in enumerate(all_rows):
                if row and row[0] == session_id:
                    row_num = i + 1  # 1-indexed
                    self.sheet.update_cell(row_num, 8, status)  # Column H = Status
                    self.sheet.update_cell(row_num, 10, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    return True
            return False
        except Exception as e:
            print(f"[Sheets] Failed to update status: {e}")
            return False

    def get_all_applications(self) -> List[dict]:
        """Fetch all applications from Google Sheets."""
        if not self.sheet:
            # Return mock data for development
            return self._mock_applications()
        
        try:
            records = self.sheet.get_all_records()
            return records
        except Exception as e:
            print(f"[Sheets] Failed to fetch: {e}")
            return self._mock_applications()

    def get_stats(self) -> dict:
        """Get dashboard statistics."""
        apps = self.get_all_applications()
        
        total = len(apps)
        applied = sum(1 for a in apps if a.get("Status") == "Applied")
        generated = sum(1 for a in apps if a.get("Status") == "Generated")
        avg_score = sum(int(a.get("Match Score (%)", 0) or 0) for a in apps) / max(total, 1)
        
        return {
            "total": total,
            "applied": applied,
            "generated": generated,
            "avg_match_score": round(avg_score, 1),
            "applications": apps,
        }

    def _mock_applications(self) -> List[dict]:
        """Return mock data when Sheets is not configured."""
        return [
            {
                "Session ID": "a1b2c3d4",
                "Candidate Name": "Alex Johnson",
                "Email": "alex@example.com",
                "Job Title": "Senior Python Developer",
                "Company": "TechCorp Inc",
                "Job URL": "https://example.com/job/123",
                "Match Score (%)": 82,
                "Status": "Applied",
                "Date Applied": "2025-01-15 10:30:00",
                "Last Updated": "2025-01-15 10:31:00",
            },
            {
                "Session ID": "e5f6g7h8",
                "Candidate Name": "Alex Johnson",
                "Email": "alex@example.com",
                "Job Title": "Full Stack Engineer",
                "Company": "StartupXYZ",
                "Job URL": "https://example.com/job/456",
                "Match Score (%)": 74,
                "Status": "Generated",
                "Date Applied": "2025-01-16 14:20:00",
                "Last Updated": "2025-01-16 14:20:00",
            },
            {
                "Session ID": "i9j0k1l2",
                "Candidate Name": "Alex Johnson",
                "Email": "alex@example.com",
                "Job Title": "Backend Developer",
                "Company": "Enterprise Solutions Ltd",
                "Job URL": "https://example.com/job/789",
                "Match Score (%)": 91,
                "Status": "Applied",
                "Date Applied": "2025-01-17 09:15:00",
                "Last Updated": "2025-01-17 09:16:00",
            },
        ]


if __name__ == "__main__":
    db = GoogleSheetsDB()
    print("Stats:", db.get_stats())
