from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "Mad's Chinese"
APP_SLUG = "madschinese"
APP_ID = "madschinese.desktop"

PRIMARY_WORKSPACE_DIRNAME = "madschinese_workspace"
LEGACY_WORKSPACE_DIRNAME = "workspace"
HISTORY_DIRNAME = "history"
SAVED_NOTES_DIRNAME = "saved_notes"
JOB_FOLDER_PREFIX = "job_"
OUTPUT_HTML_FILENAME = "output.html"

PDF_FILE_FILTER = "PDF Files (*.pdf)"


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_primary_workspace_path() -> Path:
    return get_app_root() / PRIMARY_WORKSPACE_DIRNAME


def get_legacy_workspace_path() -> Path:
    return get_app_root() / LEGACY_WORKSPACE_DIRNAME


def get_history_path() -> Path:
    return get_app_root() / HISTORY_DIRNAME


def get_saved_notes_path() -> Path:
    return get_app_root() / SAVED_NOTES_DIRNAME
