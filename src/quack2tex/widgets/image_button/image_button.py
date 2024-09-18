from PySide6 import QtCore
from PySide6.QtCore import Signal, QSize, QTimer
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QGraphicsOpacityEffect, QPushButton, QGraphicsDropShadowEffect


class ImageButton(QPushButton):
    """
    A custom QPushButton that emits a doubleClicked signal when double clicked
    """

    doubleClicked = Signal()

    def __init__(self, image_path: str, icon_size: QSize, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;  /* Transparent background */
                border: none;                    /* Remove border */
                padding: 10px;
                color: black;                    /* Set text color */
            }
            
            QPushButton:pressed {
                background-color: transparent;  /* Transparent when pressed */
            }
        
            QPushButton:hover {
                background-color: transparent;  /* Transparent on hover */
            }
        """)
        self.setContentsMargins(0, 0, 0, 0)
        self.image_path = image_path
        self.setIconSize(icon_size)
        self.setIcon(QIcon(image_path))
        #self.setFlat(True)
        self.setFixedSize(icon_size)

    def sizeHint(self):
        """
        Return the size hint
        :return: QSize object with the size hint
        """
        return self.iconSize()


    def mouseDoubleClickEvent(self, event):
        """
        Emit the doubleClicked signal on double click
        :param event:
        :return:
        """
        self.doubleClicked.emit()
