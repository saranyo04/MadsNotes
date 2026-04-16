import fitz


def extract_text_from_pdf(pdf_path):
    text_parts = []

    with fitz.open(pdf_path) as doc:
        for page in doc:
            text_parts.append(page.get_text("text"))

    return "\n".join(text_parts)