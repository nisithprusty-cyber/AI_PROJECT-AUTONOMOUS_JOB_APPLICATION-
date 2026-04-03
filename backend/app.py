from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import traceback
from dotenv import load_dotenv

load_dotenv()

import config
from resume_parser import parse_resume
from job_scraper import scrape_job_posting
from agent import JobApplicationAgent
from pdf_generator import generate_tailored_resume, generate_cover_letter_pdf
from sheets_db import GoogleSheetsDB
from email_service import send_confirmation_email

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
CORS(app)

db = GoogleSheetsDB()
agent = JobApplicationAgent()

UPLOAD_FOLDER = config.UPLOAD_FOLDER
OUTPUT_FOLDER = config.OUTPUT_FOLDER


@app.route("/api/health", methods=["GET"])
def health():
    cfg = config.validate_config()
    return jsonify({"status": "ok", "message": "Autonomous Job Agent API is running", "services": cfg["status"]})


@app.route("/api/parse-resume", methods=["POST"])
def parse_resume_preview():
    try:
        resume_file = request.files.get("resume")
        if not resume_file:
            return jsonify({"error": "No file"}), 400
        save_path = os.path.join(UPLOAD_FOLDER, "preview_" + resume_file.filename)
        resume_file.save(save_path)
        text = parse_resume(save_path)
        return jsonify({"success": True, "text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Main endpoint: accepts resume PDF + job URL + personal details
    Returns: match score, matched skills, missing skills
    """
    try:
        # Personal details
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        phone = request.form.get("phone", "")
        address = request.form.get("address", "")
        linkedin = request.form.get("linkedin", "")
        portfolio = request.form.get("portfolio", "")

        # Job details
        job_url = request.form.get("job_url", "")
        job_description_manual = request.form.get("job_description", "")

        # Resume file
        resume_file = request.files.get("resume")
        if not resume_file:
            return jsonify({"error": "Resume file is required"}), 400

        resume_path = os.path.join(UPLOAD_FOLDER, resume_file.filename)
        resume_file.save(resume_path)

        # Step 1: Parse resume
        resume_text = parse_resume(resume_path)

        # Step 2: Scrape job posting
        if job_url:
            job_data = scrape_job_posting(job_url)
        else:
            job_data = {"raw_description": job_description_manual, "url": "manual"}

        # Step 3: Run ReAct agent analysis
        analysis = agent.analyze(
            resume_text=resume_text,
            job_data=job_data,
            personal_info={
                "name": name,
                "email": email,
                "phone": phone,
                "address": address,
                "linkedin": linkedin,
                "portfolio": portfolio,
            },
        )

        return jsonify(
            {
                "success": True,
                "resume_text": resume_text[:2000],  # preview
                "job_description": job_data.get("raw_description", "")[:2000],
                "matched_skills": analysis["matched_skills"],
                "missing_skills": analysis["missing_skills"],
                "match_score": analysis["match_score"],
                "job_title": job_data.get("title", "Position"),
                "company": job_data.get("company", "Company"),
                "analysis_summary": analysis["summary"],
                "session_id": analysis["session_id"],
            }
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Generates tailored resume PDF + cover letter PDF
    Only called when match_score >= 70
    """
    try:
        data = request.json
        session_id = data.get("session_id")
        personal_info = data.get("personal_info", {})
        job_data = data.get("job_data", {})
        analysis = data.get("analysis", {})

        # Generate tailored resume
        resume_pdf_path = generate_tailored_resume(
            session_id=session_id,
            personal_info=personal_info,
            analysis=analysis,
            output_folder=OUTPUT_FOLDER,
        )

        # Generate cover letter
        cover_letter_pdf_path = generate_cover_letter_pdf(
            session_id=session_id,
            personal_info=personal_info,
            job_data=job_data,
            analysis=analysis,
            output_folder=OUTPUT_FOLDER,
        )

        # Log to Google Sheets
        db.log_application(
            {
                "name": personal_info.get("name"),
                "email": personal_info.get("email"),
                "job_title": job_data.get("title", "N/A"),
                "company": job_data.get("company", "N/A"),
                "job_url": job_data.get("url", "N/A"),
                "match_score": analysis.get("match_score", 0),
                "status": "Generated",
                "session_id": session_id,
            }
        )

        return jsonify(
            {
                "success": True,
                "resume_pdf": f"/api/download/{session_id}_resume.pdf",
                "cover_letter_pdf": f"/api/download/{session_id}_cover_letter.pdf",
            }
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/send-confirmation", methods=["POST"])
def send_confirmation():
    """Send confirmation email after application"""
    try:
        data = request.json
        result = send_confirmation_email(
            to_email=data["email"],
            name=data["name"],
            job_title=data["job_title"],
            company=data["company"],
            job_url=data["job_url"],
        )
        # Update Google Sheets status
        db.update_status(data["session_id"], "Applied")
        return jsonify({"success": True, "message": "Confirmation email sent"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<filename>", methods=["GET"])
def download(filename):
    """Download generated PDF files"""
    path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404


@app.route("/api/applications", methods=["GET"])
def get_applications():
    """Get all applications from Google Sheets for dashboard"""
    try:
        apps = db.get_all_applications()
        return jsonify({"success": True, "applications": apps})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cover-letter-text", methods=["POST"])
def get_cover_letter_text():
    """Generate and return cover letter text for preview"""
    try:
        data = request.json
        cover_letter = agent.generate_cover_letter(
            personal_info=data["personal_info"],
            job_data=data["job_data"],
            analysis=data["analysis"],
        )
        return jsonify({"success": True, "cover_letter": cover_letter})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
