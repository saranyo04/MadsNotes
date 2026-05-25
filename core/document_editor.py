from __future__ import annotations

from core.models import Block, Document, InlineText, ensure_document
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


def _preserve_inline_details(
    parsed_inline: InlineText | None,
    base_inline: InlineText | None,
) -> InlineText | None:
    if parsed_inline is None or base_inline is None:
        return parsed_inline
    if parsed_inline.text != base_inline.text:
        return parsed_inline
    return InlineText(
        text=parsed_inline.text,
        tokens=list(base_inline.tokens),
        metadata=dict(base_inline.metadata),
    )


def _preserve_block_details(parsed_block: Block, base_block: Block) -> Block:
    if parsed_block.kind != base_block.kind:
        return parsed_block

    if parsed_block.kind == "list":
        merged_items: list[InlineText] = []
        for index, parsed_item in enumerate(parsed_block.items):
            base_item = base_block.items[index] if index < len(base_block.items) else None
            merged_items.append(_preserve_inline_details(parsed_item, base_item) or parsed_item)
        return Block(
            kind=parsed_block.kind,
            items=merged_items,
            metadata=dict(base_block.metadata) if merged_items else dict(parsed_block.metadata),
        )

    return Block(
        kind=parsed_block.kind,
        text=_preserve_inline_details(parsed_block.text, base_block.text),
        metadata=dict(base_block.metadata) if parsed_block.text and base_block.text and parsed_block.text.text == base_block.text.text else dict(parsed_block.metadata),
    )


def _preserve_document_details(parsed_document: Document, base_document: Document | None) -> Document:
    if base_document is None:
        return parsed_document

    merged_meta = dict(base_document.meta)
    merged_meta.update(parsed_document.meta)

    merged_blocks: list[Block] = []
    for index, parsed_block in enumerate(parsed_document.blocks):
        base_block = base_document.blocks[index] if index < len(base_document.blocks) else None
        if base_block is None:
            merged_blocks.append(parsed_block)
            continue
        merged_blocks.append(_preserve_block_details(parsed_block, base_block))

    return Document(meta=merged_meta, blocks=merged_blocks)


def editor_text_to_document(text: str, base_document: Document | None = None) -> Document:
    if not text or not text.strip():
        raise ValueError("No text to process")

    document = build_document(text, mode="strict")
    if not document.blocks:
        raise ValueError("No text to process")
    return _preserve_document_details(document, base_document)


class DocumentEditorCodec:
    def to_text(self, document: Document) -> str:
        return document_to_editor_text(document)

    def from_text(
        self,
        editor_text: str,
        mode: str = "strict",
        base_document: Document | None = None,
    ) -> Document:
        if mode != "strict":
            return _preserve_document_details(build_document(editor_text, mode=mode), base_document)
        return editor_text_to_document(editor_text, base_document=base_document)
