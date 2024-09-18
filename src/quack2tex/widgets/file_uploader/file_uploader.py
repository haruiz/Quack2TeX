from importlib.metadata import files

from PySide6.QtCore import Property
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget, QPushButton
from quack2tex.widgets import ClickableLineEdit


class FileUploader(QWidget):
    """
    A custom widget that allows the user to upload a file
    """

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)

        # Create a horizontal layout for the uploader widget
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Create the text field to display the file path
        self.file_path_edit = ClickableLineEdit(self)
        self.file_path_edit.setFixedHeight(30)
        self.file_path_edit.doubleClicked.connect(self.open_file_dialog)
        self.file_path_edit.setPlaceholderText("No file selected")

        # Create the upload button
        self.upload_button = QPushButton("Browse...", self)
        self.upload_button.clicked.connect(self.open_file_dialog)

        # Add the text field and button to the layout
        self.layout.addWidget(self.file_path_edit)
        self.layout.addWidget(self.upload_button)

        # Set the layout on this custom widget
        self.setLayout(self.layout)
        self.file_path_edit.setReadOnly(True)

        # Set the file filter
        file_filter = kwargs.get("file_filter", None)
        self.file_filter = file_filter or "All Files (*)"


    def get_file_path(self):
        """
        Get the file path
        :return: the file path
        """
        return self.file_path_edit.text()


    def set_file_path(self, file_path):
        """
        Set the file path
        :param file_path:
        :return:
        """
        self.file_path_edit.setText(file_path)

    file_path = Property(str, get_file_path, set_file_path)


    def open_file_dialog(self):
        """
        Open a file dialog to select a file
        :return:
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", self.file_filter)
        if file_path:
            self.file_path_edit.setText(file_path)

    def mouseDoubleClickEvent(self, event):
        """
        Triggered when the user double-clicks the widget
        :param event:
        :return:
        """
        self.open_file_dialog()
        super().mouseDoubleClickEvent(event)