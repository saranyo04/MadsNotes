from __future__ import annotations

"""Legacy compatibility wrapper around infrastructure.job_store.JobStore."""

from pathlib import Path
from typing import Any

from infrastructure.job_store import JobStore

_JOB_STORE = JobStore()


def get_workspace_path() -> Path:
    return _JOB_STORE.get_workspace_path()


def create_job() -> Path:
    return _JOB_STORE.create_job()


def write_job_text(job_path: Path, relative_path: str, content: str) -> Path:
    return _JOB_STORE.write_job_text(job_path, relative_path, content)


def write_job_json(job_path: Path, relative_path: str, payload: dict[str, Any]) -> Path:
    return _JOB_STORE.write_job_json(job_path, relative_path, payload)


def delete_all_jobs() -> int:
    return _JOB_STORE.delete_all()
