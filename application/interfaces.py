from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, TypeVar

from core.models import Document
from core.workflow_models import RenderArtifact, SourceRequest, SourceText, StoredOutput

T = TypeVar("T")


class TextExtractor(Protocol):
    def extract(self, source_request: SourceRequest) -> SourceText:
        ...


class DocumentBuilder(Protocol):
    def build(self, text: str, mode: str) -> Document:
        ...


class EditorCodec(Protocol):
    def to_text(self, document: Document) -> str:
        ...

    def from_text(
        self,
        editor_text: str,
        mode: str = "strict",
        base_document: Document | None = None,
    ) -> Document:
        ...


class DocumentEnricher(Protocol):
    def enrich(self, document: Document) -> Document:
        ...


class Renderer(Protocol):
    def render(self, document: Document) -> RenderArtifact:
        ...


class ArtifactStore(Protocol):
    def persist(
        self,
        render_artifact: RenderArtifact,
        source_text: SourceText,
        editor_text: str | None,
        session_meta: dict[str, object],
    ) -> StoredOutput:
        ...

    def delete_all(self) -> int:
        ...

    def get_workspace_path(self) -> Path:
        ...


class TaskRunner(Protocol):
    def submit(
        self,
        fn: Callable[[], T],
        on_success: Callable[[T], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        ...
