from __future__ import annotations

from html import escape

from core.models import Document, ensure_document

from application.results import RenderArtifact
from infrastructure.config import APP_NAME


def _is_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _html_text(text: str) -> str:
    return escape(text).replace("\n", "<br>")


class HtmlRenderer:
    def render(self, document: Document) -> RenderArtifact:
        document = ensure_document(document)
        meta = document.meta
        font_family = meta.get("font_family", "Microsoft YaHei, PingFang SC, sans-serif")

        body_parts: list[str] = []
        for block in document.blocks:
            if block.kind == "heading" and block.text is not None:
                body_parts.append(f"<h2>{_html_text(block.text.text)}</h2>")
            elif block.kind == "label" and block.text is not None:
                body_parts.append(f"<p class='label'>{_html_text(block.text.text)}</p>")
            elif block.kind == "paragraph" and block.text is not None:
                text = block.text.text
                cls = "cjk" if _is_cjk(text) else "latin"
                body_parts.append(f"<p class='{cls}'>{_html_text(text)}</p>")
            elif block.kind == "list":
                li_html = "".join(
                    f"<li>{_html_text(item.text)}</li>"
                    for item in block.items
                    if item.text and item.text.strip()
                )
                body_parts.append(f"<ul>{li_html}</ul>")

        body = "\n".join(body_parts) if body_parts else "<p></p>"
        html_content = f"""<!DOCTYPE html>
<html lang="{meta.get("lang", "zh-CN")}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(meta.get("title", APP_NAME))}</title>
    <style>
        body {{
            font-family: {font_family};
            padding: {meta.get("padding", "20px")};
            line-height: {meta.get("line_height", "1.9")};
            font-size: {meta.get("font_size", "18px")};
            max-width: 100%;
            margin: 0;
            background: {meta.get("background", "#fff")};
            color: {meta.get("color", "#111")};
        }}

        h2 {{
            margin: 1.25em 0 0.6em 0;
            font-size: 1.2em;
        }}

        p {{
            margin: 0 0 {meta.get("paragraph_margin_bottom", "1em")} 0;
        }}

        p.cjk {{
            text-indent: {meta.get("paragraph_text_indent", "2em")};
        }}

        p.latin {{
            text-indent: 0;
        }}

        p.label {{
            font-weight: 600;
            margin-top: 1em;
            text-indent: 0;
        }}

        ul {{
            margin: 0 0 1em 1.5em;
            padding-left: 1.2em;
        }}

        li {{
            margin-bottom: 0.45em;
        }}
    </style>
</head>
<body>
    {body}
</body>
</html>
"""
        return RenderArtifact(document=document, html=html_content, metadata={"body": body})
