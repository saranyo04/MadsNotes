from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtGui import QKeySequence, QShortcut


def install_shortcuts(window):
    if hasattr(window, "_shortcuts"):
        return
    
    window._shortcuts = []

    def add_shortcut(sequence, callback):
        shortcut = QShortcut(QKeySequence(sequence), window)
        shortcut.setContext(Qt.WindowShortcut)
        shortcut.activated.connect(callback)
        window._shortcuts.append(shortcut)

    add_shortcut("Ctrl+Return", window.handle_primary_action)

    if hasattr(window, "handle_generate_html"):
        add_shortcut("Ctrl+Shift+Return", window.handle_generate_html)
    if hasattr(window, "handle_save_note"):
        add_shortcut("Ctrl+S", window.handle_save_note)
    clear_action = getattr(window, "handle_clear_text", window.text_input.clear)
    add_shortcut("Ctrl+L", clear_action)
    add_shortcut("Ctrl+W", window.close)

    window._easter_eggs = EasterEggHandler(window, window.text_input)


class EasterEggHandler(QObject):
    def __init__(self, window, target_widget):
        super().__init__(window)
        self.window = window
        self.target_widget = target_widget
        self.buffer = ""
        self.easter_map = self.register_easter_eggs()
        self._label = None
        self._fade_anim = None
        target_widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.target_widget and event.type() == QEvent.KeyPress:
            text = event.text()
            if text and text.isprintable():
                self.buffer = (self.buffer + text.lower())[-10:]
                for key, action in self.easter_map.items():
                    if key in self.buffer:
                        self.buffer = ""
                        action()
                        break
        return super().eventFilter(obj, event)
    def register_easter_eggs(self):
        return {
            "rio": lambda: self.show_message("我爱你 答胡雅"),
            "madhurjya": lambda: self.show_message("Hiya, I love you!"),
        }
        
    def show_message(self, text):
        import random

        from PySide6.QtCore import Qt, QPropertyAnimation
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel

        label = QLabel(text, self.window)
        label.setAttribute(Qt.WA_TransparentForMouseEvents)

        label.setStyleSheet("""
            QLabel {
                color: #c00000;
                background: rgba(255, 255, 255, 220);
                border: 1px solid #d9d9d9;
                border-radius: 10px;
                padding: 10px 14px;
            }
        """)

        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        label.setFont(font)

        label.adjustSize()
        
        x = self.window.width() - label.width() - 20
        y = self.window.height() - label.height() - 20

        x += random.randint(-10, 10) 
        y += random.randint(-10, 10)
        
        label.move(x, y)
        label.show()

        # Opacity effect (correct way)
        effect = QGraphicsOpacityEffect(label)
        label.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", label)
        anim.setDuration(2000)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)

        anim.finished.connect(label.deleteLater)
        anim.start()
