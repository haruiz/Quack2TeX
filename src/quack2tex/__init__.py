import os
import sys
import openai
import google.generativeai as genai
from PySide6.QtWidgets import QApplication

from .windows import MainWindow


def run_app(model_name: str = "models/gemini-1.5-flash-latest") -> None:
    """
    Run the application.
    :return:
    """
    if "OPENAI_API_KEY" in os.environ:
        openai.api_key = os.getenv("OPENAI_API_KEY")
    if "GOOGLE_API_KEY" in os.environ:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    app = QApplication(sys.argv)
    window = MainWindow(model_name)
    window.show()
    sys.exit(app.exec())
