from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtWidgets import QMainWindow, QLabel, QStyleFactory, QToolBox

from quack2tex.widgets import MarkdownViewer


class PredictionsWindow(QMainWindow):
    """
    A window to display the predictions output
    """
    def __init__(self, predictions: dict, parent=None):
        super().__init__(parent)

        # Set window properties
        self.setWindowTitle("Matrix Theme Window")
        self.setGeometry(100, 100, 800, 600)
        toolbox = QToolBox()
        for model, prediction in predictions.items():
            viewer = MarkdownViewer()
            viewer.set_content(prediction)
            toolbox.addItem(viewer, model)

        self.setCentralWidget(toolbox)

