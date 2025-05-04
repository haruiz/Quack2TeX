import sys
from typing import Optional

from quack2tex.pyqt import (
    Signal, QTabWidget,
    QWidget, QApplication,
    QVBoxLayout, QDialog
)
from quack2tex.resources import *  # noqa
from quack2tex.windows.setting_window.menu_manager import MenuManager
from quack2tex.windows.setting_window.prompt_browser import PromptBrowser


class SettingsWindow(QDialog):
    """
    Main application window.
    """
    on_settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(800, 600)
        self.setWindowTitle("Settings")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.menu_manager = MenuManager()
        self.menu_manager.on_menu_options_changed.connect(self.on_settings_changed)

        self.prompt_browser = PromptBrowser(self)
        self.tabs.addTab(self.menu_manager, "Menu Manager")
        self.tabs.addTab(self.prompt_browser, "Prompts Browser")


if __name__ == '__main__':
    from quack2tex.repository.db.sync_session import  init_db
    app = QApplication(sys.argv)
    init_db()
    win = SettingsWindow()
    win.show()
    sys.exit(app.exec())