from quack2tex.pyqt import (
    Signal,
    QLineEdit
)

class ClickableLineEdit(QLineEdit):
    """
    A custom QLabel that emits a doubleClicked signal when double clicked
    """

    doubleClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mouseDoubleClickEvent(self, event):
        """
        Emit the doubleClicked signal on double click
        :param event:
        :return:
        """
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)