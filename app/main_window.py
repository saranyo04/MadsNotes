import sys
import os
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
)

from app.shortcuts import install_shortcuts
from core.pipeline import process_text, process_pdf


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
            }

            QTextEdit {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
            }

            QPushButton {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #aaa;
                padding: 15px;
            }

            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        self.setWindowTitle("Chinese OCR Cleaner")
        self.resize(600, 550)

        layout = QVBoxLayout()

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Paste Chinese text here...")

        self.process_button = QPushButton("Process Text")
        self.process_button.clicked.connect(self.handle_process)

        self.upload_button = QPushButton("Upload PDF")
        self.upload_button.clicked.connect(self.handle_pdf_upload)

        layout.addWidget(self.text_input)
        layout.addWidget(self.process_button)
        layout.addWidget(self.upload_button)

        self.setLayout(layout)

        install_shortcuts(self)

    def open_html(self, html_path):
        full_path = Path(html_path).resolve()
        webbrowser.open(full_path.as_uri())

    def handle_process(self):
        try:
            text = self.text_input.toPlainText().strip()

            if not text:
                QMessageBox.warning(self, "Empty Input", "Paste some Chinese text first.")
                return

            html_path = process_text(text)
            self.open_html(html_path)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            print("ERROR:", repr(e))

    def handle_pdf_upload(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select PDF",
                "",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            html_path = process_pdf(file_path)
            self.open_html(html_path)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            print("ERROR:", repr(e))


def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())