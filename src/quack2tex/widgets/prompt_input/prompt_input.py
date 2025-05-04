from PyQt6.QtCore import QSize
from jinja2 import Template
from modihub.llm import LLM

from quack2tex.pyqt import (
    QVBoxLayout,
    QTextEdit,
    QWidget,
    QMenu,
    QAction,
    QIcon,
    Qt,
    QCursor,
    QThreadPool,
    QPushButton,
    Property
)
from quack2tex.resources import *  # noqa
from quack2tex.utils import Worker
from string import Template

default_prompt_template = Template("""
Please enhance the following prompt to make it more effective and precise 
for AI interpretation. Ensure clarity, specificity, and include any necessary 
context or constraints to guide the AI towards the desired output.
Original Prompt:
{prompt}
Instructions:
- Clarify ambiguous terms or phrases.
- Specify the desired format or structure of the response.
- Include relevant context or background information.
- Define the intended audience or purpose, if applicable.
- Set any constraints such as length, tone, or style.

Enhanced Prompt:
Return it in plain text format without any additional explanation.
""")

class PromptInput(QWidget):
    def __init__(self, prompt_template: Template = default_prompt_template, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Prompt")

        self.prompt_template = prompt_template

        # Multiline text input
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("Enter your prompt here...")

        self.btn_enhance_prompt = QPushButton()
        self.btn_enhance_prompt.setEnabled(False)
        self.btn_enhance_prompt.setToolTip("Enhance Prompt")
        self.btn_enhance_prompt.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_enhance_prompt.setIcon(QIcon(":/icons/ai.png"))
        self.btn_enhance_prompt.setIconSize(QSize(32, 32))


        self.model_picker: QMenu = QMenu()
        self.model_picker.triggered.connect(lambda action: self.enhance_prompt(action.text()))
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.btn_enhance_prompt, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)

        self.threadpool = QThreadPool()
        self.populate_model_picker()

    def populate_model_picker(self):
        """
        Load models into the menu.
        :return:
        """
        worker = Worker(self.do_load_models)
        worker.signals.result.connect(self.done_load_models)
        worker.signals.finished.connect(lambda: print("Finished loading models"))
        worker.signals.error.connect(lambda ex: print(f"Error loading models: {ex}"))
        self.threadpool.start(worker)


    def do_load_models(self):
        return list(LLM.available_models().group_by("client"))

    def done_load_models(self, available_models):
        """
        Load models into the menu.
        :return:
        """
        self.model_picker.clear()
        for client, models in available_models:
            client_menu = QMenu(client, self.model_picker)
            for model in models:
                action = QAction(model.name, self.model_picker)
                client_menu.addAction(action)
            self.model_picker.addMenu(client_menu)
        self.btn_enhance_prompt.setEnabled(True)
        self.btn_enhance_prompt.setMenu(self.model_picker)

    def enhance_prompt(self, model_name: str):
        """
        Enhance the prompt using the selected model.
        :param model_name:
        :return:
        """
        prompt = self.text_edit.toPlainText().strip()
        if not prompt:
            return
        self.btn_enhance_prompt.setEnabled(False)
        worker = Worker(self.do_enhance_prompt, model_name, prompt)
        worker.signals.result.connect(self.done_enhance_prompt)
        worker.signals.error.connect(self.error_enhance_prompt)
        self.threadpool.start(worker)

    def do_enhance_prompt(self, model_name: str, prompt: str):
        """
        Enhance the prompt using the selected model.
        :param model_name:
        :param prompt:
        :return:
        """
        system_instruction = self.prompt_template.safe_substitute(prompt=prompt)
        llm = LLM.create(model_name, system_instruction=system_instruction)
        return llm(prompt)

    def done_enhance_prompt(self, enhanced_prompt: str):
        """
        Set the enhanced prompt in the text edit widget.
        :param enhanced_prompt:
        :return:
        """
        self.text_edit.setPlainText(enhanced_prompt.strip())
        self.btn_enhance_prompt.setEnabled(True)

    def error_enhance_prompt(self, ex: Exception):
        """
        Handle errors during the enhancement process.
        :param ex:
        :return:
        """
        print(f"Error enhancing prompt: {ex}")
        self.btn_enhance_prompt.setEnabled(True)

    def toPlainText(self) -> str:
        """
        Get the plain text from the text edit widget.
        :return:
        """
        return self.text_edit.toPlainText().strip()

    def setPlainText(self, value: str):
        """
        Set the plain text in the text edit widget.
        :param value:
        :return:
        """
        self.text_edit.setPlainText(value)

    def setPlaceholderText(self, text: str):
        """
        Set the placeholder text for the prompt input.
        :param text:
        :return:
        """
        self.text_edit.setPlaceholderText(text)

    def clear(self):
        """
        Clear the text edit widget.
        :return:
        """
        self.text_edit.clear()

    plainText = Property(str, toPlainText, setPlainText)
