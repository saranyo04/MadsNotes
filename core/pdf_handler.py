from __future__ import annotations

"""Legacy compatibility wrapper around infrastructure.pdf_extractor."""

from infrastructure.pdf_extractor import PdfTextExtractor

_PDF_EXTRACTOR = PdfTextExtractor()


def extract_text_from_pdf(pdf_path: str) -> str:
    return _PDF_EXTRACTOR.extract_text(pdf_path)
