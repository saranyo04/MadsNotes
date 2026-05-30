from __future__ import annotations

from dataclasses import dataclass, field, replace
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

    def with_source(self, source: SourceText) -> "WorkflowSession":
        return replace(self, source=source)

    def with_document(self, document: Document, mode: str | None = None) -> "WorkflowSession":
        return replace(
            self,
            current_document=document,
            last_structuring_mode=mode if mode is not None else self.last_structuring_mode,
        )

    def with_render(self, stored_output: StoredOutput | None) -> "WorkflowSession":
        return replace(self, last_output=stored_output)

    def cleared_output(self) -> "WorkflowSession":
        return replace(self, last_output=None)

    def cleared_active_state(self) -> "WorkflowSession":
        return replace(self, source=None, current_document=None)


@dataclass
class EditorViewResult:
    source: SourceText
    document: Document
    editor_text: str
    session: WorkflowSession


@dataclass
class RenderResult:
    source: SourceText
    document: Document
    editor_text: str | None
    artifact: RenderArtifact
    stored_output: StoredOutput | None = None
    session: WorkflowSession | None = None


@dataclass
class UiActionResult:
    view_mode: str
    display_text: str
    render_result: RenderResult | None = None
    session: WorkflowSession | None = None


@dataclass
class DeleteJobsResult:
    deleted_count: int
    session: WorkflowSession
