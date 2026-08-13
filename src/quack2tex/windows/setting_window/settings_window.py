import sys
from typing import Optional

from quack2tex.pyqt import (
    Signal, QTabWidget,
    QWidget, QApplication,
    QVBoxLayout, QDialog,Qt
)
from quack2tex.resources import *  # noqa
from quack2tex.windows.setting_window.menu_manager import MenuManager
from quack2tex.windows.setting_window.preferences_panel import PreferencesPanel
from quack2tex.windows.setting_window.prompt_browser import PromptBrowser


class SettingsWindow(QDialog):
    """
    Main application window.
    """
    on_settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("settingsWindow")
        self.setModal(True)
        self.setMinimumSize(1180, 780)
        self.resize(1280, 840)
        self.setWindowTitle("Settings")
        self.setWindowFlag(Qt.WindowType.Window)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("settingsTabs")
        self.layout.addWidget(self.tabs)

        self.menu_manager = MenuManager()
        self.menu_manager.on_menu_options_changed.connect(self.on_settings_changed)

        self.prompt_browser = PromptBrowser(self)
        self.preferences_panel = PreferencesPanel(self)
        self.preferences_panel.on_preferences_changed.connect(self.on_settings_changed)
        self.tabs.addTab(self.menu_manager, "Menu Manager")
        self.tabs.addTab(self.prompt_browser, "Prompts Browser")
        self.tabs.addTab(self.preferences_panel, "Preferences")

    def show_history(self) -> None:
        self.tabs.setCurrentWidget(self.prompt_browser)


if __name__ == '__main__':
    from quack2tex.repository.db.sync_session import  init_db
    app = QApplication(sys.argv)
    init_db()
    win = SettingsWindow()
    win.show()
    sys.exit(app.exec())
