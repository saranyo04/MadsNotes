from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit

from core.note_highlights import (
    HIGHLIGHT_COLORS,
    HighlightSpan,
    clear_highlight,
    normalize_highlight_spans,
    set_highlight,
)


class EditorHighlightController(QObject):
    def __init__(self, editor: QPlainTextEdit) -> None:
        super().__init__(editor)
        self._editor = editor
        self._highlights: list[HighlightSpan] = []
        self._editor.document().contentsChange.connect(self._handle_contents_change)

    def highlights(self) -> list[HighlightSpan]:
        return normalize_highlight_spans(
            list(self._highlights),
            text_length=len(self._editor.toPlainText()),
        )

    def set_highlights(self, highlights: list[HighlightSpan]) -> None:
        self._highlights = normalize_highlight_spans(
            highlights,
            text_length=len(self._editor.toPlainText()),
        )
        self.refresh()

    def clear(self) -> None:
        self._highlights = []
        self.refresh()

    def apply_to_selection(self, color: str) -> bool:
        cursor = self._editor.textCursor()
        if not cursor.hasSelection():
            return False
        self._highlights = set_highlight(
            self._highlights,
            start=cursor.selectionStart(),
            end=cursor.selectionEnd(),
            color=color,
            text_length=len(self._editor.toPlainText()),
        )
        self.refresh()
        return True

    def remove_from_selection(self) -> bool:
        cursor = self._editor.textCursor()
        if not cursor.hasSelection():
            return False
        self._highlights = clear_highlight(
            self._highlights,
            start=cursor.selectionStart(),
            end=cursor.selectionEnd(),
            text_length=len(self._editor.toPlainText()),
        )
        self.refresh()
        return True

    def refresh(self) -> None:
        text_length = len(self._editor.toPlainText())
        self._highlights = normalize_highlight_spans(
            self._highlights,
            text_length=text_length,
        )

        extra_selections: list[QTextEdit.ExtraSelection] = []
        document = self._editor.document()
        for span in self._highlights:
            selection = QTextEdit.ExtraSelection()
            selection.cursor = QTextCursor(document)
            selection.cursor.setPosition(span.start)
            selection.cursor.setPosition(span.end, QTextCursor.KeepAnchor)

            char_format = QTextCharFormat()
            char_format.setBackground(QColor(HIGHLIGHT_COLORS[span.color]))
            char_format.setForeground(QColor("#2F3340"))
            selection.format = char_format
            extra_selections.append(selection)

        self._editor.setExtraSelections(extra_selections)

    def _handle_contents_change(
        self,
        position: int,
        chars_removed: int,
        chars_added: int,
    ) -> None:
        if not self._highlights:
            self.refresh()
            return

        delta = chars_added - chars_removed
        changed_end = position + chars_removed
        adjusted: list[HighlightSpan] = []

        for span in self._highlights:
            if chars_removed == 0:
                adjusted.append(self._adjust_for_insertion(span, position, chars_added))
                continue

            if span.end <= position:
                adjusted.append(span)
                continue
            if span.start >= changed_end:
                adjusted.append(
                    HighlightSpan(span.start + delta, span.end + delta, span.color)
                )
                continue

            start = min(span.start, position)
            end = max(position, span.end + delta)
            adjusted.append(HighlightSpan(start, end, span.color))

        self._highlights = normalize_highlight_spans(
            adjusted,
            text_length=len(self._editor.toPlainText()),
        )
        self.refresh()

    def _adjust_for_insertion(
        self,
        span: HighlightSpan,
        position: int,
        chars_added: int,
    ) -> HighlightSpan:
        if chars_added <= 0 or position > span.end:
            return span
        if position <= span.start:
            return HighlightSpan(
                span.start + chars_added,
                span.end + chars_added,
                span.color,
            )
        return HighlightSpan(span.start, span.end + chars_added, span.color)
