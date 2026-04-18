from core.text_structurer import build_document


def document_to_editor_text(document: dict) -> str:
    blocks = document.get("blocks", [])
    editor_blocks: list[str] = []

    for block in blocks:
        block_type = block.get("type")

        if block_type in {"heading", "paragraph", "label"}:
            text = block.get("text", "").strip()
            if text:
                editor_blocks.append(text)

        elif block_type == "list":
            items = [
                f"- {item.strip()}"
                for item in block.get("items", [])
                if item and item.strip()
            ]

            if items:
                editor_blocks.append("\n".join(items))

    if not editor_blocks:
        editor_blocks = [
            paragraph.strip()
            for paragraph in document.get("paragraphs", [])
            if paragraph and paragraph.strip()
        ]

    return "\n\n".join(editor_blocks)


def editor_text_to_document(text: str) -> dict:
    if not text or not text.strip():
        raise ValueError("No text to process")

    # The editor is a manual structure-correction surface, so we always
    # rebuild it with the strict parser regardless of the input mode.
    document = build_document(text, mode="strict")

    if not document.get("blocks"):
        raise ValueError("No text to process")

    return document
