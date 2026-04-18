import json
import shutil
from pathlib import Path


def create_job() -> Path:
    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)

    existing = [int(p.name.split("_")[1]) for p in workspace.glob("job_*") if "_" in p.name]
    next_id = max(existing, default=0) + 1

    job_path = workspace / f"job_{next_id:03d}"
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


def delete_all_jobs(workspace_path: str | Path = "workspace") -> int:
    workspace = Path(workspace_path)

    if not workspace.exists():
        return 0

    deleted_count = 0

    for job_path in workspace.iterdir():
        if job_path.is_dir() and job_path.name.startswith("job_"):
            shutil.rmtree(job_path)
            deleted_count += 1

    return deleted_count
