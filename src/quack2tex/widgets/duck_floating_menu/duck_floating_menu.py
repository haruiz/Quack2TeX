from PySide6.QtCore import QSize

from quack2tex.widgets import FloatingMenu, LoadingIndicator
from .menu_items import menu_items


class DuckFloatingMenu(FloatingMenu):
    def __init__(self, parent=None):
        super().__init__(
            ":icons/rubber-duck.png",
            QSize(64, 64),
            QSize(32, 32),
            start_angle=0,
            end_angle=360,
            parent=parent,
        )
        for action in menu_items:
            self.add_menu_item(
                action["icon"], action["value"], action["tooltip"], action["data"]
            )

        self.draw_menu()

        self.loading_indicator = LoadingIndicator(
            ":icons/loading.gif", QSize(200, 100), self
        )
        self.loading_indicator.move(
            int(self.geometry().center().x() - self.loading_indicator.width() // 2),
            int(self.geometry().center().y()),
        )
        self.loading_indicator.close()
