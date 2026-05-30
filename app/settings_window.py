from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.theme_system import Theme, sorted_theme_names
from app.ui_config import APP_NAME


class SettingsWindow(QDialog):
    def __init__(
        self,
        *,
        themes: dict[str, Theme],
        current_theme_name: str,
        open_editor_before_render_action: QAction,
        on_theme_changed: Callable[[str], None],
        on_delete_saved_files: Callable[[], None],
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._on_theme_changed = on_theme_changed

        self.setWindowTitle(f"{APP_NAME} Settings")
        self.setModal(False)
        self.resize(420, 300)

        layout = QVBoxLayout()
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        theme_group = QFrame()
        theme_group.setObjectName("utilityGroup")
        theme_layout = QVBoxLayout()
        theme_layout.setContentsMargins(16, 16, 16, 16)
        theme_layout.setSpacing(10)
        theme_label = QLabel("Theme")
        theme_label.setObjectName("panelHint")
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeCombo")
        for theme_name in sorted_theme_names(themes):
            self.theme_combo.addItem(theme_name)
        theme_index = self.theme_combo.findText(current_theme_name)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)

        generation_group = QFrame()
        generation_group.setObjectName("utilityGroup")
        generation_layout = QVBoxLayout()
        generation_layout.setContentsMargins(16, 16, 16, 16)
        generation_layout.setSpacing(10)
        generation_label = QLabel("Before generating")
        generation_label.setObjectName("panelHint")
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
        generation_layout.addWidget(generation_label)
        generation_layout.addWidget(self.open_editor_before_render_checkbox)
        generation_group.setLayout(generation_layout)

        cleanup_group = QFrame()
        cleanup_group.setObjectName("utilityGroup")
        cleanup_layout = QVBoxLayout()
        cleanup_layout.setContentsMargins(16, 16, 16, 16)
        cleanup_layout.setSpacing(10)
        cleanup_label = QLabel("Cleanup")
        cleanup_label.setObjectName("panelHint")
        self.delete_saved_files_button = QPushButton("Delete saved files")
        self.delete_saved_files_button.setObjectName("utilityDanger")
        self.delete_saved_files_button.clicked.connect(on_delete_saved_files)
        cleanup_layout.addWidget(cleanup_label)
        cleanup_layout.addWidget(self.delete_saved_files_button)
        cleanup_group.setLayout(cleanup_layout)

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_button = QPushButton("Close")
        close_button.setObjectName("secondaryAction")
        close_button.clicked.connect(self.close)
        close_row.addWidget(close_button)

        layout.addWidget(theme_group)
        layout.addWidget(generation_group)
        layout.addWidget(cleanup_group)
        layout.addStretch()
        layout.addLayout(close_row)
        self.setLayout(layout)

    def set_busy(self, busy: bool) -> None:
        self.open_editor_before_render_checkbox.setEnabled(not busy)
        self.delete_saved_files_button.setEnabled(not busy)

    def set_current_theme(self, theme_name: str) -> None:
        theme_index = self.theme_combo.findText(theme_name)
        if theme_index < 0 or self.theme_combo.currentIndex() == theme_index:
            return

        was_blocked = self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(theme_index)
        self.theme_combo.blockSignals(was_blocked)
