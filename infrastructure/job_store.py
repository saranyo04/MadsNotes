from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from application.results import RenderArtifact, SourceText, StoredOutput
from infrastructure.config import (
    JOB_FOLDER_PREFIX,
    OUTPUT_HTML_FILENAME,
    get_legacy_workspace_path,
    get_primary_workspace_path,
)


class JobStore:
    def get_workspace_path(self) -> Path:
        primary_workspace = get_primary_workspace_path()
        legacy_workspace = get_legacy_workspace_path()

        if primary_workspace.exists():
            primary_workspace.mkdir(exist_ok=True)
            return primary_workspace

        if legacy_workspace.exists():
            try:
                legacy_workspace.rename(primary_workspace)
                primary_workspace.mkdir(exist_ok=True)
                return primary_workspace
            except OSError:
                legacy_workspace.mkdir(exist_ok=True)
                return legacy_workspace

        primary_workspace.mkdir(exist_ok=True)
        return primary_workspace

    def _job_directories(self, workspace: Path) -> list[Path]:
        return [
            path
            for path in workspace.iterdir()
            if path.is_dir() and path.name.startswith(JOB_FOLDER_PREFIX)
        ]

    def create_job(self) -> Path:
        workspace = self.get_workspace_path()
        existing: list[int] = []
        for path in self._job_directories(workspace):
            suffix = path.name[len(JOB_FOLDER_PREFIX):]
            if suffix.isdigit():
                existing.append(int(suffix))

        next_id = max(existing, default=0) + 1
        job_path = workspace / f"{JOB_FOLDER_PREFIX}{next_id:03d}"
        (job_path / "input").mkdir(parents=True)
        (job_path / "output").mkdir()
        return job_path

    def write_job_text(self, job_path: Path, relative_path: str, content: str) -> Path:
        target_path = job_path / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return target_path

    def write_job_json(self, job_path: Path, relative_path: str, payload: dict[str, Any]) -> Path:
        target_path = job_path / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target_path

    def build_job_meta(
        self,
        render_artifact: RenderArtifact,
        *,
        source_text: SourceText,
        session_meta: dict[str, object],
        job_name: str,
    ) -> dict[str, Any]:
        blocks = render_artifact.document.blocks
        return {
            "job": job_name,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_kind": source_text.kind,
            "source_path": source_text.path,
            "structuring_mode": session_meta.get("structuring_mode"),
            "used_editor": bool(session_meta.get("used_editor")),
            "block_count": len(blocks),
            "block_types": [block.kind for block in blocks],
        }

    def persist(
        self,
        render_artifact: RenderArtifact,
        source_text: SourceText,
        editor_text: str | None,
        session_meta: dict[str, object],
    ) -> StoredOutput:
        job_path = self.create_job()
        output_path = job_path / "output" / OUTPUT_HTML_FILENAME
        source_file_path: Path | None = None
        structured_path: Path | None = None

        if source_text.text.strip():
            source_file_path = self.write_job_text(job_path, "input/source.txt", source_text.text)

        if editor_text and editor_text.strip():
            structured_path = self.write_job_text(job_path, "input/structured.txt", editor_text)

        output_path.write_text(render_artifact.html, encoding="utf-8")
        meta = self.build_job_meta(
            render_artifact,
            source_text=source_text,
            session_meta=session_meta,
            job_name=job_path.name,
        )
        meta_path = self.write_job_json(job_path, "meta.json", meta)
        return StoredOutput(
            job_path=job_path,
            output_path=output_path,
            source_path=source_file_path,
            structured_path=structured_path,
            meta_path=meta_path,
            metadata=meta,
        )

    def delete_all(self) -> int:
        deleted_count = 0
        for workspace in {get_primary_workspace_path(), get_legacy_workspace_path()}:
            if not workspace.exists():
                continue
            for job_path in self._job_directories(workspace):
                shutil.rmtree(job_path)
                deleted_count += 1
        return deleted_count
