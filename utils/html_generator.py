from html import escape
from pathlib import Path


def generate_html(text, output_path):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    paragraphs = "\n".join(f"<p>{escape(line)}</p>" for line in lines)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Chinese Study</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", sans-serif;
            padding: 40px;
            line-height: 1.8;
            font-size: 18px;
        }}
        p {{
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div>
        {paragraphs}
    </div>
</body>
</html>
"""

    Path(output_path).write_text(html_content, encoding="utf-8")