from __future__ import annotations

from application.results import SourceRequest, SourceText


class PdfTextExtractor:
    def __init__(self) -> None:
        self._fitz = None

    def _fitz_module(self):
        if self._fitz is None:
            import fitz

            self._fitz = fitz
        return self._fitz

    def extract_text(self, pdf_path: str) -> str:
        fitz = self._fitz_module()
        text_parts: list[str] = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text_parts.append(page.get_text("text"))
        return "\n".join(text_parts)

    def extract(self, source_request: SourceRequest) -> SourceText:
        if not source_request.path:
            raise ValueError("PDF source requires a file path")
        return SourceText(
            kind=source_request.kind,
            text=self.extract_text(source_request.path),
            path=source_request.path,
            metadata=dict(source_request.metadata),
        )
