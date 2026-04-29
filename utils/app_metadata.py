"""Legacy compatibility wrapper for application/infrastructure config."""

from infrastructure.config import (
    APP_ID,
    APP_NAME,
    APP_SLUG,
    JOB_FOLDER_PREFIX,
    LEGACY_WORKSPACE_DIRNAME,
    OUTPUT_HTML_FILENAME,
    PDF_FILE_FILTER,
    PRIMARY_WORKSPACE_DIRNAME,
    get_app_root,
    get_legacy_workspace_path,
    get_primary_workspace_path,
)
