import inspect
import sys
import typing

from pydantic import BaseModel

from quack2tex.pyqt import (
    QApplication, Qt, QIcon, QFile, QPalette, QColor, QCursor, QFontDatabase,QIODevice
)
from modihub.llm import LLM
from .resources import * # noqa
from .utils import GuiUtils
from .windows import MainWindow
from quack2tex.repository.db.sync_session import init_db

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
    QFontDatabase.addApplicationFont(":/fonts/Roboto/Roboto-Regular.ttf")
    app.setWindowIcon(QIcon(":icons/rubber-duck.png"))
    file = QFile(":/styles/style.qss")
    file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text)
    style_sheet = file.readAll().data().decode("utf-8")
    app.setStyleSheet(style_sheet)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("white"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("white"))
    palette.setColor(QPalette.ColorRole.Text, QColor("white"))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("white"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("red"))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("black"))
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
            response = llm(prompt + "\n\n" + func_code)
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
    # apply_theme(app)
    init_db()
    app.setOverrideCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
