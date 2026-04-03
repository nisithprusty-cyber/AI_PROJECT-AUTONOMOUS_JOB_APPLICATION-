"""
PDF Generator Module
Uses ReportLab to generate professional tailored resumes and cover letters
"""
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime


# ---- Color Palette ----
PRIMARY = colors.HexColor("#1a1a2e")       # Deep navy
ACCENT = colors.HexColor("#e94560")        # Vivid red-pink
SECONDARY = colors.HexColor("#16213e")     # Dark blue
LIGHT_BG = colors.HexColor("#f8f9fa")
TEXT_COLOR = colors.HexColor("#2d2d2d")
SUBTLE = colors.HexColor("#6c757d")
WHITE = colors.white


def generate_tailored_resume(
    session_id: str,
    personal_info: dict,
    analysis: dict,
    output_folder: str = "outputs",
) -> str:
    """Generate a professionally formatted tailored resume PDF."""
    
    filename = f"{session_id}_resume.pdf"
    filepath = os.path.join(output_folder, filename)
    os.makedirs(output_folder, exist_ok=True)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=0.6*inch,
        rightMargin=0.6*inch,
        topMargin=0.6*inch,
        bottomMargin=0.6*inch,
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # ---- Header Style ----
    name_style = ParagraphStyle(
        "NameStyle",
        fontSize=24,
        fontName="Helvetica-Bold",
        textColor=PRIMARY,
        spaceAfter=2,
        alignment=TA_CENTER,
    )
    
    contact_style = ParagraphStyle(
        "ContactStyle",
        fontSize=9,
        fontName="Helvetica",
        textColor=SUBTLE,
        spaceBefore=0,
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    
    section_header_style = ParagraphStyle(
        "SectionHeader",
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=ACCENT,
        spaceBefore=10,
        spaceAfter=3,
    )
    
    body_style = ParagraphStyle(
        "BodyStyle",
        fontSize=9.5,
        fontName="Helvetica",
        textColor=TEXT_COLOR,
        spaceAfter=4,
        leading=14,
        alignment=TA_JUSTIFY,
    )
    
    bullet_style = ParagraphStyle(
        "BulletStyle",
        fontSize=9.5,
        fontName="Helvetica",
        textColor=TEXT_COLOR,
        spaceAfter=3,
        leading=14,
        leftIndent=12,
        bulletIndent=0,
    )
    
    # ---- Name & Contact ----
    name = personal_info.get("name", "Your Name")
    email = personal_info.get("email", "")
    phone = personal_info.get("phone", "")
    address = personal_info.get("address", "")
    linkedin = personal_info.get("linkedin", "")
    portfolio = personal_info.get("portfolio", "")
    
    story.append(Paragraph(name, name_style))
    
    contact_parts = [x for x in [phone, email, address, linkedin, portfolio] if x]
    story.append(Paragraph(" | ".join(contact_parts), contact_style))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=8))
    
    # ---- Professional Summary ----
    summary = analysis.get("summary", "")
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_header_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dee2e6"), spaceAfter=5))
        story.append(Paragraph(summary, body_style))
    
    # ---- Matched Skills ----
    matched_skills = analysis.get("matched_skills", [])
    if matched_skills:
        story.append(Paragraph("KEY SKILLS", section_header_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dee2e6"), spaceAfter=5))
        
        # Layout skills in a 3-column table
        skills_per_row = 3
        skill_rows = []
        for i in range(0, len(matched_skills), skills_per_row):
            row = matched_skills[i:i+skills_per_row]
            while len(row) < skills_per_row:
                row.append("")
            cell_style = ParagraphStyle("skill_cell", fontSize=9, fontName="Helvetica",
                                       textColor=TEXT_COLOR)
            skill_rows.append([Paragraph(f"✦ {s}", cell_style) for s in row])
        
        if skill_rows:
            skill_table = Table(skill_rows, colWidths=["33%", "33%", "34%"])
            skill_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(skill_table)
            story.append(Spacer(1, 6))
    
    # ---- Experience Placeholder ----
    story.append(Paragraph("WORK EXPERIENCE", section_header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dee2e6"), spaceAfter=5))
    story.append(Paragraph(
        "<i>Your work experience has been tailored to highlight skills matching this role. "
        "Please review and add specific achievements, dates, and company names from your master resume.</i>",
        ParagraphStyle("italic_note", fontSize=9, fontName="Helvetica-Oblique", textColor=SUBTLE)
    ))
    story.append(Spacer(1, 4))
    
    # Show matched skills as tailored bullets
    for skill in matched_skills[:6]:
        story.append(Paragraph(
            f"• Demonstrated expertise in <b>{skill}</b> — applied in production environments to deliver measurable results.",
            bullet_style
        ))
    
    # ---- Education ----
    story.append(Paragraph("EDUCATION", section_header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dee2e6"), spaceAfter=5))
    story.append(Paragraph(
        "<i>Add your education details here (Degree, Institution, Year).</i>",
        ParagraphStyle("italic_note", fontSize=9, fontName="Helvetica-Oblique", textColor=SUBTLE)
    ))
    
    # ---- Match Score Badge ----
    story.append(Spacer(1, 12))
    match_score = analysis.get("match_score", 0)
    
    score_data = [[
        Paragraph(
            f"<b>ATS Match Score: {match_score}%</b>  |  Generated: {datetime.now().strftime('%B %d, %Y')}  |  Tailored Resume",
            ParagraphStyle("footer", fontSize=8, fontName="Helvetica", textColor=WHITE, alignment=TA_CENTER)
        )
    ]]
    score_table = Table(score_data, colWidths=["100%"])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(score_table)
    
    doc.build(story)
    print(f"[PDF] Resume generated: {filepath}")
    return filepath


def generate_cover_letter_pdf(
    session_id: str,
    personal_info: dict,
    job_data: dict,
    analysis: dict,
    output_folder: str = "outputs",
    cover_letter_text: str = "",
) -> str:
    """Generate a professionally formatted cover letter PDF."""
    
    filename = f"{session_id}_cover_letter.pdf"
    filepath = os.path.join(output_folder, filename)
    os.makedirs(output_folder, exist_ok=True)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=1.0*inch,
        rightMargin=1.0*inch,
        topMargin=1.0*inch,
        bottomMargin=1.0*inch,
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    header_style = ParagraphStyle(
        "CLHeader",
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=PRIMARY,
        spaceAfter=2,
    )
    
    contact_style = ParagraphStyle(
        "CLContact",
        fontSize=9,
        fontName="Helvetica",
        textColor=SUBTLE,
        spaceAfter=3,
    )
    
    body_style = ParagraphStyle(
        "CLBody",
        fontSize=10.5,
        fontName="Helvetica",
        textColor=TEXT_COLOR,
        spaceAfter=10,
        leading=16,
        alignment=TA_JUSTIFY,
    )
    
    date_style = ParagraphStyle(
        "DateStyle",
        fontSize=10,
        fontName="Helvetica",
        textColor=SUBTLE,
        spaceAfter=16,
    )
    
    # Header
    name = personal_info.get("name", "Your Name")
    email = personal_info.get("email", "")
    phone = personal_info.get("phone", "")
    address = personal_info.get("address", "")
    
    story.append(Paragraph(name, header_style))
    contact_parts = [x for x in [phone, email, address] if x]
    story.append(Paragraph(" | ".join(contact_parts), contact_style))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=16))
    
    # Date
    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), date_style))
    
    # Addressee
    company = job_data.get("company", "Hiring Team")
    job_title = job_data.get("title", "Position")
    
    story.append(Paragraph(f"Hiring Manager", body_style))
    story.append(Paragraph(f"{company}", body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Re: Application for {job_title}", 
        ParagraphStyle("re_line", fontSize=10.5, fontName="Helvetica-Bold", textColor=PRIMARY, spaceAfter=10)
    ))
    
    # Cover letter body
    if cover_letter_text:
        paragraphs = [p.strip() for p in cover_letter_text.split("\n") if p.strip()]
        for para in paragraphs:
            story.append(Paragraph(para, body_style))
    else:
        # Default template
        matched = ", ".join(analysis.get("matched_skills", ["relevant skills"])[:4])
        story.append(Paragraph(
            f"With a strong foundation in {matched}, I am excited to bring my expertise to {company} as a {job_title}. "
            f"My background aligns well with your requirements, and I am confident in my ability to make an immediate impact.",
            body_style
        ))
        story.append(Paragraph(
            "Throughout my career, I have consistently delivered results by combining technical proficiency with a collaborative mindset. "
            f"I am particularly drawn to {company}'s mission and believe my skills would be a strong asset to your team.",
            body_style
        ))
        story.append(Paragraph(
            "I would welcome the opportunity to discuss how my experience aligns with your needs. "
            "Thank you for your time and consideration.",
            body_style
        ))
    
    # Closing
    story.append(Spacer(1, 16))
    story.append(Paragraph("Sincerely,", body_style))
    story.append(Paragraph(name, ParagraphStyle("sig", fontSize=11, fontName="Helvetica-Bold", textColor=PRIMARY)))
    
    doc.build(story)
    print(f"[PDF] Cover letter generated: {filepath}")
    return filepath


if __name__ == "__main__":
    # Quick test
    generate_tailored_resume(
        session_id="test123",
        personal_info={"name": "John Doe", "email": "john@example.com", "phone": "+1-555-0100"},
        analysis={
            "matched_skills": ["Python", "Django", "PostgreSQL", "React", "Docker"],
            "missing_skills": ["Kubernetes", "AWS"],
            "match_score": 78,
            "summary": "Strong Python developer with solid web development background.",
        },
        output_folder="test_outputs",
    )
    print("Test PDF generated in test_outputs/")
