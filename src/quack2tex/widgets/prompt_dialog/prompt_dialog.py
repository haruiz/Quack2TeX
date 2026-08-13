
from quack2tex.pyqt import (
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QSizePolicy
)
from quack2tex.resources import *  # noqa
from quack2tex.widgets.prompt_input import PromptInput


class PromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("promptDialog")
        self.setWindowTitle("Enter Prompt")
        self.setMinimumSize(680, 460)
        # Multiline text input
        self.prompt_input = PromptInput(parent=self)
        self.prompt_input.setObjectName("promptDialogInput")
        self.prompt_input.setMinimumHeight(300)
        self.prompt_input.setPlaceholderText("Enter your prompt here...")
        self.prompt_input.text_edit.setObjectName("promptDialogTextEdit")
        self.prompt_input.text_edit.setMinimumHeight(300)
        self.prompt_input.btn_enhance_prompt.setFixedSize(52, 52)
        self.prompt_input.btn_enhance_prompt.setIconSize(self.prompt_input.btn_enhance_prompt.iconSize())

        # Button box (OK / Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.setObjectName("promptDialogButtons")
        self.button_box.setCenterButtons(False)
        for button in self.button_box.buttons():
            button.setMinimumSize(128, 44)
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(16)
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
