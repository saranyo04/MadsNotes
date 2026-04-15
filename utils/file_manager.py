# utils/file_manager.py

from pathlib import Path

def create_job():
    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)

    existing = [int(p.name.split("_")[1]) for p in workspace.glob("job_*") if "_" in p.name]
    next_id = max(existing, default=0) + 1

    job_path = workspace / f"job_{next_id:03d}"
    (job_path / "input").mkdir(parents=True)
    (job_path / "output").mkdir()

    return job_path