"""
Generates a realistic CIA CREST declassified PDF using ReportLab.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def create_crest_pdf(txt_path: str, pdf_path: str):
    text = Path(txt_path).read_text(encoding="utf-8")
    lines = [l.strip() for l in text.splitlines()]

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.red
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
    )

    story = []
    story.append(Paragraph("TOP SECRET // SANITIZED COPY // DECLASSIFIED UNDER CREST", header_style))
    story.append(Spacer(1, 10))

    for line in lines:
        if not line:
            story.append(Spacer(1, 6))
        elif any(line.startswith(h) for h in ["CENTRAL", "DIRECTORATE", "OFFICE", "MEMORANDUM", "SUBJECT:", "1.", "2.", "3.", "4."]):
            story.append(Paragraph(f"<b>{line}</b>", body_style))
        else:
            story.append(Paragraph(line, body_style))

    doc.build(story)
    print(f"Built official sample PDF: {pdf_path}")


if __name__ == "__main__":
    txt_file = Path(__file__).parent / "cia_crest_sanitized_report.txt"
    pdf_file = Path(__file__).parent / "cia_crest_sanitized_report.pdf"
    create_crest_pdf(str(txt_file), str(pdf_file))
