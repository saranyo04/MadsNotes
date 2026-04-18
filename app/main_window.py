import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QUrl
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
from core.document_editor import document_to_editor_text, editor_text_to_document
from core.pipeline import process_text, read_pdf_text, render_document
from core.text_structurer import DEFAULT_STRUCTURING_MODE, STRUCTURING_MODE_OPTIONS


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.view_mode = "input"
        self.current_source_kind = "text"
        self.current_source_path: str | None = None
        self.current_source_text = ""
        self.raw_input_cache = ""
        self.last_output_path: Path | None = None

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

        self.setWindowTitle("Chinese OCR Cleaner")
        self.resize(780, 640)

        main_layout = QVBoxLayout()
        top_bar = QHBoxLayout()
        button_row = QHBoxLayout()

        mode_label = QLabel("Structuring Mode")

        self.mode_combo = QComboBox()
        for mode, label in STRUCTURING_MODE_OPTIONS:
            self.mode_combo.addItem(label, mode)

        default_index = self.mode_combo.findData(DEFAULT_STRUCTURING_MODE)
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

        self.settings_menu.addAction(self.open_editor_before_render_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(self.open_last_output_action)
        self.settings_menu.addAction(self.open_job_folder_action)
        self.settings_menu.aboutToShow.connect(self.sync_quick_settings_menu)
        self.settings_button.setMenu(self.settings_menu)

        self.view_label = QLabel("Input View")

        self.text_input = QPlainTextEdit()
        self.text_input.installEventFilter(self)
        self.text_input.setPlaceholderText(
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

    def update_view_state(self) -> None:
        in_editor = self.view_mode == "editor"

        self.view_label.setText("Editor View" if in_editor else "Input View")
        self.open_editor_button.setText("Back to Input" if in_editor else "Open Editor")
        self.mode_combo.setEnabled(not in_editor)

        if in_editor:
            self.text_input.setPlaceholderText(
                "Edit the structured text here, then click Render HTML."
            )
        else:
            self.text_input.setPlaceholderText(
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

    def sync_quick_settings_menu(self) -> None:
        has_output = bool(
            self.last_output_path
            and self.last_output_path.exists()
        )
        has_job_folder = bool(
            has_output
            and self.last_output_path is not None
            and self.last_output_path.parent.parent.exists()
        )

        self.open_last_output_action.setEnabled(has_output)
        self.open_job_folder_action.setEnabled(has_job_folder)

    def _text_content(self) -> str:
        return self.text_input.toPlainText()

    def _has_text(self) -> bool:
        return bool(self._text_content().strip())

    def _selected_structuring_mode(self) -> str:
        return self.mode_combo.currentData() or DEFAULT_STRUCTURING_MODE

    def _remember_text_source(self, text: str) -> None:
        self.current_source_kind = "text"
        self.current_source_path = None
        self.current_source_text = text
        self.raw_input_cache = text

    def _remember_pdf_source(self, pdf_path: str, text: str) -> None:
        self.current_source_kind = "pdf"
        self.current_source_path = pdf_path
        self.current_source_text = text
        self.raw_input_cache = text

    def _remember_current_input_source(self, text: str) -> None:
        if self.current_source_kind == "pdf" and self.current_source_path:
            self.current_source_text = text
            self.raw_input_cache = text
            return

        self._remember_text_source(text)

    def _set_input_view_text(self, text: str) -> None:
        self.view_mode = "input"
        self.raw_input_cache = text
        self.text_input.setPlainText(text)
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
        source_text = read_pdf_text(file_path)
        self._remember_pdf_source(file_path, source_text)
        self._set_input_view_text(source_text)

        if self.open_editor_before_render_action.isChecked():
            document = process_text(
                source_text,
                mode=self._selected_structuring_mode(),
            )
            self._enter_editor_view(document, source_text)
            return

        self.handle_generate_html()

    def _enter_editor_view(self, document: dict, source_text: str) -> None:
        self.view_mode = "editor"
        self.current_source_text = source_text
        self.raw_input_cache = source_text
        self.text_input.setPlainText(document_to_editor_text(document))
        self.update_view_state()

    def _return_to_input_view(self) -> None:
        self.view_mode = "input"
        self.text_input.setPlainText(self.raw_input_cache)
        self.update_view_state()

    def open_local_path(self, path: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def open_html(self, html_path: str) -> None:
        self.open_local_path(Path(html_path))

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
                    try:
                        self._handle_pdf_file(pdf_path)
                    except Exception as error:
                        QMessageBox.critical(self, "Error", str(error))
                        print("ERROR:", repr(error))
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

        try:
            self._handle_pdf_file(pdf_path)
        except Exception as error:
            QMessageBox.critical(self, "Error", str(error))
            print("ERROR:", repr(error))

    def handle_primary_action(self) -> None:
        if self.view_mode == "editor":
            self.handle_generate_html()
            return

        if self.open_editor_before_render_action.isChecked():
            self.handle_open_editor()
            return

        self.handle_generate_html()

    def handle_open_editor(self) -> None:
        try:
            if self.view_mode == "editor":
                self._return_to_input_view()
                return

            if not self._has_text():
                QMessageBox.warning(
                    self,
                    "Empty Input",
                    "Paste some Chinese text or upload a PDF first.",
                )
                return

            source_text = self._text_content()
            self._remember_current_input_source(source_text)

            document = process_text(
                source_text,
                mode=self._selected_structuring_mode(),
            )
            self._enter_editor_view(document, source_text)

        except Exception as error:
            QMessageBox.critical(self, "Error", str(error))
            print("ERROR:", repr(error))

    def handle_generate_html(self) -> None:
        try:
            if not self._has_text():
                QMessageBox.warning(
                    self,
                    "Empty Input",
                    "Paste some Chinese text or upload a PDF first.",
                )
                return

            if self.view_mode == "editor":
                editor_text = self._text_content()
                document = editor_text_to_document(editor_text)
                html_path = render_document(
                    document,
                    editor_text=editor_text,
                    source_text=self.current_source_text,
                    source_kind=self.current_source_kind,
                    source_path=self.current_source_path,
                    structuring_mode="editor",
                    used_editor=True,
                )
            else:
                source_text = self._text_content()
                self._remember_current_input_source(source_text)
                structuring_mode = self._selected_structuring_mode()
                document = process_text(source_text, mode=structuring_mode)
                html_path = render_document(
                    document,
                    source_text=source_text,
                    source_kind=self.current_source_kind,
                    source_path=self.current_source_path,
                    structuring_mode=structuring_mode,
                    used_editor=False,
                )

            self.last_output_path = Path(html_path).resolve()
            self.open_html(html_path)

        except Exception as error:
            QMessageBox.critical(self, "Error", str(error))
            print("ERROR:", repr(error))

    def handle_pdf_upload(self) -> None:
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select PDF",
                "",
                "PDF Files (*.pdf)",
            )

            if not file_path:
                return

            self._handle_pdf_file(file_path)

        except Exception as error:
            QMessageBox.critical(self, "Error", str(error))
            print("ERROR:", repr(error))

    def handle_open_last_output(self) -> None:
        if not self.last_output_path or not self.last_output_path.exists():
            QMessageBox.information(
                self,
                "No Output",
                "Generate HTML once before opening the last output.",
            )
            return

        self.open_local_path(self.last_output_path)

    def handle_open_job_folder(self) -> None:
        if (
            not self.last_output_path
            or not self.last_output_path.exists()
            or not self.last_output_path.parent.parent.exists()
        ):
            QMessageBox.information(
                self,
                "No Job Folder",
                "Generate HTML once before opening the job folder.",
            )
            return

        self.open_local_path(self.last_output_path.parent.parent)

    def handle_clear_text(self) -> None:
        self.view_mode = "input"
        self.current_source_kind = "text"
        self.current_source_path = None
        self.current_source_text = ""
        self.raw_input_cache = ""
        self.text_input.clear()
        self.update_view_state()


def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
