from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.config import get_saved_notes_path


@dataclass(frozen=True)
class SavedNote:
    path: Path
    title: str
    modified_at: datetime


class SavedNotesStore:
    _INVALID_FILENAME_CHARACTERS = '<>:"/\\|?*'

    def get_notes_path(self) -> Path:
        notes_path = get_saved_notes_path()
        notes_path.mkdir(parents=True, exist_ok=True)
        return notes_path

    def list_notes(self) -> list[SavedNote]:
        notes_path = self.get_notes_path()
        notes: list[SavedNote] = []
        for path in notes_path.glob("*.md"):
            if not path.is_file():
                continue
            modified_at = datetime.fromtimestamp(path.stat().st_mtime)
            notes.append(
                SavedNote(
                    path=path,
                    title=path.stem,
                    modified_at=modified_at,
                )
            )
        return sorted(notes, key=lambda note: note.modified_at, reverse=True)

    def newest_note(self) -> SavedNote | None:
        notes = self.list_notes()
        return notes[0] if notes else None

    def load(self, note: SavedNote | Path) -> str:
        path = note.path if isinstance(note, SavedNote) else note
        return path.read_text(encoding="utf-8")

    def save(
        self,
        text: str,
        note_name: str = "",
        *,
        rendered_output_path: Path | None = None,
    ) -> SavedNote:
        notes_path = self.get_notes_path()
        title = self._note_title(note_name)
        path = self._available_note_path(notes_path, title)
        path.write_text(text, encoding="utf-8")
        if rendered_output_path is not None:
            self._write_note_metadata(path, {"rendered_output_path": str(rendered_output_path)})
        modified_at = datetime.fromtimestamp(path.stat().st_mtime)
        return SavedNote(path=path, title=path.stem, modified_at=modified_at)

    def rendered_output_path(self, note: SavedNote | Path) -> Path | None:
        note_path = note.path if isinstance(note, SavedNote) else note
        metadata_path = note_path.with_suffix(".json")
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        rendered_output_path = metadata.get("rendered_output_path")
        if not isinstance(rendered_output_path, str) or not rendered_output_path.strip():
            return None
        return Path(rendered_output_path)

    def _write_note_metadata(self, note_path: Path, metadata: dict[str, Any]) -> None:
        note_path.with_suffix(".json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _note_title(self, note_name: str) -> str:
        title = note_name.strip()
        if title.lower().endswith(".md"):
            title = title[:-3].strip()

        title = "".join(
            " "
            if character in self._INVALID_FILENAME_CHARACTERS or ord(character) < 32
            else character
            for character in title
        )
        title = " ".join(title.split()).strip(" .")
        if title:
            return title
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def _available_note_path(self, notes_path: Path, title: str) -> Path:
        path = notes_path / f"{title}.md"
        suffix = 2
        while path.exists():
            path = notes_path / f"{title} ({suffix}).md"
            suffix += 1
        return path

    def delete_all(self) -> int:
        notes_path = self.get_notes_path()
        deleted_count = 0
        for path in notes_path.iterdir():
            if path.is_file():
                path.unlink()
                deleted_count += 1
            elif path.is_dir():
                shutil.rmtree(path)
                deleted_count += 1
        return deleted_count
