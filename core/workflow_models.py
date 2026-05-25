from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.models import Document


@dataclass
class SourceRequest:
    kind: str
    path: str | None = None
    text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceText:
    kind: str
    text: str
    path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderArtifact:
    document: Document
    html: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StoredOutput:
    job_path: Path
    output_path: Path
    source_path: Path | None = None
    structured_path: Path | None = None
    meta_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowSession:
    source: SourceText | None = None
    current_document: Document | None = None
    last_output: StoredOutput | None = None
    last_structuring_mode: str | None = None

    def set_source(self, source: SourceText) -> None:
        self.source = source

    def set_document(self, document: Document, mode: str | None = None) -> None:
        self.current_document = document
        if mode is not None:
            self.last_structuring_mode = mode

    def set_render_output(self, stored_output: StoredOutput | None) -> None:
        self.last_output = stored_output

    def clear_output(self) -> None:
        self.last_output = None

    def clear_active_state(self) -> None:
        self.source = None
        self.current_document = None


@dataclass
class EditorViewResult:
    source: SourceText
    document: Document
    editor_text: str


@dataclass
class RenderResult:
    source: SourceText
    document: Document
    editor_text: str | None
    artifact: RenderArtifact
    stored_output: StoredOutput | None = None


@dataclass
class DeleteJobsResult:
    deleted_count: int
