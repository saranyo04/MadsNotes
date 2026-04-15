import sys
import os
import webbrowser
from app.shortcuts import install_shortcuts

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QMessageBox,
)

from core.pipeline import process_text


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
        self.setWindowTitle("Mad Chinese")
        self.resize(600, 550)

        layout = QVBoxLayout()

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Paste Chinese text here...")
        
        self.process_button = QPushButton("Done")
        self.process_button.clicked.connect(self.handle_process)

        layout.addWidget(self.text_input)
        layout.addWidget(self.process_button)

        self.setLayout(layout)
        
        install_shortcuts(self)

    def handle_process(self):
        try:
            text = self.text_input.toPlainText().strip()

            if not text:
                QMessageBox.warning(self, "Empty Input", "Paste some Chinese text first.")
                return

            html_path = process_text(text)
            full_path = os.path.abspath(html_path)

            opened = webbrowser.open(f"file:///{full_path.replace(os.sep, '/')}")
            if not opened:
                QMessageBox.warning(self, "Browser Error", f"Could not open:\n{full_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            print("ERROR:", repr(e))


def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())