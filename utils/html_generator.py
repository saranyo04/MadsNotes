from html import escape
from pathlib import Path


def generate_html(document: dict, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    meta = document.get("meta", {})
    paragraphs = document.get("paragraphs", [])

    body = "\n".join(f"<p>{escape(p)}</p>" for p in paragraphs if p.strip())
    if not body:
        body = "<p></p>"

    font_family = meta.get("font_family", "Microsoft YaHei, PingFang SC, sans-serif")

    html_content = f"""<!DOCTYPE html>
<html lang="{meta.get("lang", "zh-CN")}">
<head>
    <meta charset="UTF-8">
    <title>{escape(meta.get("title", "Chinese Study"))}</title>
    <style>
        body {{
            font-family: {font_family};
            padding: {meta.get("padding", "20px")};
            line-height: {meta.get("line_height", "1.9")};
            font-size: {meta.get("font_size", "18px")};
            max-width: {meta.get("max_width", "100%")};
            margin: {meta.get("margin", "0")};
            background: {meta.get("background", "#fff")};
            color: {meta.get("color", "#111")};
        }}
        p {{
            margin-bottom: {meta.get("paragraph_margin_bottom", "1em")};
            text-indent: {meta.get("paragraph_text_indent", "2em")};
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