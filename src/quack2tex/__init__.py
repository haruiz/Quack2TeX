import sys

from PySide6.QtWidgets import QApplication

from .windows import MainWindow


def run_app(model_name: str = "models/gemini-1.5-flash-latest") -> None:
    """
    Run the application.
    :return:
    """
    app = QApplication(sys.argv)
    window = MainWindow(model_name)
    window.show()
    sys.exit(app.exec())
