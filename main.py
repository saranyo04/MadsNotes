import sys
from pathlib import Path

from infrastructure.config import APP_ID


def _set_windows_app_id() -> None:
    if sys.platform != "win32":
        return

    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def _resolve_launch_file(argv: list[str]) -> str | None:
    for argument in argv[1:]:
        if not argument or argument.startswith("-"):
            continue

        path = Path(argument).expanduser()
        try:
            return str(path.resolve(strict=False))
        except OSError:
            return str(path)

    return None


if __name__ == "__main__":
    _set_windows_app_id()
    from app.main_window import run_app

    run_app(initial_file_path=_resolve_launch_file(sys.argv))
