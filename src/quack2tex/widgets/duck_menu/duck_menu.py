from PySide6.QtCore import QSize, QThreadPool
from quack2tex.repository import MenuItemRepository
from quack2tex.repository.db.sync_session import get_db_session
from quack2tex.widgets import FloatingMenu, LoadingIndicator, FloatingMenuItem
from quack2tex.utils.worker import  Worker
from quack2tex.resources import resources_rc  # noqa: F401


class DuckMenu(FloatingMenu):
    def __init__(self, parent=None):
        """
        Initialize the DuckMenu with a loading indicator and a thread pool for asynchronous tasks.
        """
        super().__init__(parent=parent)
        self.threadpool = QThreadPool()
        self.loading_indicator = LoadingIndicator(":icons/loading.gif", QSize(200, 100), self)
        self.loading_indicator.hide()

    def clear_menu(self):
        """
        Clear the menu by deleting all FloatingMenuItem children.
        """
        for item in self.findChildren(FloatingMenuItem):
            item.deleteLater()

    def build_menu(self):
        """
        Start building the menu asynchronously by fetching data from the database.
        """
        worker = Worker(self.do_build_menu)
        worker.signals.result.connect(self.done_build_menu)
        self.threadpool.start(worker)

    def do_build_menu(self):
        """
        Synchronously fetch the menu data from the database.
        """
        with get_db_session() as session:
            return MenuItemRepository.build_tree(session)

    def done_build_menu(self, tree):
        """
        Process the fetched menu data and populate the FloatingMenu with items.
        :param tree: The hierarchical menu tree fetched from the database.
        """
        self.clear_menu()
        root_item = self.create_root_item()
        self.add_default_items(root_item)
        self.populate_menu(tree, root_item)
        self.set_root(root_item)
        self.draw_menu()

        self.loading_indicator.move(
            int(self.geometry().center().x() - self.loading_indicator.width() // 2),
            int(self.geometry().center().y())
        )


    def create_root_item(self):
        """
        Create and return the root FloatingMenuItem for the DuckMenu.
        """
        return FloatingMenuItem(
            ":icons/rubber-duck.png",
            QSize(64, 64),
            distance_to_center=100,
            start_angle=0,
            end_angle=360,
            root=None,
            parent=self
        )

    def add_default_items(self, root_item):
        """
        Add default items (e.g., Close and Settings) to the root item.
        :param root_item: The root FloatingMenuItem.
        """
        default_items = [
            {"icon": ":icons/close.png", "tooltip": "Close", "data": {"action": "exit"}},
            {"icon": ":icons/gears.png", "tooltip": "Settings", "data": {"action": "settings"}},
        ]
        for item in default_items:
            self.create_menu_item(root_item, item)

    def create_menu_item(self, parent_item, action):
        """
        Create a menu item and attach it to a parent item.
        :param parent_item: The parent FloatingMenuItem.
        :param action: Dictionary containing icon, tooltip, and data for the item.
        """
        item = FloatingMenuItem(
            action["icon"],
            QSize(parent_item.size().width() // 2, parent_item.size().height() // 2),
            distance_to_center=parent_item.distance_to_center // 2,
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
            self.add_menu_item_recursive(db_item, root_item)

    def add_menu_item_recursive(self, db_item, parent_item):
        """
        Recursively add items to the menu based on the database item hierarchy.
        :param db_item: Database item containing child items.
        :param parent_item: The parent FloatingMenuItem to which children will be added.
        """
        child_item = FloatingMenuItem(
            db_item.icon,
            #QSize(parent_item.size().width() // 2, parent_item.size().height() // 2),
            QSize(32, 32),
            distance_to_center=parent_item.distance_to_center // 2,
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
            self.add_menu_item_recursive(db_child_item, child_item)
