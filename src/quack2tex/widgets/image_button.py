from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtGui import QColor, QPixmap, QIcon
from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect


class ImageButton(QPushButton):
    """
    A custom QPushButton that emits a doubleClicked signal when double clicked
    """

    doubleClicked = Signal()

    def __init__(self, image_path: str, icon_size: QSize, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0)")
        self.setContentsMargins(0, 0, 0, 0)
        self.image_path = image_path
        self.resize(icon_size)

    def mousePressEvent(self, event):
        """
        Add a drop shadow effect on press
        :param event:
        :return:
        """
        # Call the parent's mousePressEvent
        if self.window() is not None:
            self.window().mousePressEvent(event)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(255, 255, 255))
        shadow.setOffset(5, 5)
        self.setGraphicsEffect(shadow)
        super().mousePressEvent(event)

    def update_icon_size(self):
        """
        Update the icon size to fit the button
        :return:
        """
        new_size = min(self.width(), self.height())  # Maintain aspect ratio
        icon_size = QSize(new_size, new_size)
        self.setIconSize(icon_size)
        pixmap = QPixmap(self.image_path).scaled(
            icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setIcon(QIcon(pixmap))

    def resizeEvent(self, event):
        """
        Update the icon size when the button is resized
        :param event:
        :return:
        """
        self.update_icon_size()
        super().resizeEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Remove the drop shadow effect on release
        :param event:
        :return:
        """
        self.setGraphicsEffect(None)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """
        Emit the doubleClicked signal on double click
        :param event:
        :return:
        """
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
