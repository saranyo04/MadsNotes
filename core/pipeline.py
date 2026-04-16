from core.pdf_handler import extract_text_from_pdf
from core.text_structurer import build_document
from utils.html_generator import generate_html
from utils.file_manager import create_job


def process_text(text):
    job_path = create_job()
    output_path = job_path / "output" / "study.html"

    document = build_document(text)

    if not document.get("paragraphs"):
        raise ValueError("No text to process")

    generate_html(document, output_path)
    return str(output_path)


def process_pdf(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        raise ValueError("No selectable text found in PDF")

    return process_text(text)