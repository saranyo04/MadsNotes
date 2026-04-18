from html import escape
from pathlib import Path


def _is_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _html_text(text: str) -> str:
    return escape(text).replace("\n", "<br>")


def generate_html(document: dict, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    meta = document.get("meta", {})
    blocks = document.get("blocks")

    if not blocks:
        paragraphs = document.get("paragraphs", [])
        blocks = [{"type": "paragraph", "text": p} for p in paragraphs]

    font_family = meta.get("font_family", "Microsoft YaHei, PingFang SC, sans-serif")

    body_parts = []

    for block in blocks:
        btype = block.get("type")

        if btype == "heading":
            text = _html_text(block.get("text", ""))
            body_parts.append(f"<h2>{text}</h2>")

        elif btype == "label":
            text = _html_text(block.get("text", ""))
            body_parts.append(f"<p class='label'>{text}</p>")

        elif btype == "paragraph":
            text = block.get("text", "")
            cls = "cjk" if _is_cjk(text) else "latin"
            body_parts.append(f"<p class='{cls}'>{_html_text(text)}</p>")

        elif btype == "list":
            items = block.get("items", [])
            li_html = "".join(
                f"<li>{_html_text(item)}</li>"
                for item in items
                if item and item.strip()
            )
            body_parts.append(f"<ul>{li_html}</ul>")

    body = "\n".join(body_parts) if body_parts else "<p></p>"

    html_content = f"""<!DOCTYPE html>
<html lang="{meta.get("lang", "zh-CN")}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(meta.get("title", "Chinese Study"))}</title>
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

    output_path.write_text(html_content, encoding="utf-8")
    return output_path