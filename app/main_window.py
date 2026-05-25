from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
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
                background-color: white;
                color: black;
            }

            QPlainTextEdit {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                padding: 8px;
            }

            QPushButton, QComboBox, QToolButton {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #aaa;
                padding: 10px 12px;
            }

            QPushButton:hover, QComboBox:hover, QToolButton:hover {
                background-color: #e0e0e0;
            }
        """
        )

        self.setWindowTitle(APP_NAME)
        self.resize(780, 640)

        main_layout = QVBoxLayout()
        top_bar = QHBoxLayout()
        button_row = QHBoxLayout()

        mode_label = QLabel("Structuring Mode")
        self.mode_combo = QComboBox()
        for mode, label in self._workflow.structuring_mode_options:
            self.mode_combo.addItem(label, mode)

        default_index = self.mode_combo.findData(self._workflow.default_structuring_mode)
        if default_index >= 0:
            self.mode_combo.setCurrentIndex(default_index)

        self.settings_button = QToolButton()
        self.settings_button.setText("Options")
        self.settings_button.setPopupMode(QToolButton.InstantPopup)

        self.settings_menu = QMenu(self)
        self.open_editor_before_render_action = QAction(
            "Open editor before render",
            self,
            checkable=True,
        )
        self.open_last_output_action = QAction("Open Last Output", self)
        self.open_last_output_action.triggered.connect(self.handle_open_last_output)
        self.open_job_folder_action = QAction("Open Job Folder", self)
        self.open_job_folder_action.triggered.connect(self.handle_open_job_folder)
        self.delete_all_jobs_action = QAction("Delete All Jobs", self)
        self.delete_all_jobs_action.triggered.connect(self.handle_delete_all_jobs)

        self.settings_menu.addAction(self.open_editor_before_render_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(self.open_last_output_action)
        self.settings_menu.addAction(self.open_job_folder_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(self.delete_all_jobs_action)
        self.settings_menu.aboutToShow.connect(self.sync_quick_settings_menu)
        self.settings_button.setMenu(self.settings_menu)

        self.view_label = QLabel("Input View")
        self.text_input = QPlainTextEdit()
        self.text_input.installEventFilter(self)
        self.text_input.setPlaceholderText(self._input_placeholder_text())

        self.render_button = QPushButton("Render HTML")
        self.render_button.clicked.connect(self.handle_generate_html)

        self.open_editor_button = QPushButton("Open Editor")
        self.open_editor_button.clicked.connect(self.handle_open_editor)

        self.upload_button = QPushButton("Upload PDF")
        self.upload_button.clicked.connect(self.handle_pdf_upload)

        top_bar.addWidget(mode_label)
        top_bar.addWidget(self.mode_combo)
        top_bar.addWidget(self.view_label)
        top_bar.addStretch()
        top_bar.addWidget(self.settings_button)

        button_row.addWidget(self.render_button)
        button_row.addWidget(self.open_editor_button)
        button_row.addWidget(self.upload_button)

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.text_input)
        main_layout.addLayout(button_row)

        self.setLayout(main_layout)
        self.update_view_state()
        install_shortcuts(self)

        if initial_file_path:
            QTimer.singleShot(0, lambda: self.handle_launch_file(initial_file_path))

    def _input_placeholder_text(self) -> str:
        return (
            "Paste Chinese text here, upload a selectable PDF, or drag and drop a PDF.\n"
            "Choose a structuring mode, then click Render HTML for a quick result.\n"
            "If the result looks wrong, click Open Editor, fix the structured text, and render again.\n"
            "Use Options to open the editor before render or reopen the last output/job folder.\n\n"
            "Shortcuts:\n"
            "Ctrl+Enter - Primary action\n"
            "Ctrl+Shift+Enter - Render HTML\n"
            "Ctrl+L - Clear text\n"
            "Ctrl+W - Close app"
        )

    def _report_error(self, error: Exception) -> None:
        QMessageBox.critical(self, APP_NAME, str(error))
        print("ERROR:", repr(error))

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.render_button.setEnabled(not busy)
        self.open_editor_button.setEnabled(not busy)
        self.upload_button.setEnabled(not busy)
        self.settings_button.setEnabled(not busy)
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
        self.view_label.setText("Editor View" if in_editor else "Input View")
        self.open_editor_button.setText("Back to Input" if in_editor else "Open Editor")
        self.mode_combo.setEnabled(not in_editor and not self._busy)

        if in_editor:
            self.text_input.setPlaceholderText(
                "Edit the structured text here, then click Render HTML."
            )
        else:
            self.text_input.setPlaceholderText(self._input_placeholder_text())

    def sync_quick_settings_menu(self) -> None:
        output_path = self._last_output_path()
        job_path = self._last_job_path()
        has_output = bool(output_path and output_path.exists())
        has_job_folder = bool(job_path and job_path.exists())
        self.open_last_output_action.setEnabled(has_output)
        self.open_job_folder_action.setEnabled(has_job_folder)

    def _text_content(self) -> str:
        return self.text_input.toPlainText()

    def _has_text(self) -> bool:
        return bool(self._text_content().strip())

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
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def open_html(self, html_path: str) -> None:
        self.open_local_path(Path(html_path))

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
                f"Mad's Chinese currently supports PDF launch files only.\n\nReceived:\n{path}",
            )
            return

        self._handle_pdf_file(str(path.resolve()))

    def eventFilter(self, obj, event):
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

        if not self._has_text():
            QMessageBox.warning(
                self,
                APP_NAME,
                "Paste some Chinese text or upload a PDF first.",
            )
            return

        structuring_mode = self._selected_structuring_mode()
        source_kind, source_path, metadata = self._current_source_context()
        self._run_task(
            lambda: self._workflow.primary_action_for_ui(
                view_mode=self.view_mode,
                visible_text=self._text_content(),
                mode=structuring_mode,
                open_editor_before_render=self.open_editor_before_render_action.isChecked(),
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

        if not self._has_text():
            QMessageBox.warning(
                self,
                APP_NAME,
                "Paste some Chinese text or upload a PDF first.",
            )
            return

        source_kind, source_path, metadata = self._current_source_context()
        mode = self._selected_structuring_mode()
        self._run_task(
            lambda: self._workflow.open_editor_for_ui(
                text=self._text_content(),
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
        self.open_html(str(result.stored_output.output_path))

    def handle_generate_html(self) -> None:
        if self._busy:
            return

        if not self._has_text():
            QMessageBox.warning(
                self,
                APP_NAME,
                "Paste some Chinese text or upload a PDF first.",
            )
            return

        structuring_mode = self._selected_structuring_mode()
        source_kind, source_path, metadata = self._current_source_context()
        self._run_task(
            lambda: self._workflow.render_for_ui(
                view_mode=self.view_mode,
                visible_text=self._text_content(),
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
            "Select PDF",
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
                "Generate HTML once before opening the last output.",
            )
            return

        self.open_local_path(output_path)

    def handle_open_job_folder(self) -> None:
        job_path = self._last_job_path()
        if not job_path or not job_path.exists():
            QMessageBox.information(
                self,
                APP_NAME,
                "Generate HTML once before opening the job folder.",
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
            f"Delete all job folders in:\n{self._workflow.jobs_workspace_path}\n\n"
            "This will remove all generated HTML, structured text, and metadata for previous runs.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        self._run_task(self._workflow.delete_all_jobs, self._after_jobs_deleted)

    def _after_jobs_deleted(self, result: "DeleteJobsResult") -> None:
        self._workflow.apply_session(result.session)
        QMessageBox.information(
            self,
            APP_NAME,
            f"Deleted {result.deleted_count} job folder(s).",
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
