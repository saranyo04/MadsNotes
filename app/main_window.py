from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QSize, QTimer, Qt
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QGraphicsDropShadowEffect,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.settings_window import SettingsWindow
from app.shortcuts import install_shortcuts
from app.theme_system import (
    DEFAULT_THEME_NAME,
    get_theme,
    load_themes,
    theme_stylesheet,
)
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
        self._themes = load_themes()
        self._settings_window: SettingsWindow | None = None

        self.setAcceptDrops(True)
        self._theme = get_theme(DEFAULT_THEME_NAME)
        self.setStyleSheet(theme_stylesheet(self._theme))
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

        self.open_editor_before_render_action = QAction(
            "Open editor before generating notes",
            self,
            checkable=True,
        )

        self.view_label = QPushButton("Input")
        self.view_label.setObjectName("segmentPill")
        self.view_label.clicked.connect(self.handle_select_input_view)
        self.editor_view_label = QPushButton("Editor")
        self.editor_view_label.setObjectName("segmentPill")
        self.editor_view_label.clicked.connect(self.handle_select_editor_view)
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

        self.upload_button = QPushButton("Upload PDF")
        self.upload_button.setObjectName("secondaryAction")
        self.upload_button.setIcon(self._icon("open-pdf"))
        self.upload_button.setIconSize(QSize(20, 20))
        self.upload_button.clicked.connect(self.handle_pdf_upload)

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
        top_bar_frame.setLayout(top_bar)

        nav_icons = {
            "Home": "home",
            "History": "history",
            "Files": "files",
            "Settings": "settings",
        }
        for index, entry in enumerate(("Home", "History", "Files", "Settings")):
            nav_button = QPushButton(entry)
            nav_button.setObjectName("navButton")
            nav_button.setProperty("active", index == 0)
            nav_button.setIcon(self._icon(nav_icons[entry]))
            nav_button.setIconSize(QSize(20, 20))
            if entry == "Settings":
                self.settings_nav_button = nav_button
                nav_button.clicked.connect(self.handle_open_settings)
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

        utility_title = QLabel("Saved Notes")
        utility_title.setObjectName("sectionTitle")
        right_utility.addWidget(utility_title)

        files_group = QFrame()
        files_group.setObjectName("utilityGroup")
        files_group_layout = QVBoxLayout()
        files_group_layout.setContentsMargins(16, 16, 16, 16)
        files_group_layout.setSpacing(12)
        files_group_label = QLabel("Open your latest generated notes or saved files.")
        files_group_label.setObjectName("panelHint")
        files_group_layout.addWidget(files_group_label)
        files_group_layout.addWidget(self.open_last_output_button)
        files_group_layout.addWidget(self.open_job_folder_button)
        files_group.setLayout(files_group_layout)

        right_utility.addWidget(files_group)
        right_utility.addStretch()
        right_utility_frame.setLayout(right_utility)
        self._add_soft_shadow(files_group, blur_radius=14, y_offset=2, alpha=8)

        middle_layout.addWidget(left_nav_frame)
        middle_layout.addWidget(main_content_frame, 1)
        middle_layout.addWidget(right_utility_frame)

        button_row.addWidget(self.upload_button, 1)
        button_row.addWidget(self.render_button, 1)
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
        self.sync_saved_notes_actions()
        install_shortcuts(self)

        if initial_file_path:
            QTimer.singleShot(0, lambda: self.handle_launch_file(initial_file_path))

    def _input_placeholder_text(self) -> str:
        return ""

    def _icon(self, name: str) -> QIcon:
        return QIcon(str(Path(__file__).with_name("icons") / f"{name}.svg"))

    def handle_theme_changed(self, theme_name: str) -> None:
        self._theme = self._themes.get(theme_name) or get_theme()
        self.setStyleSheet(theme_stylesheet(self._theme))
        if self._settings_window is not None:
            self._settings_window.setStyleSheet(self.styleSheet())
            self._settings_window.set_current_theme(self._theme.name)
        self.update_view_state()

    def handle_open_settings(self) -> None:
        if self._settings_window is None:
            self._settings_window = SettingsWindow(
                themes=self._themes,
                current_theme_name=self._theme.name,
                open_editor_before_render_action=self.open_editor_before_render_action,
                on_theme_changed=self.handle_theme_changed,
                on_delete_saved_files=self.handle_delete_all_jobs,
                parent=self,
            )
            self._settings_window.setStyleSheet(self.styleSheet())
            self._settings_window.set_busy(self._busy)

        self._settings_window.show()
        self._settings_window.raise_()
        self._settings_window.activateWindow()

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
        self.upload_button.setEnabled(not busy)
        self.view_label.setEnabled(not busy)
        self.editor_view_label.setEnabled(not busy)
        if self._settings_window is not None:
            self._settings_window.set_busy(busy)
        if busy:
            self.open_last_output_button.setEnabled(False)
            self.open_job_folder_button.setEnabled(False)
        else:
            self.sync_saved_notes_actions()
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
        self.mode_combo.setEnabled(not in_editor and not self._busy)

        if in_editor:
            self.text_input.setPlaceholderText(
                "Edit the text, then click Generate Notes."
            )
        else:
            self.text_input.setPlaceholderText(self._input_placeholder_text())
        self.update_empty_state()

    def sync_saved_notes_actions(self) -> None:
        output_path = self._last_output_path()
        job_path = self._last_job_path()
        has_output = bool(output_path and output_path.exists())
        has_job_folder = bool(job_path and job_path.exists())
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

    def handle_select_input_view(self) -> None:
        if self._busy or self.view_mode != "editor":
            return
        self._return_to_input_view()

    def handle_select_editor_view(self) -> None:
        if self._busy or self.view_mode == "editor":
            return
        self.handle_open_editor()

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
        self.sync_saved_notes_actions()
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
        self.sync_saved_notes_actions()
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
