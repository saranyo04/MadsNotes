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
class EditorViewResult:
    source: SourceText
    document: Document
    editor_text: str


@dataclass
class RenderResult:
    source: SourceText
    document: Document
    editor_text: str
    artifact: RenderArtifact
    stored_output: StoredOutput | None = None
