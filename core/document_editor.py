from __future__ import annotations

from core.models import Document, ensure_document
from core.text_structurer import build_document


def document_to_editor_text(document: Document) -> str:
    document = ensure_document(document)
    editor_blocks: list[str] = []

    for block in document.blocks:
        if block.kind in {"heading", "paragraph", "label"} and block.text is not None:
            text = block.text.text.strip()
            if text:
                editor_blocks.append(text)
        elif block.kind == "list":
            items = [
                f"- {item.text.strip()}"
                for item in block.items
                if item.text and item.text.strip()
            ]
            if items:
                editor_blocks.append("\n".join(items))

    if not editor_blocks:
        editor_blocks = [
            paragraph.strip()
            for paragraph in document.paragraphs
            if paragraph and paragraph.strip()
        ]

    return "\n\n".join(editor_blocks)


def editor_text_to_document(text: str) -> Document:
    if not text or not text.strip():
        raise ValueError("No text to process")

    document = build_document(text, mode="strict")
    if not document.blocks:
        raise ValueError("No text to process")
    return document


class DocumentEditorCodec:
    def to_text(self, document: Document) -> str:
        return document_to_editor_text(document)

    def from_text(self, editor_text: str, mode: str = "strict") -> Document:
        if mode != "strict":
            return build_document(editor_text, mode=mode)
        return editor_text_to_document(editor_text)
