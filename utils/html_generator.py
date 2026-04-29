from __future__ import annotations

"""Legacy compatibility wrapper around infrastructure.html_renderer.HtmlRenderer."""

from pathlib import Path

from core.models import ensure_document
from infrastructure.html_renderer import HtmlRenderer

_HTML_RENDERER = HtmlRenderer()


def generate_html(document, output_path):
    artifact = _HTML_RENDERER.render(ensure_document(document))
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(artifact.html, encoding="utf-8")
    return output_path
