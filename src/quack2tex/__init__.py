import sys

from PySide6 import QtGui
from PySide6.QtCore import Qt, QFile
from PySide6.QtGui import QPalette, QColor, QIcon, QCursor
from PySide6.QtWidgets import QApplication, QStyleFactory
from .llm import LLM
from .utils import GuiUtils
from .windows import MainWindow
from pydantic import BaseModel
import inspect
import typing
from .resources import resources_rc  # noqa: F401



class Quack2TexWrappedFunctionResult(BaseModel):
      result: typing.Any
      latex: str 

def apply_theme(app: QApplication) -> None:
    """
    Apply the theme to the application
    :param app:
    :return:
    """
    app.setStyle("Fusion")
    QtGui.QFontDatabase.addApplicationFont(":/fonts/Roboto/Roboto-Regular.ttf")
    app.setWindowIcon(QIcon(":icons/rubber-duck.png"))
    file = QFile(":/styles/style.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    style_sheet = file.readAll().data().decode("utf-8")
    app.setStyleSheet(style_sheet)
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    QApplication.setPalette(palette)


# create quack2tex decorator
def latify(model: str = None):
    """
    Decorator to convert a function to LaTeX using the LLM model
    :param kwargs:
    :return:
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            llm = LLM.create(model or "models/gemini-1.5-flash-latest")
            func_code = inspect.getsource(func)
            prompt = kwargs.get("prompt", "Generate a LaTeX representation of the following function in markdown format:")
            response = llm.ask(prompt + "\n\n" + func_code)
            result = func(*args, **kwargs)
            return Quack2TexWrappedFunctionResult(result=result, latex=response)
        return wrapper
    return decorator

def run_app() -> None:
    """
    Run the application.
    :return:
    """

    app = QApplication(sys.argv)
    apply_theme(app)
    app.setOverrideCursor(QCursor(Qt.PointingHandCursor))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
