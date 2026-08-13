from pathlib import Path

from quack2tex.pyqt import QPoint, QSize, QThreadPool, Signal
from quack2tex.preferences import Preferences
from quack2tex.repository import MenuItemRepository
from quack2tex.repository.db.sync_session import get_db_session
from quack2tex.resources import *  # noqa: F401
from quack2tex.utils.worker import Worker
from quack2tex.widgets import FloatingMenu, LoadingIndicator, FloatingMenuItem
from quack2tex.widgets.pomodoro_timer import PomodoroTimer


class DuckMenu(FloatingMenu):
    on_hold = Signal()
    pomodoro_icon_path = str(
        Path(__file__).resolve().parents[2] / "resources" / "icons" / "pomodoro-technique.png"
    )

    def __init__(self, parent=None):
        """
        Initialize the DuckMenu with a loading indicator and a thread pool for asynchronous tasks.
        """
        super().__init__(parent=parent)
        self.threadpool = QThreadPool()
        self.loading_indicator = LoadingIndicator(":icons/loading.gif", QSize(200, 100))
        self.loading_indicator.hide()
        self.pomodoro_timer = PomodoroTimer()
        self.pomodoro_timer.hide()
        self.default_icon_path = ":icons/ai.png"

    def clear_menu(self):
        """
        Clear the menu by deleting all FloatingMenuItem children.
        """
        for item in self.findChildren(FloatingMenuItem):
            self.detach_menu_item(item)
            item.deleteLater()
        self.root_item = None

    def build_menu(self):
        """
        Start building the menu asynchronously by fetching data from the database.
        """
        root_item = self.root_item() if self.root_item and self.root_item() else None
        self._rebuild_root_center = (
            self.mapToGlobal(root_item.geometry().center())
            if root_item is not None
            else None
        )
        self._suspend_window_reposition = True
        worker = Worker(self.do_query_menu_data)
        worker.signals.result.connect(self.done_query_menu_data)
        self.threadpool.start(worker)

    def do_query_menu_data(self):
        """
        Synchronously fetch the menu data from the database.
        """
        with get_db_session() as session:
            root_item = MenuItemRepository.fetch_root_item_data(session)
            root_children = MenuItemRepository.fetch_root_children_data(session, root_item.id)
            favorite_items = MenuItemRepository.fetch_items_by_ids(session, Preferences.favorites())
            return root_item, root_children, favorite_items

    def done_query_menu_data(self, result):
        """
        Process the fetched menu data and populate the FloatingMenu with items.
        """
        root_item_data, root_children_data, favorite_items = result
        self.clear_menu()
        root_item = self.create_root_item(root_item_data)
        root_item.collapsed.connect(self.on_root_collapsed)
        root_item.expanded.connect(self.on_root_expanded)
        root_item.on_hold.connect(self.on_hold_handler)
        self.add_default_items(root_item)
        self.add_favorite_items(root_item, favorite_items)
        self.populate_menu(root_children_data, root_item)
        self.set_root(root_item)
        self.draw_menu()
        self._suspend_window_reposition = False
        if self._rebuild_root_center is not None:
            window = self.window()
            current_center = self.mapToGlobal(root_item.geometry().center())
            if window is not None and current_center != self._rebuild_root_center:
                window.move(window.pos() + (self._rebuild_root_center - current_center))
            self._rebuild_root_center = None


        self.position_loading_indicator()
        self.position_pomodoro_timer()

    def overlay_anchor(self) -> QPoint:
        """
        Return the shared global anchor for floating overlays.
        """
        if not self.root_item or not self.root_item():
            anchor = self.rect().center()
        else:
            anchor = self.root_item().geometry().center()
        return self.mapToGlobal(anchor)

    def position_loading_indicator(self):
        """
        Position the loading overlay in global coordinates so menu resizing
        cannot clip the animation.
        """
        global_anchor = self.overlay_anchor()
        self.loading_indicator.move(
            global_anchor - QPoint(
                self.loading_indicator.width() // 2,
                -self.root_item().height() // 2 if self.root_item and self.root_item() else 0,
            )
        )

    def position_pomodoro_timer(self):
        """
        Keep the pomodoro overlay centered below the duck root item.
        """
        if self.root_item and self.root_item():
            root_rect = self.root_item().geometry()
            global_anchor = self.mapToGlobal(root_rect.bottomLeft())
            x = global_anchor.x() + (root_rect.width() - self.pomodoro_timer.width()) // 2
            y = global_anchor.y() + 14
        else:
            global_anchor = self.overlay_anchor()
            x = global_anchor.x() - self.pomodoro_timer.width() // 2
            y = global_anchor.y() + 14
        self.pomodoro_timer.move(
            QPoint(x, y)
        )

    def show_loading_indicator(self):
        self.position_loading_indicator()
        self.loading_indicator.show()
        self.loading_indicator.raise_()

    def hide_loading_indicator(self):
        self.loading_indicator.hide()

    def closeEvent(self, event) -> None:
        """Close detached overlay windows with the duck menu."""
        self.loading_indicator.close()
        self.pomodoro_timer.close()
        super().closeEvent(event)

    def show_pomodoro_timer(self, restart: bool = False):
        settings = Preferences.pomodoro()
        self.position_pomodoro_timer()
        self.pomodoro_timer.start(
            settings["work_minutes"],
            settings["rest_minutes"],
            restart=restart,
        )

    def start_pomodoro_timer(self):
        self.show_pomodoro_timer(restart=True)

    def on_hold_handler(self):
        """
        Handle the on-hold signal, which is emitted when the menu is held.
        """
        self.on_hold.emit()

    def on_root_collapsed(self):
        """Resize the menu to the root item's size when collapsed."""
        self.fit_to_visible_items()

    def on_root_expanded(self):
        """Resize the menu to fit all visible items."""
        self.fit_to_visible_items()


    def create_root_item(self, root_item_data):
        """
        Create and return the root FloatingMenuItem for the DuckMenu.
        """
        duck_image = Preferences.duck_image()
        root_icon = duck_image or root_item_data.icon or self.default_icon_path
        return FloatingMenuItem(
            root_icon,
            QSize(72, 72),
            distance_to_center=130,
            start_angle=0,
            end_angle=360,
            root=None,
            parent=self,
            data={"action": None, "tag": root_item_data},
            icon_scale=1.08,
        )

    def add_default_items(self, root_item):
        """
        Add default items (e.g., Close and Settings) to the root item.
        :param root_item: The root FloatingMenuItem.
        """
        default_items = [
            {"icon": ":icons/ai.png", "tooltip": "Command Palette", "data": {"action": "command_palette"}},
            {"icon": ":icons/refresh.png", "tooltip": "Recent History", "data": {"action": "history"}},
            {"icon": self.pomodoro_icon_path, "tooltip": "pomodoro", "data": {"action": "pomodoro"}},
            {"icon": ":icons/close.png", "tooltip": "Close", "data": {"action": "exit"}},
            {"icon": ":icons/gears.png", "tooltip": "Settings", "data": {"action": "settings"}},
        ]
        for item in default_items:
            self.create_default_item_menu(root_item, item)

    def add_favorite_items(self, root_item, favorite_items):
        """
        Pin favorite prompt actions onto the first menu ring.
        """
        for item_data in favorite_items:
            if not item_data.guidance_prompt or not item_data.system_instruction:
                continue
            item = FloatingMenuItem(
                item_data.icon or self.default_icon_path,
                QSize(46, 46),
                distance_to_center=88,
                start_angle=0,
                end_angle=360,
                parent=self,
                data={"action": item_data.name, "tag": item_data}
            )
            item.setToolTip(f"Favorite: {item_data.name}")
            root_item.add_child(item)

    def create_default_item_menu(self, parent_item, action):
        """
        Create a menu item and attach it to a parent item.
        :param parent_item: The parent FloatingMenuItem.
        :param action: Dictionary containing icon, tooltip, and data for the item.
        """
        item = FloatingMenuItem(
            action["icon"] or self.default_icon_path,
            QSize(42, 42),
            distance_to_center=72,
            start_angle=0,
            end_angle=360,
            parent=self,
            data=action["data"]
        )
        item.setToolTip(action["tooltip"])
        parent_item.add_child(item)

    def populate_menu(self, tree, root_item):
        """
        Recursively populate the menu from the fetched tree.
        :param tree: List of database items representing the menu tree.
        :param root_item: The root FloatingMenuItem.
        """
        for db_item in tree:
            self.add_item_menu_recursive(db_item, root_item)

    def add_item_menu_recursive(self, db_item, parent_item):
        """
        Recursively add items to the menu based on the database item hierarchy.
        :param db_item: Database item containing child items.
        :param parent_item: The parent FloatingMenuItem to which children will be added.
        """
        child_item = FloatingMenuItem(
            db_item.icon or self.default_icon_path,
            QSize(44, 44),
            distance_to_center=max(76, parent_item.distance_to_center // 2),
            start_angle=0,
            end_angle=360,
            parent=self
        )
        prompt_node = db_item.guidance_prompt and db_item.system_instruction
        if prompt_node:
            child_item.data = {"action": db_item.name, "tag": db_item}
        child_item.setToolTip(db_item.name)
        parent_item.add_child(child_item)

        for db_child_item in db_item.children:
            self.add_item_menu_recursive(db_child_item, child_item)
