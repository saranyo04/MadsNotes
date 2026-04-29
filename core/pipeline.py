from __future__ import annotations

"""Legacy compatibility wrapper.

The real runtime workflow lives in ``application.workflow.WorkflowService``.
This module stays only to preserve older imports while delegating into the
application layer.
"""

from importlib import import_module

from core.models import Document
from core.text_structurer import DEFAULT_STRUCTURING_MODE


def _workflow_service():
    workflow_module = import_module("application.workflow")
    return workflow_module.build_default_workflow()


def process_text(
    text: str,
    mode: str = DEFAULT_STRUCTURING_MODE,
) -> Document:
    workflow = _workflow_service()
    return workflow.build_document(text=text, mode=mode)


def read_pdf_text(pdf_path: str) -> str:
    workflow = _workflow_service()
    return workflow.load_pdf_source(pdf_path).text


def process_pdf(
    pdf_path: str,
    mode: str = DEFAULT_STRUCTURING_MODE,
) -> Document:
    workflow = _workflow_service()
    source = workflow.load_pdf_source(pdf_path)
    return workflow.build_document(
        text=source.text,
        mode=mode,
        source_kind=source.kind,
        source_path=source.path,
        metadata=source.metadata,
    )


def generate_html_output(
    document: Document,
    *,
    editor_text: str | None = None,
    source_text: str | None = None,
    source_kind: str = "text",
    source_path: str | None = None,
    structuring_mode: str | None = None,
    used_editor: bool = False,
) -> str:
    workflow = _workflow_service()
    result = workflow.render_document(
        document=document,
        editor_text=editor_text,
        source_text=source_text,
        source_kind=source_kind,
        source_path=source_path,
        structuring_mode=structuring_mode,
        used_editor=used_editor,
        persist=True,
    )
    if result.stored_output is None:
        raise RuntimeError("Render did not produce a stored output")
    return str(result.stored_output.output_path)


def render_document(
    document: Document,
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
