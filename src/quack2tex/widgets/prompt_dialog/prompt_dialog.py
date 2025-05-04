
from quack2tex.pyqt import (
    QVBoxLayout,
    QDialog,
    QDialogButtonBox
)
from quack2tex.resources import *  # noqa
from quack2tex.widgets.prompt_input import PromptInput


class PromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Prompt")
        # Multiline text input
        self.prompt_input = PromptInput()
        self.prompt_input.setPlaceholderText("Enter your prompt here...")

        # Button box (OK / Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.prompt_input)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_prompt(self):
        return self.prompt_input.toPlainText().strip()

    def setPlaceholderText(self, text: str):
        """
        Set the placeholder text for the prompt input.
        :param text:
        :return:
        """
        self.prompt_input.setPlaceholderText(text)


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    from dotenv import load_dotenv
    load_dotenv()


    app = QApplication(sys.argv)
    dialog = PromptDialog()
    dialog.show()
    sys.exit(app.exec())