from enum import Enum

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect


class ToastType(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Toast(QWidget):
    """
    A toast message that displays a message for a short period of time
    """

    def __init__(self, message, message_type=ToastType):
        super().__init__()
        self.setWindowTitle("Toast")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        font = QFont()
        font.setPointSize(14)
        font.setBold(True)

        styles = {
            ToastType.INFO: "background-color: #1ffc64; color: black;",
            ToastType.WARNING: "background-color: #ffe146; color: black;",
            ToastType.ERROR: "background-color: #e71313; color: white;",
        }
        if message_type not in styles:
            message_type = ToastType.INFO
        self.setStyleSheet(styles[message_type])
        self.label = QLabel(message, self)
        self.label.setContentsMargins(10, 10, 10, 0)
        self.label.setFont(font)
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter
        )
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove layout margins
        self.layout.addWidget(self.label)
        self.adjustSize()

        # Set up opacity effect and animation
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(500)  # 500 milliseconds
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def showEvent(self, event):
        """
        Show the toast message with fade-in effect and auto close after 5 seconds
        """
        self.fade_in()
        QTimer.singleShot(3000, self.fade_out)  # Show for 5 seconds, then fade out

    def fade_in(self):
        """
        Fade in the toast message
        """
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def fade_out(self):
        """
        Fade out the toast message
        """
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.close)  # Close widget after fade out
        self.animation.start()
