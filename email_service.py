"""
Email Service Module
Sends confirmation emails using SMTP (Gmail)
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")  # Gmail App Password


def send_confirmation_email(
    to_email: str,
    name: str,
    job_title: str,
    company: str,
    job_url: str,
    resume_path: str = None,
    cover_letter_path: str = None,
) -> bool:
    """
    Send application confirmation email to the candidate.
    
    Args:
        to_email: Recipient email
        name: Candidate name
        job_title: Job title applied for
        company: Company name
        job_url: Job posting URL
        resume_path: Optional path to tailored resume PDF
        cover_letter_path: Optional path to cover letter PDF
    
    Returns:
        True if sent successfully
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print(f"[Email] Mock: would send confirmation to {to_email}")
        print(f"[Email] Job: {job_title} at {company}")
        return True
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"✅ Application Submitted: {job_title} at {company}"
        msg["From"] = f"Job Application Agent <{EMAIL_SENDER}>"
        msg["To"] = to_email
        
        # Plain text version
        text_body = f"""
Hi {name},

Your application for {job_title} at {company} has been submitted!

Application Details:
- Position: {job_title}
- Company: {company}
- Job URL: {job_url}
- Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

Your tailored resume and cover letter have been generated and are attached to this email.

Good luck with your application! 🚀

Best,
Autonomous Job Application Agent
        """
        
        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f6fa; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 32px; text-align: center; }}
  .header h1 {{ color: white; margin: 0; font-size: 22px; }}
  .header p {{ color: #e94560; margin: 8px 0 0; font-size: 14px; }}
  .checkmark {{ font-size: 48px; display: block; margin-bottom: 12px; }}
  .body {{ padding: 32px; }}
  .greeting {{ font-size: 18px; color: #1a1a2e; font-weight: 600; margin-bottom: 16px; }}
  .details-card {{ background: #f8f9fa; border-left: 4px solid #e94560; border-radius: 8px; padding: 20px; margin: 20px 0; }}
  .detail-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #e9ecef; }}
  .detail-row:last-child {{ border-bottom: none; }}
  .detail-label {{ color: #6c757d; font-size: 13px; font-weight: 500; }}
  .detail-value {{ color: #1a1a2e; font-size: 13px; font-weight: 600; }}
  .tip-box {{ background: linear-gradient(135deg, #e3f2fd, #f3e5f5); border-radius: 8px; padding: 16px; margin: 20px 0; }}
  .tip-box h3 {{ color: #1a1a2e; font-size: 14px; margin: 0 0 8px; }}
  .tip-box ul {{ color: #495057; font-size: 13px; margin: 0; padding-left: 20px; line-height: 1.8; }}
  .footer {{ background: #1a1a2e; padding: 20px 32px; text-align: center; }}
  .footer p {{ color: #6c757d; font-size: 12px; margin: 4px 0; }}
  .job-link {{ color: #e94560; text-decoration: none; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <span class="checkmark">✅</span>
    <h1>Application Submitted!</h1>
    <p>Your tailored application is on its way</p>
  </div>
  
  <div class="body">
    <div class="greeting">Hi {name},</div>
    
    <p style="color:#495057; font-size:15px; line-height:1.7;">
      Great news! Your application for <strong>{job_title}</strong> at <strong>{company}</strong> 
      has been successfully submitted. Your tailored resume and cover letter are attached below.
    </p>
    
    <div class="details-card">
      <div class="detail-row">
        <span class="detail-label">Position</span>
        <span class="detail-value">{job_title}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Company</span>
        <span class="detail-value">{company}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Application Date</span>
        <span class="detail-value">{datetime.now().strftime('%B %d, %Y')}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Job Link</span>
        <span class="detail-value"><a href="{job_url}" class="job-link">View Posting →</a></span>
      </div>
    </div>
    
    <div class="tip-box">
      <h3>🎯 Next Steps for Success</h3>
      <ul>
        <li>Follow up by email in 5-7 business days if no response</li>
        <li>Connect with employees at {company} on LinkedIn</li>
        <li>Research the company's latest news before your interview</li>
        <li>Prepare STAR method stories for your matched skills</li>
      </ul>
    </div>
    
    <p style="color:#495057; font-size:14px;">Good luck! 🚀</p>
  </div>
  
  <div class="footer">
    <p>Sent by Autonomous Job Application Agent</p>
    <p>Powered by AI | Your career, accelerated</p>
  </div>
</div>
</body>
</html>
"""
        
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Attach PDFs if provided
        for pdf_path, pdf_name in [
            (resume_path, f"{name.replace(' ', '_')}_Tailored_Resume.pdf"),
            (cover_letter_path, f"{name.replace(' ', '_')}_Cover_Letter.pdf"),
        ]:
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={pdf_name}")
                msg.attach(part)
        
        # Send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        
        print(f"[Email] Sent confirmation to {to_email}")
        return True
        
    except Exception as e:
        print(f"[Email] Failed to send: {e}")
        return False


def send_skill_gap_email(
    to_email: str,
    name: str,
    job_title: str,
    company: str,
    missing_skills: list,
    match_score: int,
) -> bool:
    """Send skill gap notification email."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print(f"[Email] Mock: skill gap email to {to_email}")
        return True
    
    skill_list_html = "".join([f"<li>{skill}</li>" for skill in missing_skills[:10]])
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family: Arial, sans-serif; background: #f5f6fa; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }}
  .header {{ background: #1a1a2e; padding: 24px; text-align: center; color: white; }}
  .body {{ padding: 24px; }}
  .score {{ font-size: 48px; font-weight: bold; color: #e94560; text-align: center; }}
  .skills-list {{ background: #fff3cd; border-radius: 8px; padding: 16px; margin: 16px 0; }}
  .skills-list ul {{ margin: 0; padding-left: 20px; line-height: 2; }}
</style>
</head>
<body>
<div class="container">
  <div class="header"><h2>Resume Analysis Results</h2></div>
  <div class="body">
    <p>Hi {name},</p>
    <p>Your resume was analyzed for <strong>{job_title}</strong> at <strong>{company}</strong>.</p>
    
    <div class="score">{match_score}%</div>
    <p style="text-align:center;color:#6c757d;">Match Score</p>
    
    <p>To improve your chances, consider developing these skills:</p>
    <div class="skills-list">
      <ul>{skill_list_html}</ul>
    </div>
    
    <p>Resources to upskill: Coursera, Udemy, freeCodeCamp, YouTube, and official documentation.</p>
    <p>Once you've built these skills, run the analysis again for better results!</p>
  </div>
</div>
</body>
</html>
"""
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📊 Resume Analysis: {match_score}% match for {job_title}"
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[Email] Skill gap email failed: {e}")
        return False
