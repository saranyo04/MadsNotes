from __future__ import annotations

from collections.abc import Sequence

from core.document_editor import DocumentEditorCodec
from core.models import Document, ensure_document
from core.text_structurer import (
    DEFAULT_STRUCTURING_MODE,
    STRUCTURING_MODE_OPTIONS,
    StructuredDocumentBuilder,
)
from infrastructure.html_renderer import HtmlRenderer
from infrastructure.job_store import JobStore
from infrastructure.ocr_extractor import NullOcrExtractor
from infrastructure.pdf_extractor import PdfTextExtractor

from .interfaces import ArtifactStore, DocumentBuilder, DocumentEnricher, EditorCodec, Renderer, TextExtractor
from .results import EditorViewResult, RenderResult, SourceRequest, SourceText
from .session import WorkflowSession


class IdentityDocumentEnricher:
    def enrich(self, document: Document) -> Document:
        return document


class DefaultTextExtractor:
    def __init__(
        self,
        pdf_extractor: PdfTextExtractor | None = None,
        ocr_extractor: NullOcrExtractor | None = None,
    ) -> None:
        self._pdf_extractor = pdf_extractor or PdfTextExtractor()
        self._ocr_extractor = ocr_extractor or NullOcrExtractor()

    def extract(self, source_request: SourceRequest) -> SourceText:
        if source_request.kind == "text":
            if source_request.text is None:
                raise ValueError("Text source requires text content")
            return SourceText(
                kind=source_request.kind,
                text=source_request.text,
                path=source_request.path,
                metadata=dict(source_request.metadata),
            )

        if source_request.kind == "pdf":
            source = self._pdf_extractor.extract(source_request)
            if source.text.strip():
                return source
            return self._ocr_extractor.extract(source_request)

        if source_request.kind == "image":
            return self._ocr_extractor.extract(source_request)

        raise ValueError(f"Unsupported source kind: {source_request.kind}")


class WorkflowService:
    def __init__(
        self,
        *,
        text_extractor: TextExtractor,
        document_builder: DocumentBuilder,
        editor_codec: EditorCodec,
        renderer: Renderer,
        artifact_store: ArtifactStore,
        enrichers: Sequence[DocumentEnricher] | None = None,
        session: WorkflowSession | None = None,
    ) -> None:
        self._text_extractor = text_extractor
        self._document_builder = document_builder
        self._editor_codec = editor_codec
        self._renderer = renderer
        self._artifact_store = artifact_store
        self._enrichers = list(enrichers or [IdentityDocumentEnricher()])
        self.session = session or WorkflowSession()

    @property
    def default_structuring_mode(self) -> str:
        return DEFAULT_STRUCTURING_MODE

    @property
    def structuring_mode_options(self) -> tuple[tuple[str, str], ...]:
        return STRUCTURING_MODE_OPTIONS

    def load_source(self, source_request: SourceRequest) -> SourceText:
        source = self._text_extractor.extract(source_request)
        if not source.text.strip():
            if source.kind == "pdf":
                raise ValueError("No selectable text found in PDF")
            raise ValueError("No text to process")
        self.session.remember_source(source)
        return source

    def remember_source_text(
        self,
        text: str,
        *,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> SourceText:
        source = SourceText(
            kind=source_kind,
            text=text,
            path=source_path,
            metadata=dict(metadata or {}),
        )
        if not source.text.strip():
            raise ValueError("No text to process")
        self.session.remember_source(source)
        return source

    def remember_text_source(self, text: str, *, source_path: str | None = None) -> SourceText:
        return self.remember_source_text(text, source_kind="text", source_path=source_path)

    def load_pdf_source(self, pdf_path: str) -> SourceText:
        return self.load_source(SourceRequest(kind="pdf", path=pdf_path))

    def build_document(
        self,
        *,
        text: str,
        mode: str,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Document:
        source = self.remember_source_text(
            text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        return self._build_document(source.text, mode)

    def build_editor_view(
        self,
        *,
        text: str,
        mode: str,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> EditorViewResult:
        source = self.remember_source_text(
            text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        document = self._build_document(source.text, mode)
        editor_text = self._editor_codec.to_text(document)
        self.session.remember_editor_text(editor_text)
        return EditorViewResult(source=source, document=document, editor_text=editor_text)

    def render_source(
        self,
        *,
        text: str,
        mode: str,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
        persist: bool = True,
    ) -> RenderResult:
        source = self.remember_source_text(
            text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        document = self._build_document(source.text, mode)
        editor_text = self._editor_codec.to_text(document)
        return self._render(
            source=source,
            document=document,
            editor_text=editor_text,
            structuring_mode=mode,
            used_editor=False,
            persist=persist,
        )

    def render_editor(
        self,
        *,
        editor_text: str,
        source_text: str,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
        persist: bool = True,
    ) -> RenderResult:
        source = self.remember_source_text(
            source_text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        document = self._editor_codec.from_text(editor_text, mode="strict")
        return self._render(
            source=source,
            document=document,
            editor_text=editor_text,
            structuring_mode="editor",
            used_editor=True,
            persist=persist,
        )

    def render_document(
        self,
        *,
        document: Document,
        editor_text: str | None = None,
        source_text: str | None = None,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
        structuring_mode: str | None = None,
        used_editor: bool = False,
        persist: bool = True,
    ) -> RenderResult:
        document = ensure_document(document)
        if not document.blocks:
            raise ValueError("No text to process")

        resolved_editor_text = (
            editor_text
            if editor_text and editor_text.strip()
            else self._editor_codec.to_text(document)
        )
        resolved_source_text = (
            source_text if source_text and source_text.strip() else resolved_editor_text
        )
        source = self.remember_source_text(
            resolved_source_text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        self.session.remember_document(document, mode=structuring_mode)
        return self._render(
            source=source,
            document=document,
            editor_text=resolved_editor_text,
            structuring_mode=structuring_mode or self.default_structuring_mode,
            used_editor=used_editor,
            persist=persist,
        )

    def delete_all_jobs(self) -> int:
        deleted_count = self._artifact_store.delete_all()
        self.session.clear_output()
        return deleted_count

    def clear_active_state(self) -> None:
        self.session.clear_active_state()

    def _build_document(self, text: str, mode: str) -> Document:
        if not text or not text.strip():
            raise ValueError("No text to process")
        document = self._document_builder.build(text, mode)
        if not document.blocks:
            raise ValueError("No text to process")
        for enricher in self._enrichers:
            document = enricher.enrich(document)
        self.session.remember_document(document, mode=mode)
        return document

    def _render(
        self,
        *,
        source: SourceText,
        document: Document,
        editor_text: str,
        structuring_mode: str,
        used_editor: bool,
        persist: bool,
    ) -> RenderResult:
        artifact = self._renderer.render(document)
        stored_output = None
        if persist:
            stored_output = self._artifact_store.persist(
                artifact,
                source_text=source,
                editor_text=editor_text,
                session_meta={
                    "structuring_mode": structuring_mode,
                    "used_editor": used_editor,
                },
            )
        self.session.remember_document(document, mode=structuring_mode)
        self.session.remember_editor_text(editor_text)
        self.session.remember_render(artifact, stored_output)
        return RenderResult(
            source=source,
            document=document,
            editor_text=editor_text,
            artifact=artifact,
            stored_output=stored_output,
        )


def build_default_workflow() -> WorkflowService:
    return WorkflowService(
        text_extractor=DefaultTextExtractor(),
        document_builder=StructuredDocumentBuilder(),
        editor_codec=DocumentEditorCodec(),
        renderer=HtmlRenderer(),
        artifact_store=JobStore(),
    )
