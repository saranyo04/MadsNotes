from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
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
        on_theme_changed: Callable[[str], None],
        on_open_saved_notes_folder: Callable[[], None],
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
        theme_group.layout().addWidget(self.theme_combo)
        self.set_current_theme(current_theme_name)

        saved_notes_group = self._build_group("Saved Notes")
        self.open_saved_notes_folder_button = QPushButton("Open Saved Notes Folder")
        self.open_saved_notes_folder_button.setObjectName("secondaryAction")
        self.open_saved_notes_folder_button.setFixedWidth(240)
        self.open_saved_notes_folder_button.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )
        self.open_saved_notes_folder_button.clicked.connect(on_open_saved_notes_folder)
        saved_notes_group.layout().addWidget(self.open_saved_notes_folder_button)

        cleanup_group = self._build_group("Cleanup")
        cleanup_hint = QLabel(
            "History and saved notes are stored separately."
        )
        cleanup_hint.setObjectName("panelHint")
        self.delete_history_button = QPushButton("Delete All History")
        self.delete_history_button.setObjectName("utilityDanger")
        self.delete_history_button.setFixedWidth(190)
        self.delete_history_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.delete_history_button.clicked.connect(on_delete_history)
        self.delete_saved_notes_button = QPushButton("Delete All Saved Notes")
        self.delete_saved_notes_button.setObjectName("utilityDanger")
        self.delete_saved_notes_button.setFixedWidth(210)
        self.delete_saved_notes_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.delete_saved_notes_button.clicked.connect(on_delete_saved_notes)
        cleanup_actions = QHBoxLayout()
        cleanup_actions.setContentsMargins(0, 0, 0, 0)
        cleanup_actions.setSpacing(12)
        cleanup_actions.addWidget(self.delete_history_button)
        cleanup_actions.addWidget(self.delete_saved_notes_button)
        cleanup_actions.addStretch()
        cleanup_group.layout().addWidget(cleanup_hint)
        cleanup_group.layout().addLayout(cleanup_actions)

        layout.addWidget(header)
        layout.addWidget(helper)
        layout.addWidget(theme_group)
        layout.addWidget(saved_notes_group)
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
        self.open_saved_notes_folder_button.setEnabled(not busy)
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
            return
