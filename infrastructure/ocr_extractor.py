from __future__ import annotations

from application.results import SourceRequest, SourceText


class NullOcrExtractor:
    def extract(self, source_request: SourceRequest) -> SourceText:
        raise NotImplementedError("OCR extraction is not configured")
