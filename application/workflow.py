from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from core.document_editor import DocumentEditorCodec
from core.models import Document, ensure_document
from core.workflow_models import (
    DeleteJobsResult,
    EditorViewResult,
    RenderArtifact,
    RenderResult,
    SourceRequest,
    SourceText,
    UiActionResult,
    WorkflowSession,
)
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
        self._enrichers = list(enrichers or [])
        self.session = session or WorkflowSession()

    @property
    def default_structuring_mode(self) -> str:
        return DEFAULT_STRUCTURING_MODE

    @property
    def structuring_mode_options(self) -> tuple[tuple[str, str], ...]:
        return STRUCTURING_MODE_OPTIONS

    @property
    def jobs_workspace_path(self) -> Path:
        return self._artifact_store.get_workspace_path()

    def apply_session(self, session: WorkflowSession | None) -> None:
        if session is not None:
            self.session = session

    def load_source(self, source_request: SourceRequest) -> SourceText:
        source, _session = self._load_source_for_session(source_request, self.session)
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
        return source

    def remember_text_source(self, text: str, *, source_path: str | None = None) -> SourceText:
        return self.remember_source_text(text, source_kind="text", source_path=source_path)

    def load_pdf_source(self, pdf_path: str) -> SourceText:
        return self.load_source(SourceRequest(kind="pdf", path=pdf_path))

    def prepare_pdf_for_ui(
        self,
        *,
        pdf_path: str,
        mode: str,
        open_editor_before_render: bool,
    ) -> UiActionResult:
        source, session = self._load_source_for_session(
            SourceRequest(kind="pdf", path=pdf_path),
            self.session,
        )
        if open_editor_before_render:
            editor_view = self.build_editor_view(
                text=source.text,
                mode=mode,
                source_kind=source.kind,
                source_path=source.path,
                metadata=source.metadata,
                session=session,
            )
            return UiActionResult(
                view_mode="editor",
                display_text=editor_view.editor_text,
                session=editor_view.session,
            )

        render_result = self.render_source(
            text=source.text,
            mode=mode,
            source_kind=source.kind,
            source_path=source.path,
            metadata=source.metadata,
            persist=True,
            session=session,
        )
        return UiActionResult(
            view_mode="input",
            display_text=source.text,
            render_result=render_result,
            session=render_result.session,
        )

    def build_document(
        self,
        *,
        text: str,
        mode: str,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
        session: WorkflowSession | None = None,
    ) -> Document:
        source = self.remember_source_text(
            text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        _document, _session = self._build_document(source.text, mode, session or self.session)
        return _document

    def build_editor_view(
        self,
        *,
        text: str,
        mode: str,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
        session: WorkflowSession | None = None,
    ) -> EditorViewResult:
        source = self.remember_source_text(
            text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        base_session = (session or self.session).with_source(source)
        document, next_session = self._build_document(source.text, mode, base_session)
        editor_text = self._editor_codec.to_text(document)
        return EditorViewResult(
            source=source,
            document=document,
            editor_text=editor_text,
            session=next_session,
        )

    def open_editor_for_ui(
        self,
        *,
        text: str,
        mode: str,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> UiActionResult:
        editor_view = self.build_editor_view(
            text=text,
            mode=mode,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        return UiActionResult(
            view_mode="editor",
            display_text=editor_view.editor_text,
            session=editor_view.session,
        )

    def render_source(
        self,
        *,
        text: str,
        mode: str,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
        persist: bool = True,
        session: WorkflowSession | None = None,
    ) -> RenderResult:
        source = self.remember_source_text(
            text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        base_session = (session or self.session).with_source(source)
        document, next_session = self._build_document(source.text, mode, base_session)
        editor_text = self._editor_codec.to_text(document)
        return self._render_document(
            source=source,
            document=document,
            editor_text=editor_text,
            structuring_mode=mode,
            used_editor=False,
            persist=persist,
            session=next_session,
        )

    def render_editor(
        self,
        *,
        editor_text: str,
        source_text: str | None = None,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
        persist: bool = True,
        session: WorkflowSession | None = None,
    ) -> RenderResult:
        base_session = session or self.session
        current_document = base_session.current_document
        if current_document is None:
            document = self._editor_codec.from_text(editor_text, mode="strict")
        else:
            document = self._editor_codec.from_text(
                editor_text,
                mode="strict",
                base_document=current_document,
            )
        source, next_session = self._resolve_source(
            session=base_session,
            fallback_text=source_text or editor_text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        return self._render_document(
            source=source,
            document=document,
            editor_text=editor_text,
            structuring_mode="editor",
            used_editor=True,
            persist=persist,
            session=next_session.with_document(document, mode="editor"),
        )

    def render_for_ui(
        self,
        *,
        view_mode: str,
        visible_text: str,
        mode: str,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
        persist: bool = True,
        session: WorkflowSession | None = None,
    ) -> UiActionResult:
        base_session = session or self.session
        if view_mode == "editor":
            render_result = self.render_editor(
                editor_text=visible_text,
                source_kind=source_kind,
                source_path=source_path,
                metadata=metadata,
                persist=persist,
                session=base_session,
            )
            return UiActionResult(
                view_mode="editor",
                display_text=visible_text,
                render_result=render_result,
                session=render_result.session,
            )

        render_result = self.render_source(
            text=visible_text,
            mode=mode,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
            persist=persist,
            session=base_session,
        )
        return UiActionResult(
            view_mode="input",
            display_text=visible_text,
            render_result=render_result,
            session=render_result.session,
        )

    def primary_action_for_ui(
        self,
        *,
        view_mode: str,
        visible_text: str,
        mode: str,
        open_editor_before_render: bool,
        source_kind: str = "text",
        source_path: str | None = None,
        metadata: dict[str, object] | None = None,
        persist: bool = True,
        session: WorkflowSession | None = None,
    ) -> UiActionResult:
        base_session = session or self.session
        if view_mode == "editor":
            return self.render_for_ui(
                view_mode=view_mode,
                visible_text=visible_text,
                mode=mode,
                source_kind=source_kind,
                source_path=source_path,
                metadata=metadata,
                persist=persist,
                session=base_session,
            )

        if open_editor_before_render:
            return self.open_editor_for_ui(
                text=visible_text,
                mode=mode,
                source_kind=source_kind,
                source_path=source_path,
                metadata=metadata,
            )

        return self.render_for_ui(
            view_mode="input",
            visible_text=visible_text,
            mode=mode,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
            persist=persist,
            session=base_session,
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
        session: WorkflowSession | None = None,
    ) -> RenderResult:
        document = ensure_document(document)
        if not document.blocks:
            raise ValueError("No text to process")
        base_session = session or self.session

        resolved_editor_text = (
            editor_text
            if editor_text and editor_text.strip()
            else self._editor_codec.to_text(document)
        )
        source, next_session = self._resolve_source(
            session=base_session,
            fallback_text=source_text or resolved_editor_text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        return self._render_document(
            source=source,
            document=document,
            editor_text=resolved_editor_text,
            structuring_mode=structuring_mode or self.default_structuring_mode,
            used_editor=used_editor,
            persist=persist,
            session=next_session.with_document(
                document,
                mode=structuring_mode or self.default_structuring_mode,
            ),
        )

    def delete_all_jobs(self) -> DeleteJobsResult:
        deleted_count = self._artifact_store.delete_all()
        return DeleteJobsResult(
            deleted_count=deleted_count,
            session=self.session.cleared_output(),
        )

    def clear_active_state(self) -> None:
        self.session = self.session.cleared_active_state()

    def _build_document(
        self,
        text: str,
        mode: str,
        session: WorkflowSession,
    ) -> tuple[Document, WorkflowSession]:
        if not text or not text.strip():
            raise ValueError("No text to process")
        document = self._document_builder.build(text, mode)
        if not document.blocks:
            raise ValueError("No text to process")
        for enricher in self._enrichers:
            document = enricher.enrich(document)
        return document, session.with_document(document, mode=mode)

    def _resolve_source(
        self,
        *,
        session: WorkflowSession,
        fallback_text: str,
        source_kind: str,
        source_path: str | None,
        metadata: dict[str, object] | None,
    ) -> tuple[SourceText, WorkflowSession]:
        source = session.source
        if source is not None:
            return source, session
        source = self.remember_source_text(
            fallback_text,
            source_kind=source_kind,
            source_path=source_path,
            metadata=metadata,
        )
        return source, session.with_source(source)

    def _load_source_for_session(
        self,
        source_request: SourceRequest,
        session: WorkflowSession,
    ) -> tuple[SourceText, WorkflowSession]:
        source = self._text_extractor.extract(source_request)
        if not source.text.strip():
            if source.kind == "pdf":
                raise ValueError("No selectable text found in PDF")
            raise ValueError("No text to process")
        return source, session.with_source(source)

    def _render_document(
        self,
        *,
        source: SourceText,
        document: Document,
        editor_text: str,
        structuring_mode: str,
        used_editor: bool,
        persist: bool,
        session: WorkflowSession,
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
        next_session = session.with_render(artifact, stored_output)
        return RenderResult(
            source=source,
            document=document,
            editor_text=editor_text,
            artifact=artifact,
            stored_output=stored_output,
            session=next_session,
        )


def build_default_workflow() -> WorkflowService:
    return WorkflowService(
        text_extractor=DefaultTextExtractor(),
        document_builder=StructuredDocumentBuilder(),
        editor_codec=DocumentEditorCodec(),
        renderer=HtmlRenderer(),
        artifact_store=JobStore(),
    )
