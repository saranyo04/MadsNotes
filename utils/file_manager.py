import json
import shutil
from pathlib import Path

from utils.app_metadata import (
    JOB_FOLDER_PREFIX,
    get_legacy_workspace_path,
    get_primary_workspace_path,
)


def get_workspace_path() -> Path:
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


def _job_directories(workspace: Path) -> list[Path]:
    return [
        path
        for path in workspace.iterdir()
        if path.is_dir() and path.name.startswith(JOB_FOLDER_PREFIX)
    ]


def create_job() -> Path:
    workspace = get_workspace_path()

    existing = []
    for path in _job_directories(workspace):
        suffix = path.name[len(JOB_FOLDER_PREFIX):]
        if suffix.isdigit():
            existing.append(int(suffix))

    next_id = max(existing, default=0) + 1
    job_path = workspace / f"{JOB_FOLDER_PREFIX}{next_id:03d}"

    (job_path / "input").mkdir(parents=True)
    (job_path / "output").mkdir()

    return job_path


def write_job_text(job_path: Path, relative_path: str, content: str) -> Path:
    target_path = job_path / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    return target_path


def write_job_json(job_path: Path, relative_path: str, payload: dict) -> Path:
    target_path = job_path / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target_path


def delete_all_jobs() -> int:
    deleted_count = 0

    for workspace in {get_primary_workspace_path(), get_legacy_workspace_path()}:
        if not workspace.exists():
            continue

        for job_path in _job_directories(workspace):
            shutil.rmtree(job_path)
            deleted_count += 1

    return deleted_count
