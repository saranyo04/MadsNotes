from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QSize, QTimer, Qt
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QGraphicsDropShadowEffect,
    QPlainTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.shortcuts import install_shortcuts
from app.ui_config import APP_NAME, PDF_FILE_FILTER

if TYPE_CHECKING:
    from application.workflow import WorkflowService
    from app.qt_task_runner import QtTaskRunner
    from core.workflow_models import DeleteJobsResult, RenderResult, UiActionResult


class MainWindow(QWidget):
    def __init__(
        self,
        *,
        workflow: "WorkflowService",
        task_runner: "QtTaskRunner",
        initial_file_path: str | None = None,
    ):
        super().__init__()

        self._workflow = workflow
        self._task_runner = task_runner
        self._busy = False
        self.view_mode = "input"

        self.setAcceptDrops(True)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #FFFDF9;
                color: #4A4A48;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            QLabel {
                background-color: transparent;
            }

            QPlainTextEdit {
                background-color: #FFFCF7;
                color: #4A4A48;
                border: 1px dashed #F4B7BF;
                border-radius: 16px;
                padding: 22px;
                selection-background-color: #F6C1C8;
                selection-color: #4A4A48;
            }

            QPushButton, QComboBox, QToolButton {
                background-color: #FFF9F4;
                color: #4A4A48;
                border: 1px solid transparent;
                border-radius: 12px;
                padding: 11px 14px;
            }

            QPushButton:hover, QComboBox:hover, QToolButton:hover {
                background-color: #FFF1F3;
                border-color: #F6C1C8;
            }

            QPushButton:disabled, QComboBox:disabled, QToolButton:disabled {
                color: #9E9E9E;
                background-color: #F7F2EC;
                border-color: #E8DED5;
            }

            QComboBox {
                min-width: 150px;
                min-height: 24px;
            }

            QComboBox#modeCombo {
                background-color: #FFFDF9;
                border-color: #DDECD6;
                padding-left: 14px;
            }

            QToolButton#settingsButton {
                background-color: #D7E8CD;
                border-color: transparent;
                color: #3E4D38;
                padding: 12px 18px;
                font-weight: 600;
            }

            QMenu {
                background-color: #FFF9F4;
                color: #4A4A48;
                border: 1px solid #DDECD6;
                border-radius: 12px;
                padding: 10px;
            }

            QMenu::item {
                padding: 8px 28px 8px 12px;
                border-radius: 6px;
            }

            QMenu::item:selected {
                background-color: #FCECEF;
            }

            QCheckBox {
                spacing: 10px;
                background-color: transparent;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #B7D7A8;
                border-radius: 5px;
                background-color: #FFFDF9;
            }

            QCheckBox::indicator:checked {
                background-color: #B7D7A8;
                border-color: #9FCA8D;
            }

            QFrame#topBar,
            QFrame#leftNav,
            QFrame#rightUtility,
            QFrame#bottomActions {
                background-color: #FFF9F4;
                border: 1px solid transparent;
                border-radius: 18px;
            }

            QFrame#mainContent {
                background-color: #FFF9F4;
                border: 1px solid transparent;
                border-radius: 18px;
            }

            QFrame#editorCard {
                background-color: #FFFCF8;
                border: 1px solid #F7D5DA;
                border-radius: 18px;
            }

            QFrame#viewSegment {
                background-color: #FFFDF9;
                border: 1px solid #E7E1D1;
                border-radius: 12px;
            }

            QFrame#utilityGroup {
                background-color: #FFFCF8;
                border: 1px solid transparent;
                border-radius: 14px;
            }

            QLabel#appTitle {
                color: #2F3430;
                font-size: 18px;
                font-weight: 700;
            }

            QLabel#sectionTitle {
                color: #2F3430;
                font-size: 18px;
                font-weight: 700;
                background-color: transparent;
            }

            QLabel#panelHint {
                color: #8A887D;
                font-size: 12px;
                background-color: transparent;
            }

            QLabel#fieldLabel {
                color: #6D6D6D;
                background-color: transparent;
            }

            QLabel#segmentPill {
                background-color: transparent;
                color: #6D6D6D;
                border: 1px solid transparent;
                border-radius: 10px;
                padding: 9px 16px;
            }

            QLabel#segmentPill[active="true"] {
                background-color: #FFF1F3;
                color: #C54E61;
                border: 1px solid #F6C1C8;
            }

            QFrame#emptyState {
                background-color: transparent;
                border: none;
            }

            QLabel#emptyStateHeading {
                color: #3D3F3B;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#emptyStateText {
                color: #7D7A70;
                font-size: 15px;
            }

            QLabel#emptyStateArt {
                color: #C54E61;
                font-size: 15px;
                font-weight: 700;
            }

            QLabel#emptyStateIcon {
                background-color: #FFF1F3;
                border: 1px solid #F7D5DA;
                border-radius: 20px;
                padding: 18px;
            }

            QPushButton#navButton {
                text-align: left;
                background-color: #FFF9F4;
                border: 1px solid transparent;
                border-radius: 14px;
                padding: 13px 16px;
                color: #53604C;
            }

            QPushButton#navButton:hover,
            QPushButton#navButton[active="true"] {
                background-color: #FBE3E8;
                border-color: transparent;
                color: #3D3F3B;
            }

            QPushButton#primaryAction {
                background-color: #FFF0F2;
                color: #D2475C;
                border-color: #F2AEB8;
                padding: 15px 18px;
                font-size: 16px;
                font-weight: 700;
            }

            QPushButton#primaryAction:hover {
                background-color: #FFE5EA;
                border-color: #EA9AA8;
            }

            QPushButton#secondaryAction {
                background-color: #F7FBF2;
                border-color: transparent;
                color: #4F6A42;
                padding: 14px 16px;
                font-weight: 600;
            }

            QPushButton#secondaryAction:hover {
                background-color: #F4FAEF;
                border-color: #B7D7A8;
            }

            QPushButton#utilityDanger {
                background-color: #FFF4F2;
                border-color: #E9C5BD;
                color: #9D4F42;
                padding: 13px 14px;
            }
        """
        )

        self.setWindowTitle(APP_NAME)
        self.resize(1260, 760)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(16)

        top_bar_frame = QFrame()
        top_bar_frame.setObjectName("topBar")
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(20, 14, 20, 14)
        top_bar.setSpacing(20)

        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(16)

        left_nav_frame = QFrame()
        left_nav_frame.setObjectName("leftNav")
        left_nav_frame.setFixedWidth(174)
        left_nav = QVBoxLayout()
        left_nav.setContentsMargins(14, 24, 14, 24)
        left_nav.setSpacing(14)

        main_content_frame = QFrame()
        main_content_frame.setObjectName("mainContent")
        main_content = QVBoxLayout()
        main_content.setContentsMargins(22, 20, 22, 22)
        main_content.setSpacing(14)

        right_utility_frame = QFrame()
        right_utility_frame.setObjectName("rightUtility")
        right_utility_frame.setFixedWidth(300)
        right_utility = QVBoxLayout()
        right_utility.setContentsMargins(18, 18, 18, 18)
        right_utility.setSpacing(16)

        bottom_actions_frame = QFrame()
        bottom_actions_frame.setObjectName("bottomActions")
        button_row = QHBoxLayout()
        button_row.setContentsMargins(18, 14, 18, 14)
        button_row.setSpacing(16)

        mode_label = QLabel("Structure")
        mode_label.setObjectName("fieldLabel")
        self.mode_combo = QComboBox()
        self.mode_combo.setObjectName("modeCombo")
        for mode, label in self._workflow.structuring_mode_options:
            self.mode_combo.addItem(label, mode)

        default_index = self.mode_combo.findData(self._workflow.default_structuring_mode)
        if default_index >= 0:
            self.mode_combo.setCurrentIndex(default_index)

        self.settings_button = QToolButton()
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setText("Settings")
        self.settings_button.setIcon(self._icon("settings"))
        self.settings_button.setIconSize(QSize(18, 18))
        self.settings_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.settings_button.setPopupMode(QToolButton.InstantPopup)

        self.settings_menu = QMenu(self)
        self.open_editor_before_render_action = QAction(
            "Open editor before generating notes",
            self,
            checkable=True,
        )
        self.open_last_output_action = QAction("Open last notes", self)
        self.open_last_output_action.triggered.connect(self.handle_open_last_output)
        self.open_job_folder_action = QAction("Open saved files", self)
        self.open_job_folder_action.triggered.connect(self.handle_open_job_folder)
        self.delete_all_jobs_action = QAction("Delete saved files", self)
        self.delete_all_jobs_action.triggered.connect(self.handle_delete_all_jobs)

        self.settings_menu.addAction(self.open_editor_before_render_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(self.open_last_output_action)
        self.settings_menu.addAction(self.open_job_folder_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(self.delete_all_jobs_action)
        self.settings_menu.aboutToShow.connect(self.sync_quick_settings_menu)
        self.settings_button.setMenu(self.settings_menu)

        self.view_label = QLabel("Input")
        self.view_label.setObjectName("segmentPill")
        self.editor_view_label = QLabel("Editor")
        self.editor_view_label.setObjectName("segmentPill")
        view_segment = QFrame()
        view_segment.setObjectName("viewSegment")
        view_segment_layout = QHBoxLayout()
        view_segment_layout.setContentsMargins(2, 2, 2, 2)
        view_segment_layout.setSpacing(0)
        view_segment_layout.addWidget(self.view_label)
        view_segment_layout.addWidget(self.editor_view_label)
        view_segment.setLayout(view_segment_layout)

        self.text_input = QPlainTextEdit()
        self.text_input.installEventFilter(self)
        self.text_input.setPlaceholderText(self._input_placeholder_text())
        self.text_input.textChanged.connect(self.update_empty_state)
        self.empty_state = self._build_empty_state()

        self.render_button = QPushButton("Generate Notes")
        self.render_button.setObjectName("primaryAction")
        self.render_button.setIcon(self._icon("generate-notes"))
        self.render_button.setIconSize(QSize(20, 20))
        self.render_button.clicked.connect(self.handle_generate_html)

        self.open_editor_button = QPushButton("Edit Text")
        self.open_editor_button.setObjectName("secondaryAction")
        self.open_editor_button.setIcon(self._icon("edit-text"))
        self.open_editor_button.setIconSize(QSize(20, 20))
        self.open_editor_button.clicked.connect(self.handle_open_editor)

        self.upload_button = QPushButton("Open PDF")
        self.upload_button.setObjectName("secondaryAction")
        self.upload_button.setIcon(self._icon("open-pdf"))
        self.upload_button.setIconSize(QSize(20, 20))
        self.upload_button.clicked.connect(self.handle_pdf_upload)

        self.open_editor_before_render_checkbox = QCheckBox(
            "Open editor before generating notes"
        )
        self.open_editor_before_render_checkbox.toggled.connect(
            self.open_editor_before_render_action.setChecked
        )
        self.open_editor_before_render_action.toggled.connect(
            self.open_editor_before_render_checkbox.setChecked
        )

        self.open_last_output_button = QPushButton("Open last notes")
        self.open_last_output_button.setObjectName("secondaryAction")
        self.open_last_output_button.setIcon(self._icon("saved-notes"))
        self.open_last_output_button.setIconSize(QSize(18, 18))
        self.open_last_output_button.clicked.connect(self.handle_open_last_output)

        self.open_job_folder_button = QPushButton("Open saved files")
        self.open_job_folder_button.setObjectName("secondaryAction")
        self.open_job_folder_button.setIcon(self._icon("files"))
        self.open_job_folder_button.setIconSize(QSize(18, 18))
        self.open_job_folder_button.clicked.connect(self.handle_open_job_folder)

        self.delete_all_jobs_button = QPushButton("Delete saved files")
        self.delete_all_jobs_button.setObjectName("utilityDanger")
        self.delete_all_jobs_button.setIcon(self._icon("cleanup"))
        self.delete_all_jobs_button.setIconSize(QSize(18, 18))
        self.delete_all_jobs_button.clicked.connect(self.handle_delete_all_jobs)

        app_title = QLabel(APP_NAME)
        app_title.setObjectName("appTitle")

        top_bar.addWidget(app_title)
        top_bar.addStretch()
        top_bar.addWidget(mode_label)
        top_bar.addWidget(self.mode_combo)
        top_bar.addSpacing(18)
        view_text_label = QLabel("View")
        view_text_label.setObjectName("fieldLabel")
        top_bar.addWidget(view_text_label)
        top_bar.addWidget(view_segment)
        top_bar.addStretch()
        top_bar.addWidget(self.settings_button)
        top_bar_frame.setLayout(top_bar)

        nav_icons = {
            "Home": "home",
            "Editor": "editor",
            "History": "history",
            "Files": "files",
            "Settings": "settings",
        }
        for index, entry in enumerate(("Home", "Editor", "History", "Files", "Settings")):
            nav_button = QPushButton(entry)
            nav_button.setObjectName("navButton")
            nav_button.setProperty("active", index == 0)
            nav_button.setIcon(self._icon(nav_icons[entry]))
            nav_button.setIconSize(QSize(20, 20))
            left_nav.addWidget(nav_button)
        left_nav.addStretch()
        left_nav_frame.setLayout(left_nav)

        content_title_row = QHBoxLayout()
        content_title_row.setSpacing(14)
        content_title = QLabel("Text")
        content_title.setObjectName("sectionTitle")
        content_hint = QLabel("Paste text or open a PDF to make study notes.")
        content_hint.setObjectName("panelHint")
        content_title_row.addWidget(content_title)
        content_title_row.addWidget(content_hint)
        content_title_row.addStretch()
        main_content.addLayout(content_title_row)
        editor_card = QFrame()
        editor_card.setObjectName("editorCard")
        editor_card_layout = QVBoxLayout()
        editor_card_layout.setContentsMargins(20, 20, 20, 20)
        editor_card_layout.setSpacing(0)
        editor_card_layout.addWidget(self.text_input)
        editor_card.setLayout(editor_card_layout)
        main_content.addWidget(editor_card, 1)
        main_content_frame.setLayout(main_content)

        utility_title = QLabel("Settings")
        utility_title.setObjectName("sectionTitle")
        right_utility.addWidget(utility_title)

        start_group = QFrame()
        start_group.setObjectName("utilityGroup")
        start_group_layout = QVBoxLayout()
        start_group_layout.setContentsMargins(16, 16, 16, 16)
        start_group_layout.setSpacing(12)
        start_group_label = QLabel("Before generating")
        start_group_label.setObjectName("panelHint")
        start_group_layout.addWidget(start_group_label)
        start_group_layout.addWidget(self.open_editor_before_render_checkbox)
        start_group.setLayout(start_group_layout)

        files_group = QFrame()
        files_group.setObjectName("utilityGroup")
        files_group_layout = QVBoxLayout()
        files_group_layout.setContentsMargins(16, 16, 16, 16)
        files_group_layout.setSpacing(12)
        files_group_label = QLabel("Saved notes")
        files_group_label.setObjectName("panelHint")
        files_group_layout.addWidget(files_group_label)
        files_group_layout.addWidget(self.open_last_output_button)
        files_group_layout.addWidget(self.open_job_folder_button)
        files_group.setLayout(files_group_layout)

        danger_group = QFrame()
        danger_group.setObjectName("utilityGroup")
        danger_group_layout = QVBoxLayout()
        danger_group_layout.setContentsMargins(16, 16, 16, 16)
        danger_group_layout.setSpacing(12)
        danger_group_label = QLabel("Cleanup")
        danger_group_label.setObjectName("panelHint")
        danger_group_layout.addWidget(danger_group_label)
        danger_group_layout.addWidget(self.delete_all_jobs_button)
        danger_group.setLayout(danger_group_layout)

        right_utility.addWidget(start_group)
        right_utility.addWidget(files_group)
        right_utility.addWidget(danger_group)
        right_utility.addStretch()
        right_utility_frame.setLayout(right_utility)
        self._add_soft_shadow(start_group, blur_radius=14, y_offset=2, alpha=8)
        self._add_soft_shadow(files_group, blur_radius=14, y_offset=2, alpha=8)
        self._add_soft_shadow(danger_group, blur_radius=14, y_offset=2, alpha=8)

        middle_layout.addWidget(left_nav_frame)
        middle_layout.addWidget(main_content_frame, 1)
        middle_layout.addWidget(right_utility_frame)

        button_row.addWidget(self.render_button, 1)
        button_row.addWidget(self.open_editor_button, 1)
        button_row.addWidget(self.upload_button, 1)
        bottom_actions_frame.setLayout(button_row)

        main_layout.addWidget(top_bar_frame)
        main_layout.addLayout(middle_layout, 1)
        main_layout.addWidget(bottom_actions_frame)

        self.setLayout(main_layout)
        self._add_soft_shadow(top_bar_frame, blur_radius=18, y_offset=3, alpha=10)
        self._add_soft_shadow(left_nav_frame, blur_radius=18, y_offset=4, alpha=10)
        self._add_soft_shadow(main_content_frame, blur_radius=26, y_offset=5, alpha=20)
        self._add_soft_shadow(editor_card, blur_radius=22, y_offset=4, alpha=14)
        self._add_soft_shadow(right_utility_frame, blur_radius=18, y_offset=3, alpha=12)
        self._add_soft_shadow(bottom_actions_frame, blur_radius=18, y_offset=3, alpha=10)
        self.update_view_state()
        self.sync_quick_settings_menu()
        install_shortcuts(self)

        if initial_file_path:
            QTimer.singleShot(0, lambda: self.handle_launch_file(initial_file_path))

    def _input_placeholder_text(self) -> str:
        return ""

    def _icon(self, name: str) -> QIcon:
        return QIcon(str(Path(__file__).with_name("icons") / f"{name}.svg"))

    def _refresh_widget_style(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _add_soft_shadow(
        self,
        widget: QWidget,
        *,
        blur_radius: int,
        y_offset: int,
        alpha: int,
    ) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(0, y_offset)
        shadow.setColor(QColor(112, 91, 72, alpha))
        widget.setGraphicsEffect(shadow)

    def _build_empty_state(self) -> QFrame:
        empty_state = QFrame(self.text_input.viewport())
        empty_state.setObjectName("emptyState")
        empty_state.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(8)
        layout.addStretch()

        icon = QLabel()
        icon.setObjectName("emptyStateIcon")
        icon.setPixmap(self._icon("generate-notes").pixmap(QSize(42, 42)))
        icon.setAlignment(Qt.AlignCenter)

        art = QLabel("Study Notes")
        art.setObjectName("emptyStateArt")
        art.setAlignment(Qt.AlignCenter)

        heading = QLabel("Paste Chinese Text")
        heading.setObjectName("emptyStateHeading")
        heading.setAlignment(Qt.AlignCenter)

        secondary = QLabel("or open a PDF file")
        secondary.setObjectName("emptyStateText")
        secondary.setAlignment(Qt.AlignCenter)

        hint = QLabel("You can also drag and drop a PDF here.")
        hint.setObjectName("emptyStateText")
        hint.setAlignment(Qt.AlignCenter)

        layout.addWidget(icon, alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(art, alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(heading)
        layout.addSpacing(2)
        layout.addWidget(secondary)
        layout.addWidget(hint)
        layout.addStretch()
        empty_state.setLayout(layout)
        return empty_state

    def update_empty_state(self) -> None:
        if not hasattr(self, "empty_state"):
            return

        self.empty_state.setGeometry(self.text_input.viewport().rect())
        should_show = self.view_mode == "input" and not self._text_content().strip()
        self.empty_state.setVisible(should_show)
        if should_show:
            self.empty_state.raise_()

    def _report_error(self, error: Exception) -> None:
        QMessageBox.critical(self, APP_NAME, str(error))
        print("ERROR:", repr(error))

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.render_button.setEnabled(not busy)
        self.open_editor_button.setEnabled(not busy)
        self.upload_button.setEnabled(not busy)
        self.settings_button.setEnabled(not busy)
        self.open_editor_before_render_checkbox.setEnabled(not busy)
        self.delete_all_jobs_button.setEnabled(not busy)
        if busy:
            self.open_last_output_button.setEnabled(False)
            self.open_job_folder_button.setEnabled(False)
        else:
            self.sync_quick_settings_menu()
        self.mode_combo.setEnabled(not busy and self.view_mode != "editor")

    def _run_task(self, fn, on_success) -> None:
        if self._busy:
            return

        self._set_busy(True)

        def handle_success(result) -> None:
            self._set_busy(False)
            on_success(result)

        def handle_error(error: Exception) -> None:
            self._set_busy(False)
            self._report_error(error)

        self._task_runner.submit(fn, handle_success, handle_error)

    def _last_output_path(self) -> Path | None:
        output = self._workflow.session.last_output
        if output is None:
            return None
        return output.output_path

    def _last_job_path(self) -> Path | None:
        output = self._workflow.session.last_output
        if output is None:
            return None
        return output.job_path

    def _current_source_context(self) -> tuple[str, str | None, dict[str, object]]:
        source = self._workflow.session.source
        if source is not None and source.kind != "text":
            return source.kind, source.path, dict(source.metadata)
        return "text", None, {}

    def _current_source_text(self) -> str:
        source = self._workflow.session.source
        if source is not None:
            return source.text
        return self._text_content()

    def update_view_state(self) -> None:
        in_editor = self.view_mode == "editor"
        self.view_label.setProperty("active", not in_editor)
        self.editor_view_label.setProperty("active", in_editor)
        self._refresh_widget_style(self.view_label)
        self._refresh_widget_style(self.editor_view_label)
        self.open_editor_button.setText("Back to Input" if in_editor else "Edit Text")
        self.mode_combo.setEnabled(not in_editor and not self._busy)

        if in_editor:
            self.text_input.setPlaceholderText(
                "Edit the text, then click Generate Notes."
            )
        else:
            self.text_input.setPlaceholderText(self._input_placeholder_text())
        self.update_empty_state()

    def sync_quick_settings_menu(self) -> None:
        output_path = self._last_output_path()
        job_path = self._last_job_path()
        has_output = bool(output_path and output_path.exists())
        has_job_folder = bool(job_path and job_path.exists())
        self.open_last_output_action.setEnabled(has_output)
        self.open_job_folder_action.setEnabled(has_job_folder)
        self.open_last_output_button.setEnabled(has_output and not self._busy)
        self.open_job_folder_button.setEnabled(has_job_folder and not self._busy)

    def _text_content(self) -> str:
        return self.text_input.toPlainText()

    def _selected_structuring_mode(self) -> str:
        return self.mode_combo.currentData() or self._workflow.default_structuring_mode

    def _set_input_view_text(self, text: str) -> None:
        self.view_mode = "input"
        self.text_input.setPlainText(text)
        self.update_view_state()

    def _enter_editor_view(self, editor_text: str) -> None:
        self.view_mode = "editor"
        self.text_input.setPlainText(editor_text)
        self.update_view_state()

    def _return_to_input_view(self) -> None:
        self.view_mode = "input"
        self.text_input.setPlainText(self._current_source_text())
        self.update_view_state()

    def _pdf_path_from_mime_data(self, mime_data) -> str | None:
        if not mime_data or not mime_data.hasUrls():
            return None

        for url in mime_data.urls():
            if not url.isLocalFile():
                continue

            local_path = Path(url.toLocalFile())
            if local_path.suffix.lower() == ".pdf":
                return str(local_path)

        return None

    def _handle_pdf_file(self, file_path: str) -> None:
        mode = self._selected_structuring_mode()
        open_editor_before_render = self.open_editor_before_render_action.isChecked()
        self._run_task(
            lambda: self._workflow.prepare_pdf_for_ui(
                pdf_path=file_path,
                mode=mode,
                open_editor_before_render=open_editor_before_render,
            ),
            self._after_ui_action_ready,
        )

    def _after_ui_action_ready(self, result: "UiActionResult") -> None:
        self._workflow.apply_session(result.session)
        if result.view_mode == "editor":
            self._enter_editor_view(result.display_text)
        else:
            self._set_input_view_text(result.display_text)

        if result.render_result is not None:
            self._after_render_ready(result.render_result)

    def open_local_path(self, path: Path) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def handle_launch_file(self, file_path: str) -> None:
        if self._busy:
            return

        path = Path(file_path).expanduser()
        if not path.exists():
            QMessageBox.warning(
                self,
                APP_NAME,
                f"Could not open file:\n{path}",
            )
            return

        if path.suffix.lower() != ".pdf":
            QMessageBox.warning(
                self,
                APP_NAME,
                f"Mad's Chinese can open PDF files only.\n\nReceived:\n{path}",
            )
            return

        self._handle_pdf_file(str(path.resolve()))

    def eventFilter(self, obj, event):
        if obj is self.text_input and event.type() == QEvent.Resize:
            QTimer.singleShot(0, self.update_empty_state)

        if obj is self.text_input and event.type() in {
            QEvent.DragEnter,
            QEvent.DragMove,
            QEvent.Drop,
        }:
            pdf_path = self._pdf_path_from_mime_data(event.mimeData())
            if pdf_path:
                event.acceptProposedAction()
                if event.type() == QEvent.Drop:
                    self._handle_pdf_file(pdf_path)
                return True

        return super().eventFilter(obj, event)

    def dragEnterEvent(self, event) -> None:
        if self._pdf_path_from_mime_data(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if self._pdf_path_from_mime_data(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        pdf_path = self._pdf_path_from_mime_data(event.mimeData())
        if not pdf_path:
            super().dropEvent(event)
            return

        event.acceptProposedAction()
        self._handle_pdf_file(pdf_path)

    def handle_primary_action(self) -> None:
        if self._busy:
            return

        visible_text = self._text_content()
        if not visible_text.strip():
            QMessageBox.warning(
                self,
                APP_NAME,
                "Paste Chinese text or open a PDF first.",
            )
            return

        structuring_mode = self._selected_structuring_mode()
        source_kind, source_path, metadata = self._current_source_context()
        view_mode = self.view_mode
        open_editor_before_render = self.open_editor_before_render_action.isChecked()
        self._run_task(
            lambda: self._workflow.primary_action_for_ui(
                view_mode=view_mode,
                visible_text=visible_text,
                mode=structuring_mode,
                open_editor_before_render=open_editor_before_render,
                source_kind=source_kind,
                source_path=source_path,
                metadata=metadata,
                persist=True,
            ),
            self._after_ui_action_ready,
        )

    def handle_open_editor(self) -> None:
        if self._busy:
            return

        if self.view_mode == "editor":
            self._return_to_input_view()
            return

        visible_text = self._text_content()
        if not visible_text.strip():
            QMessageBox.warning(
                self,
                APP_NAME,
                "Paste Chinese text or open a PDF first.",
            )
            return

        source_kind, source_path, metadata = self._current_source_context()
        mode = self._selected_structuring_mode()
        self._run_task(
            lambda: self._workflow.open_editor_for_ui(
                text=visible_text,
                mode=mode,
                source_kind=source_kind,
                source_path=source_path,
                metadata=metadata,
            ),
            self._after_ui_action_ready,
        )

    def _after_render_ready(self, result: "RenderResult") -> None:
        self._workflow.apply_session(result.session)
        if result.stored_output is None:
            raise RuntimeError("Render did not produce a stored output")
        self.sync_quick_settings_menu()
        self.open_local_path(result.stored_output.output_path)

    def handle_generate_html(self) -> None:
        if self._busy:
            return

        visible_text = self._text_content()
        if not visible_text.strip():
            QMessageBox.warning(
                self,
                APP_NAME,
                "Paste Chinese text or open a PDF first.",
            )
            return

        structuring_mode = self._selected_structuring_mode()
        source_kind, source_path, metadata = self._current_source_context()
        view_mode = self.view_mode
        self._run_task(
            lambda: self._workflow.render_for_ui(
                view_mode=view_mode,
                visible_text=visible_text,
                mode=structuring_mode,
                source_kind=source_kind,
                source_path=source_path,
                metadata=metadata,
                persist=True,
            ),
            self._after_ui_action_ready,
        )

    def handle_pdf_upload(self) -> None:
        if self._busy:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF",
            "",
            PDF_FILE_FILTER,
        )
        if not file_path:
            return
        self._handle_pdf_file(file_path)

    def handle_open_last_output(self) -> None:
        output_path = self._last_output_path()
        if not output_path or not output_path.exists():
            QMessageBox.information(
                self,
                APP_NAME,
                "Generate notes once before opening the last notes.",
            )
            return

        self.open_local_path(output_path)

    def handle_open_job_folder(self) -> None:
        job_path = self._last_job_path()
        if not job_path or not job_path.exists():
            QMessageBox.information(
                self,
                APP_NAME,
                "Generate notes once before opening saved files.",
            )
            return

        self.open_local_path(job_path)

    def handle_clear_text(self) -> None:
        if self._busy:
            return

        self.view_mode = "input"
        self.text_input.clear()
        self._workflow.clear_active_state()
        self.update_view_state()

    def handle_delete_all_jobs(self) -> None:
        if self._busy:
            return

        result = QMessageBox.question(
            self,
            APP_NAME,
            f"Delete saved files in:\n{self._workflow.jobs_workspace_path}\n\n"
            "This will remove generated notes and saved text from previous runs.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        self._run_task(self._workflow.delete_all_jobs, self._after_jobs_deleted)

    def _after_jobs_deleted(self, result: "DeleteJobsResult") -> None:
        self._workflow.apply_session(result.session)
        self.sync_quick_settings_menu()
        QMessageBox.information(
            self,
            APP_NAME,
            f"Deleted {result.deleted_count} saved folder(s).",
        )


def run_app(initial_file_path: str | None = None):
    from application.workflow import build_default_workflow
    from app.qt_task_runner import QtTaskRunner

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)

    window = MainWindow(
        workflow=build_default_workflow(),
        task_runner=QtTaskRunner(),
        initial_file_path=initial_file_path,
    )
    window.show()
    sys.exit(app.exec())
