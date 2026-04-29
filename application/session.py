from __future__ import annotations

from dataclasses import dataclass

from core.models import Document

from .results import RenderArtifact, SourceText, StoredOutput


@dataclass
class WorkflowSession:
    source: SourceText | None = None
    current_document: Document | None = None
    editor_text: str | None = None
    last_render: RenderArtifact | None = None
    last_output: StoredOutput | None = None
    last_structuring_mode: str | None = None

    def remember_source(self, source: SourceText) -> None:
        self.source = source

    def remember_document(self, document: Document, mode: str | None = None) -> None:
        self.current_document = document
        if mode is not None:
            self.last_structuring_mode = mode

    def remember_editor_text(self, editor_text: str) -> None:
        self.editor_text = editor_text

    def remember_render(
        self,
        render_artifact: RenderArtifact,
        stored_output: StoredOutput | None,
    ) -> None:
        self.last_render = render_artifact
        self.last_output = stored_output

    def clear_output(self) -> None:
        self.last_render = None
        self.last_output = None

    def clear_active_state(self) -> None:
        self.source = None
        self.current_document = None
        self.editor_text = None
