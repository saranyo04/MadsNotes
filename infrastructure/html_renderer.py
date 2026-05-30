from __future__ import annotations

from html import escape

from core.models import Document, InlineText, ensure_document
from core.workflow_models import RenderArtifact
from infrastructure.config import APP_NAME

_DEFAULT_FONT_FAMILY = "Microsoft YaHei, PingFang SC, sans-serif"
_SAFE_CSS_VALUE_CHARS = frozenset(" #%,.-_")


def _is_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _html_text(text: str) -> str:
    return escape(text).replace("\n", "<br>")


def _inline_html(inline_text: InlineText | None) -> str:
    if inline_text is None:
        return ""
    return _html_text(inline_text.text)


def _css_value(value: object, default: str) -> str:
    text = str(value).strip()
    if text and all(char.isalnum() or char in _SAFE_CSS_VALUE_CHARS for char in text):
        return text
    return default


class HtmlRenderer:
    def render(self, document: Document) -> RenderArtifact:
        document = ensure_document(document)
        meta = document.meta
        font_family = _css_value(
            meta.get("font_family", _DEFAULT_FONT_FAMILY),
            _DEFAULT_FONT_FAMILY,
        )
        padding = _css_value(meta.get("padding", "20px"), "20px")
        line_height = _css_value(meta.get("line_height", "1.9"), "1.9")
        font_size = _css_value(meta.get("font_size", "18px"), "18px")
        background = _css_value(meta.get("background", "#fff"), "#fff")
        color = _css_value(meta.get("color", "#111"), "#111")
        paragraph_margin_bottom = _css_value(
            meta.get("paragraph_margin_bottom", "1em"),
            "1em",
        )
        paragraph_text_indent = _css_value(
            meta.get("paragraph_text_indent", "2em"),
            "2em",
        )

        body_parts: list[str] = []
        has_tokens = False
        for block in document.blocks:
            if block.kind == "heading" and block.text is not None:
                has_tokens = has_tokens or bool(block.text.tokens)
                body_parts.append(f"<h2>{_inline_html(block.text)}</h2>")
            elif block.kind == "label" and block.text is not None:
                has_tokens = has_tokens or bool(block.text.tokens)
                body_parts.append(f"<p class='label'>{_inline_html(block.text)}</p>")
            elif block.kind == "paragraph" and block.text is not None:
                text = block.text.text
                cls = "cjk" if _is_cjk(text) else "latin"
                has_tokens = has_tokens or bool(block.text.tokens)
                body_parts.append(f"<p class='{cls}'>{_inline_html(block.text)}</p>")
            elif block.kind == "list":
                has_tokens = has_tokens or any(item.tokens for item in block.items)
                li_html = "".join(
                    f"<li>{_inline_html(item)}</li>"
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
            padding: {padding};
            line-height: {line_height};
            font-size: {font_size};
            max-width: 100%;
            margin: 0;
            background: {background};
            color: {color};
        }}

        h2 {{
            margin: 1.25em 0 0.6em 0;
            font-size: 1.2em;
        }}

        p {{
            margin: 0 0 {paragraph_margin_bottom} 0;
        }}

        p.cjk {{
            text-indent: {paragraph_text_indent};
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
        return RenderArtifact(
            document=document,
            html=html_content,
            metadata={"has_tokens": has_tokens},
        )
