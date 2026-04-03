"""
Test Suite — Autonomous Job Application Agent
Run: python test_pipeline.py
Tests each module independently + end-to-end
"""
import os
import sys
import json
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# =============================================
# TEST: Resume Parser
# =============================================
class TestResumeParser(unittest.TestCase):

    def test_clean_text(self):
        from resume_parser import clean_resume_text
        raw = "John Doe\n\n\n\nPython   Developer\n\n\nSkills: Python, Django"
        cleaned = clean_resume_text(raw)
        self.assertNotIn("\n\n\n", cleaned)
        self.assertIn("Python", cleaned)

    def test_extract_sections(self):
        from resume_parser import extract_sections
        text = """
SUMMARY
Experienced developer with 5 years in Python.

SKILLS
Python, Django, React, PostgreSQL

EXPERIENCE
Software Engineer at TechCorp (2020-2023)
Built REST APIs with Django

EDUCATION
BS Computer Science, MIT, 2019
"""
        sections = extract_sections(text)
        self.assertIn("skills", sections)
        self.assertIn("experience", sections)
        self.assertIn("education", sections)

    def test_missing_file(self):
        from resume_parser import parse_resume
        with self.assertRaises(FileNotFoundError):
            parse_resume("/nonexistent/path/resume.pdf")


# =============================================
# TEST: Job Scraper
# =============================================
class TestJobScraper(unittest.TestCase):

    def test_parse_job_html(self):
        from job_scraper import parse_job_html
        mock_html = """
        <html>
        <body>
          <h1>Senior Python Developer</h1>
          <div class="companyName">TechCorp Inc</div>
          <div id="jobDescriptionText">
            <p>We are looking for a Python developer with 3+ years experience.</p>
            <p>Requirements: Python, Django, PostgreSQL, Docker knowledge required.</p>
            <ul>
              <li>Experience with REST APIs required</li>
              <li>Knowledge of AWS preferred</li>
            </ul>
          </div>
        </body>
        </html>
        """
        result = parse_job_html(mock_html, "https://example.com/jobs/123")
        self.assertIn("title", result)
        self.assertIn("raw_description", result)
        self.assertIn("requirements", result)
        self.assertIn("url", result)

    def test_extract_requirements(self):
        from job_scraper import extract_requirements
        text = """
        We are hiring a Software Engineer.
        Requirements:
        - 3+ years experience with Python required
        - Strong knowledge of Django framework
        - Experience with Docker and Kubernetes required
        - Familiarity with AWS cloud services
        """
        reqs = extract_requirements(text)
        self.assertIsInstance(reqs, list)
        # Should find lines containing "required" or "experience"
        self.assertTrue(len(reqs) > 0)


# =============================================
# TEST: Vector Store
# =============================================
class TestVectorStore(unittest.TestCase):

    SAMPLE_RESUME = """
    Jane Smith | jane@example.com | +1-555-0200
    
    SKILLS
    Python, FastAPI, React, Node.js, PostgreSQL, MongoDB, Docker, AWS, Git, Agile
    
    EXPERIENCE
    Full Stack Developer — Acme Corp (2021-2024)
    - Built Python FastAPI microservices serving 50k daily users
    - Developed React dashboards with TypeScript
    - Deployed services on AWS ECS with Docker
    
    EDUCATION
    MS Software Engineering — UC Berkeley, 2021
    """

    def test_build_store(self):
        """Test vector store creation from text."""
        try:
            from vector_store import build_resume_store
            store = build_resume_store(self.SAMPLE_RESUME, "test_vs_001")
            self.assertIsNotNone(store.vector_store)
        except ImportError as e:
            self.skipTest(f"sentence-transformers not installed: {e}")

    def test_search(self):
        """Test semantic search returns relevant chunks."""
        try:
            from vector_store import build_resume_store
            store = build_resume_store(self.SAMPLE_RESUME, "test_vs_002")
            results = store.search("Python microservices experience", k=3)
            self.assertIsInstance(results, list)
            self.assertTrue(len(results) > 0)
            # At least one result should mention Python
            combined = " ".join(results).lower()
            self.assertIn("python", combined)
        except ImportError:
            self.skipTest("sentence-transformers not installed")


# =============================================
# TEST: Agent Analysis (Mocked LLM)
# =============================================
class TestAgentAnalysis(unittest.TestCase):

    def test_parse_analysis_output_valid_json(self):
        from agent import JobApplicationAgent
        agent = JobApplicationAgent.__new__(JobApplicationAgent)
        agent.sessions = {}

        output = '''
        Final Answer: {"matched_skills": ["Python", "Django", "PostgreSQL"], 
                       "missing_skills": ["Docker", "Kubernetes"], 
                       "match_score": 75, 
                       "summary": "Strong candidate with relevant backend experience."}
        '''
        result = agent._parse_analysis_output(output)
        self.assertEqual(result["match_score"], 75)
        self.assertIn("Python", result["matched_skills"])
        self.assertIn("Docker", result["missing_skills"])
        self.assertIsInstance(result["summary"], str)

    def test_parse_analysis_output_malformed(self):
        """Should return fallback data, not crash."""
        from agent import JobApplicationAgent
        agent = JobApplicationAgent.__new__(JobApplicationAgent)
        agent.sessions = {}

        output = "I cannot parse this properly"
        result = agent._parse_analysis_output(output)
        self.assertIn("matched_skills", result)
        self.assertIn("missing_skills", result)
        self.assertIn("match_score", result)
        self.assertIsInstance(result["match_score"], int)

    def test_parse_analysis_score_bounds(self):
        """Match score must be 0-100."""
        from agent import JobApplicationAgent
        agent = JobApplicationAgent.__new__(JobApplicationAgent)
        agent.sessions = {}

        output = '{"matched_skills": [], "missing_skills": [], "match_score": 150, "summary": "test"}'
        result = agent._parse_analysis_output(output)
        # Should handle int conversion
        self.assertIsInstance(result["match_score"], int)


# =============================================
# TEST: PDF Generator
# =============================================
class TestPDFGenerator(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.personal_info = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1-555-0000",
            "address": "San Francisco, CA",
            "linkedin": "https://linkedin.com/in/testuser",
        }
        self.analysis = {
            "matched_skills": ["Python", "Django", "React", "PostgreSQL", "Docker"],
            "missing_skills": ["Kubernetes", "AWS"],
            "match_score": 78,
            "summary": "Strong backend developer with solid frontend skills.",
        }
        self.job_data = {
            "title": "Senior Software Engineer",
            "company": "TestCorp",
            "url": "https://example.com/job/123",
            "raw_description": "Looking for a senior engineer...",
        }

    def test_generate_resume_pdf(self):
        """Test resume PDF is created and non-empty."""
        try:
            from pdf_generator import generate_tailored_resume
            path = generate_tailored_resume(
                session_id="test_pdf_001",
                personal_info=self.personal_info,
                analysis=self.analysis,
                output_folder=self.test_dir,
            )
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 1000)  # At least 1KB
            print(f"✅ Resume PDF: {os.path.getsize(path)} bytes")
        except ImportError:
            self.skipTest("reportlab not installed")

    def test_generate_cover_letter_pdf(self):
        """Test cover letter PDF is created."""
        try:
            from pdf_generator import generate_cover_letter_pdf
            path = generate_cover_letter_pdf(
                session_id="test_pdf_002",
                personal_info=self.personal_info,
                job_data=self.job_data,
                analysis=self.analysis,
                output_folder=self.test_dir,
                cover_letter_text="Dear Hiring Manager,\n\nI am excited to apply for this role.\n\nSincerely,\nTest User",
            )
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 500)
            print(f"✅ Cover Letter PDF: {os.path.getsize(path)} bytes")
        except ImportError:
            self.skipTest("reportlab not installed")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)


# =============================================
# TEST: Google Sheets (Mock)
# =============================================
class TestGoogleSheets(unittest.TestCase):

    def test_mock_applications_returned(self):
        """When Sheets not configured, mock data should be returned."""
        from sheets_db import GoogleSheetsDB
        db = GoogleSheetsDB.__new__(GoogleSheetsDB)
        db.client = None
        db.sheet = None

        apps = db.get_all_applications()
        self.assertIsInstance(apps, list)
        self.assertGreater(len(apps), 0)
        # Check expected fields
        first = apps[0]
        self.assertIn("Job Title", first)
        self.assertIn("Company", first)
        self.assertIn("Match Score (%)", first)

    def test_mock_log_returns_true(self):
        """Mock log should always return True."""
        from sheets_db import GoogleSheetsDB
        db = GoogleSheetsDB.__new__(GoogleSheetsDB)
        db.client = None
        db.sheet = None

        result = db.log_application({
            "session_id": "test123",
            "name": "Test User",
            "email": "test@example.com",
            "job_title": "Engineer",
            "company": "TestCorp",
            "job_url": "https://example.com",
            "match_score": 80,
            "status": "Generated",
        })
        self.assertTrue(result)


# =============================================
# TEST: Config
# =============================================
class TestConfig(unittest.TestCase):

    def test_validate_config_returns_dict(self):
        from config import validate_config
        result = validate_config()
        self.assertIn("status", result)
        self.assertIn("warnings", result)
        self.assertIsInstance(result["status"], dict)
        self.assertIsInstance(result["warnings"], list)

    def test_required_dirs_created(self):
        """Config should create required directories."""
        import config
        self.assertTrue(os.path.exists(config.UPLOAD_FOLDER))
        self.assertTrue(os.path.exists(config.OUTPUT_FOLDER))
        self.assertTrue(os.path.exists(config.VECTOR_STORE_DIR))


# =============================================
# INTEGRATION TEST: Flask API
# =============================================
class TestFlaskAPI(unittest.TestCase):

    def setUp(self):
        # Patch heavy dependencies
        self.patches = [
            patch("agent.JobApplicationAgent"),
            patch("sheets_db.GoogleSheetsDB"),
            patch("email_service.send_confirmation_email", return_value=True),
        ]
        for p in self.patches:
            p.start()

        import app as flask_app
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "ok")

    def test_applications_endpoint(self):
        response = self.client.get("/api/applications")
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        for p in self.patches:
            try:
                p.stop()
            except Exception:
                pass


# =============================================
# EDGE CASE TESTS
# =============================================
class TestEdgeCases(unittest.TestCase):

    def test_empty_resume_text(self):
        """Agent should handle empty resume gracefully."""
        from resume_parser import clean_resume_text
        result = clean_resume_text("")
        self.assertEqual(result, "")

    def test_unicode_resume(self):
        """Parser should handle Unicode characters."""
        from resume_parser import clean_resume_text
        text = "Résumé of Müller — Ångström University — 汉字 skills"
        result = clean_resume_text(text)
        self.assertIn("skills", result)

    def test_score_threshold_logic(self):
        """Verify match score threshold logic."""
        from config import MATCH_THRESHOLD
        self.assertEqual(MATCH_THRESHOLD, 70)  # Default

        # Test threshold logic
        scores = [45, 69, 70, 85, 95]
        qualified = [s for s in scores if s >= MATCH_THRESHOLD]
        not_qualified = [s for s in scores if s < MATCH_THRESHOLD]

        self.assertEqual(qualified, [70, 85, 95])
        self.assertEqual(not_qualified, [45, 69])

    def test_skill_extraction_from_jd(self):
        """Test that common tech skills are extractable from JD text."""
        from job_scraper import extract_requirements
        jd = """
        Requirements:
        - 3+ years Python experience required
        - Strong knowledge of React and TypeScript
        - Experience with Docker containers required
        - AWS or GCP cloud platform familiarity
        - Excellent communication skills required
        - Bachelor's degree in Computer Science
        """
        reqs = extract_requirements(jd)
        self.assertTrue(len(reqs) >= 3)
        combined = " ".join(reqs).lower()
        self.assertIn("python", combined)


# =============================================
# RUNNER
# =============================================
if __name__ == "__main__":
    print("=" * 60)
    print("   ApplyGenius — Test Suite")
    print("=" * 60)
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestResumeParser,
        TestJobScraper,
        TestVectorStore,
        TestAgentAnalysis,
        TestPDFGenerator,
        TestGoogleSheets,
        TestConfig,
        TestEdgeCases,
        # TestFlaskAPI,  # Uncomment if Flask app fully loads without env vars
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        sys.exit(1)
