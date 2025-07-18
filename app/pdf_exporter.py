from fpdf import FPDF
from typing import List, Dict, Any
import os
import sys

class ResumeReportPDF(FPDF):
    def header(self):
        try:
            self.set_font("Arial", 'B', 15)
        except:
            self.set_font("Helvetica", 'B', 15)
        self.cell(0, 10, "📄 AI Resume Screening Report", 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        try:
            self.set_font("Arial", 'I', 8)
        except:
            self.set_font("Helvetica", 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')
    def chapter_title(self, title):
        try:
            self.set_font("Arial", 'B', 12)
        except:
            self.set_font("Helvetica", 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)
    def chapter_body(self, body):
        try:
            self.set_font("Arial", '', 10)
        except:
            self.set_font("Helvetica", '', 10)
        self.multi_cell(0, 5, body)
        self.ln(5)

def export_results_to_pdf(
    ranked_resumes: List[Dict[str, Any]],
    job_description_data: Dict[str, Any],
    output_path: str = "Resume_Match_Report.pdf",
    job_title: str = ""
) -> str:
    print(f"[DEBUG] Exporting PDF to: {output_path}")
    pdf = ResumeReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    try:
        pdf.set_font("Arial", 'B', 14)
    except:
        pdf.set_font("Helvetica", 'B', 14)

    pdf.cell(0, 10, f"Job Role: {job_title or 'N/A'}", 0, 1, 'C')
    pdf.ln(5)
    pdf.chapter_title("Job Description Summary:")
    jd_summary_text = (
        f"Required Skills: {', '.join(job_description_data.get('required_skills', ['N/A']))}\n"
        f"Experience Required: {job_description_data.get('experience_requirements', 'N/A')} years\n"
        f"Education Requirements: {', '.join(job_description_data.get('education_requirements', ['N/A']))}\n"
    )
    pdf.chapter_body(jd_summary_text)
    pdf.ln(5)
    pdf.chapter_title("Ranked Candidates:")
    try:
        pdf.set_font("Arial", 'B', 10)
    except:
        pdf.set_font("Helvetica", 'B', 10)

    pdf.cell(80, 7, "Candidate Resume", 1, 0, 'C')
    pdf.cell(30, 7, "Score (%)", 1, 0, 'C')
    pdf.cell(80, 7, "Key Skills Found", 1, 1, 'C')
    try:
        pdf.set_font("Arial", '', 9)
    except:
        pdf.set_font("Helvetica", '', 9)

    if not ranked_resumes:
        pdf.cell(0, 10, "No candidates matched or parsed.", 1, 1, 'C')
    else:
        for res in ranked_resumes:
            filename = res.get("filename", "N/A")
            score = res.get("score", "N/A")
            parsed_data = res.get("parsed_data", {})
            skills_list = parsed_data.get("skills", [])
            skills = ", ".join(skills_list)[:75] + ("..." if len(", ".join(skills_list)) > 75 else "")
            pdf.cell(80, 7, filename, 1, 0)
            pdf.cell(30, 7, str(score), 1, 0, 'C')
            pdf.multi_cell(80, 7, skills, 1, 'L', False)
            if pdf.get_y() + 10 > pdf.h - pdf.b_margin:
                pdf.add_page()
                pdf.chapter_title("Ranked Candidates (Cont.):")
                try:
                    pdf.set_font("Arial", 'B', 10)
                except:
                    pdf.set_font("Helvetica", 'B', 10)
                pdf.cell(80, 7, "Candidate Resume", 1, 0, 'C')
                pdf.cell(30, 7, "Score (%)", 1, 0, 'C')
                pdf.cell(80, 7, "Key Skills Found", 1, 1, 'C')
    try:
        pdf.output(output_path)
        if os.path.exists(output_path):
            print(f"[DEBUG] PDF successfully written to {output_path}")
            return output_path
        else:
            print(f"[ERROR] PDF file was not created at: {output_path}")
            return ""
    except Exception as e:
        print(f"[PDF ERROR] Exception during PDF creation: {e}", file=sys.stderr)
        return ""
