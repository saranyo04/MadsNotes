from datetime import datetime, timezone

from core.document_editor import document_to_editor_text
from core.text_structurer import (
    DEFAULT_STRUCTURING_MODE,
    build_document,
    normalize_structuring_mode,
)
from utils.file_manager import create_job, write_job_json, write_job_text
from utils.html_generator import generate_html


def _validated_document(document: dict) -> dict:
    if not document.get("blocks"):
        raise ValueError("No text to process")
    return document


def process_text(
    text: str,
    mode: str = DEFAULT_STRUCTURING_MODE,
) -> dict:
    if not text or not text.strip():
        raise ValueError("No text to process")

    normalized_mode = normalize_structuring_mode(mode)
    document = build_document(text, mode=normalized_mode)
    return _validated_document(document)


def read_pdf_text(pdf_path: str) -> str:
    from core.pdf_handler import extract_text_from_pdf

    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        raise ValueError("No selectable text found in PDF")

    return text


def process_pdf(
    pdf_path: str,
    mode: str = DEFAULT_STRUCTURING_MODE,
) -> dict:
    return process_text(read_pdf_text(pdf_path), mode=mode)


def _build_job_meta(
    document: dict,
    *,
    job_name: str,
    source_kind: str,
    source_path: str | None,
    structuring_mode: str | None,
    used_editor: bool,
) -> dict:
    blocks = document.get("blocks", [])

    return {
        "job": job_name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_kind": source_kind,
        "source_path": source_path,
        "structuring_mode": structuring_mode,
        "used_editor": used_editor,
        "block_count": len(blocks),
        "block_types": [block.get("type", "paragraph") for block in blocks],
    }


def generate_html_output(
    document: dict,
    *,
    editor_text: str | None = None,
    source_text: str | None = None,
    source_kind: str = "text",
    source_path: str | None = None,
    structuring_mode: str | None = None,
    used_editor: bool = False,
) -> str:
    document = _validated_document(document)

    job_path = create_job()
    output_path = job_path / "output" / "study.html"

    structured_text = (
        editor_text
        if editor_text and editor_text.strip()
        else document_to_editor_text(document)
    )

    if source_text and source_text.strip():
        write_job_text(job_path, "input/source.txt", source_text)

    if structured_text:
        write_job_text(job_path, "input/structured.txt", structured_text)

    generate_html(document, output_path)

    meta = _build_job_meta(
        document,
        job_name=job_path.name,
        source_kind=source_kind,
        source_path=source_path,
        structuring_mode=structuring_mode,
        used_editor=used_editor,
    )
    write_job_json(job_path, "meta.json", meta)

    return str(output_path)


def render_document(
    document: dict,
    *,
    editor_text: str | None = None,
    source_text: str | None = None,
    source_kind: str = "text",
    source_path: str | None = None,
    structuring_mode: str | None = None,
    used_editor: bool = False,
) -> str:
    return generate_html_output(
        document,
        editor_text=editor_text,
        source_text=source_text,
        source_kind=source_kind,
        source_path=source_path,
        structuring_mode=structuring_mode,
        used_editor=used_editor,
    )
