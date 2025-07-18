import fitz
import docx2txt
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        doc = fitz.open(pdf_path)
        return "".join([page.get_text() for page in doc])
    except Exception:
        return ""

def extract_text_from_docx(docx_path: str) -> str:
    try:
        return docx2txt.process(docx_path) or ""
    except Exception:
        return ""

def extract_text_from_txt(txt_path: str) -> str:
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception:
        return ""

def extract_text_from_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    if ext == ".txt":
        return extract_text_from_txt(file_path)
    return ""
