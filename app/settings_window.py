from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.theme_system import Theme, sorted_theme_names


class SettingsPage(QWidget):
    def __init__(
        self,
        *,
        themes: dict[str, Theme],
        current_theme_name: str,
        open_editor_before_render_action: QAction,
        on_theme_changed: Callable[[str], None],
        on_delete_history: Callable[[], None],
        on_delete_saved_notes: Callable[[], None],
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._themes = themes
        self._on_theme_changed = on_theme_changed

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        header = QLabel("Settings")
        header.setObjectName("sectionTitle")
        helper = QLabel("Adjust how notes are generated and saved.")
        helper.setObjectName("panelHint")

        theme_group = self._build_group("Theme")
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeCombo")
        for theme_name in sorted_theme_names(themes):
            self.theme_combo.addItem(theme_name)
        theme_index = self.theme_combo.findText(current_theme_name)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.current_theme_label = QLabel()
        self.current_theme_label.setObjectName("panelHint")
        theme_group.layout().addWidget(self.theme_combo)
        theme_group.layout().addWidget(self.current_theme_label)
        self.set_current_theme(current_theme_name)

        behavior_group = self._build_group("Behavior")
        self.open_editor_before_render_checkbox = QCheckBox(
            "Open editor before generating notes"
        )
        self.open_editor_before_render_checkbox.setChecked(
            open_editor_before_render_action.isChecked()
        )
        self.open_editor_before_render_checkbox.toggled.connect(
            open_editor_before_render_action.setChecked
        )
        open_editor_before_render_action.toggled.connect(
            self.open_editor_before_render_checkbox.setChecked
        )
        behavior_group.layout().addWidget(self.open_editor_before_render_checkbox)

        cleanup_group = self._build_group("Cleanup")
        cleanup_hint = QLabel(
            "History and saved notes are stored separately."
        )
        cleanup_hint.setObjectName("panelHint")
        self.delete_history_button = QPushButton("Delete All History")
        self.delete_history_button.setObjectName("utilityDanger")
        self.delete_history_button.clicked.connect(on_delete_history)
        self.delete_saved_notes_button = QPushButton("Delete All Saved Notes")
        self.delete_saved_notes_button.setObjectName("utilityDanger")
        self.delete_saved_notes_button.clicked.connect(on_delete_saved_notes)
        cleanup_group.layout().addWidget(cleanup_hint)
        cleanup_group.layout().addWidget(self.delete_history_button)
        cleanup_group.layout().addWidget(self.delete_saved_notes_button)

        layout.addWidget(header)
        layout.addWidget(helper)
        layout.addWidget(theme_group)
        layout.addWidget(behavior_group)
        layout.addWidget(cleanup_group)
        layout.addStretch()
        self.setLayout(layout)

    def _build_group(self, title: str) -> QFrame:
        group = QFrame()
        group.setObjectName("utilityGroup")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        group.setLayout(layout)
        return group

    def set_busy(self, busy: bool) -> None:
        self.open_editor_before_render_checkbox.setEnabled(not busy)
        self.delete_history_button.setEnabled(not busy)
        self.delete_saved_notes_button.setEnabled(not busy)

    def set_current_theme(self, theme_name: str) -> None:
        theme_index = self.theme_combo.findText(theme_name)
        if theme_index >= 0 and self.theme_combo.currentIndex() != theme_index:
            was_blocked = self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(theme_index)
            self.theme_combo.blockSignals(was_blocked)

        theme = self._themes.get(theme_name)
        if theme is None:
            self.current_theme_label.setText("Current theme: System fallback")
            return

        tokens = theme.tokens
        self.current_theme_label.setText(
            "Current theme: "
            f"{theme.name} | Primary {tokens.primary} | Secondary {tokens.secondary}"
        )
