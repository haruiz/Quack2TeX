from PySide6.QtWidgets import QToolBox, QDialog, QVBoxLayout

from quack2tex.widgets import MarkdownViewer


class OutputDialog(QDialog):
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

        self.layout = QVBoxLayout()
        self.layout.addWidget(toolbox)
        self.setLayout(self.layout)

