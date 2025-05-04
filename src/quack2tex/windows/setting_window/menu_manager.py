import typing
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from PIL import Image
from PIL import Image as PILImage

from quack2tex import GuiUtils
from quack2tex.pyqt import (
    QModelIndex, QThreadPool, QSize, Signal, QIcon, QStandardItem, QPushButton, QToolBar,
    QTreeView,
    QVBoxLayout, QFrame, QDialog
)
from quack2tex.repository import MenuItemRepository
from quack2tex.repository.db.sync_session import get_db_session
from quack2tex.repository.models import MenuItem
from quack2tex.utils import TreeViewStandardItemModel, work_exception, Worker, LibUtils  # Replace CustomModel with this
from quack2tex.windows.setting_window.menu_item_form import MenuItemForm


class MenuManager(QFrame):
    on_menu_options_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.toolbar = QToolBar()
        self.treeview = QTreeView()

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.treeview)

        self.btn_check_all = QPushButton()
        self.btn_check_all.setIcon(QIcon(":/icons/check-all.png"))
        self.btn_check_all.setIconSize(QSize(16, 16))
        self.btn_check_all.clicked.connect(self.check_all_items)
        self.btn_check_all.setToolTip("Check all items")
        self.toolbar.addWidget(self.btn_check_all)

        self.btn_uncheck_all = QPushButton()
        self.btn_uncheck_all.setIcon(QIcon(":/icons/uncheck-all.png"))
        self.btn_uncheck_all.setIconSize(QSize(16, 16))
        self.btn_uncheck_all.clicked.connect(self.uncheck_all_items)
        self.btn_uncheck_all.setToolTip("Uncheck all items")
        self.toolbar.addWidget(self.btn_uncheck_all)

        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(QIcon(":/icons/refresh.png"))
        self.btn_refresh.setIconSize(QSize(16, 16))
        self.btn_refresh.clicked.connect(self.populate_treeview)
        self.btn_refresh.setToolTip("Refresh items")
        self.toolbar.addWidget(self.btn_refresh)

        self.btn_clear_selection = QPushButton()
        self.btn_clear_selection.setIconSize(QSize(16, 16))
        self.btn_clear_selection.setIcon(QIcon(":/icons/broom.png"))
        self.btn_clear_selection.setToolTip("Clear items selection")
        self.btn_clear_selection.clicked.connect(self.treeview.clearSelection)
        self.toolbar.addWidget(self.btn_clear_selection)

        self.toolbar.addSeparator()

        self.btn_add = QPushButton()
        self.btn_add.setIcon(QIcon(":/icons/add.png"))
        self.btn_add.setIconSize(QSize(16, 16))
        self.btn_add.setToolTip("Add new item")
        self.btn_add.clicked.connect(self.add_new_item)
        self.toolbar.addWidget(self.btn_add)

        self.btn_edit = QPushButton()
        self.btn_edit.setIcon(QIcon(":/icons/edit.png"))
        self.btn_edit.setIconSize(QSize(16, 16))
        self.btn_edit.clicked.connect(self.edit_selected_item)
        self.btn_edit.setToolTip("Edit selected item")
        self.toolbar.addWidget(self.btn_edit)

        self.btn_delete = QPushButton()
        self.btn_delete.setIcon(QIcon(":/icons/delete.png"))
        self.btn_delete.setIconSize(QSize(16, 16))
        self.btn_delete.clicked.connect(self.delete_selected_items)
        self.btn_delete.setToolTip("Delete checked items")
        self.toolbar.addWidget(self.btn_delete)

        self.thread_pool = QThreadPool()
        model = TreeViewStandardItemModel(["Name"])
        self.treeview.setModel(model)
        self.populate_treeview()

    def check_all_items(self) -> None:
        """
        Check all items.
        """
        try:
            model: TreeViewStandardItemModel = self.treeview.model()
            model.check_all_items()
        except Exception as e:
            print(e)

    def uncheck_all_items(self) -> None:
        """
        Uncheck all items.
        """
        try:
            model: TreeViewStandardItemModel = self.treeview.model()
            model.uncheck_all_items()
        except Exception as e:
            print(e)

    def edit_selected_item(self) -> None:
        """
        Edit the selected item.
        :return:
        """
        model = self.treeview.model()
        selected_indexes = self.treeview.selectionModel().selectedIndexes()
        if not selected_indexes:
            GuiUtils.show_error("No item selected.")
            return

        selected_index = selected_indexes[0]
        tree_item = model.itemFromIndex(selected_index)
        tree_item_data: MenuItem = tree_item.tag
        edit_item_form = MenuItemForm(initial_values=asdict(tree_item_data))

        dialog_result = edit_item_form.exec()
        if dialog_result == QDialog.DialogCode.Accepted:
            model = MenuItem(
                name=edit_item_form.name,
                icon=edit_item_form.icon,
                models=edit_item_form.models,
                capture_mode=edit_item_form.capture_mode,
                system_instruction=edit_item_form.system_instruction,
                guidance_prompt=edit_item_form.guidance_prompt,
                parent_id=tree_item_data.parent_id,
                is_root=tree_item_data.is_root,
            )
            model.id = tree_item_data.id

            self.save_or_update_item(model)

    def save_or_update_item(self, item):
        """
        Save or update an item.
        :param item:
        :param item_id:
        :return:
        """
        work = Worker(self.do_save_or_update_item, item)
        work.signals.result.connect(self.on_save_or_update_done)
        self.thread_pool.start(work)

    @work_exception
    def do_save_or_update_item(self, tree_item):
        """
        Do the work -> save or update the item.
        :param tree_item:
        :return:
        """
        icon_out_path: Optional[Path] = None
        if tree_item.icon and not tree_item.icon.startswith(":"):
            quack2tex_home = LibUtils.get_lib_home()
            icons_folder = quack2tex_home / "icons"
            icons_folder.mkdir(exist_ok=True, parents=True)

            icon_in_path = Path(tree_item.icon)
            image: PILImage = Image.open(str(icon_in_path))
            image.thumbnail((64, 64))
            icon_out_path = icons_folder / f"{icon_in_path.name}"
            image.save(str(icon_out_path))
            tree_item.icon = str(icon_out_path)
        try:
            with get_db_session() as session:
                if tree_item.id:
                    print("Updating item")
                    new_item = MenuItemRepository.update_item(session, tree_item)
                else:
                    new_item = MenuItemRepository.add_item(session, tree_item)
            print(f"Item saved: {new_item}")
            return new_item
        except Exception as e:
            if icon_out_path and icon_out_path.exists():
                icon_out_path.unlink()
            raise e

    def on_save_or_update_done(self, result) -> None:
        """
        Handle the completion of save or update operation.
        :param result:
        :return:
        """
        new_item, error = result
        if error:
            GuiUtils.show_error(str(error))
            return
        GuiUtils.show_info("Item updated successfully.")
        self.on_menu_options_changed.emit()
        self.populate_treeview()

    def delete_selected_items(self) -> None:
        """
        Delete selected items.
        """
        model: TreeViewStandardItemModel = self.treeview.model()
        checked_items = model.find_checked_nodes_recursive()
        checked_items = [item for item in checked_items if item.tag.parent_id is not None]
        if not checked_items:
            GuiUtils.show_error("No items selected.")
            return
        self.populate_treeview()

        ids = [item.tag.id for item in checked_items]
        work = Worker(self.do_delete_items, ids)
        work.signals.result.connect(self.on_delete_done)
        self.thread_pool.start(work)

    def do_delete_items(self, ids):
        """
        Do the work -> delete the items.
        :param ids:
        :return:
        """
        with get_db_session() as session:
            MenuItemRepository.delete_items(session, ids)

    def on_delete_done(self) -> None:
        """
        Handle the completion of delete operation.
        :return:
        """
        GuiUtils.show_info("Items deleted successfully.")
        self.on_menu_options_changed.emit()
        model: TreeViewStandardItemModel = self.treeview.model()
        model.remove_checked_items()
        model.layoutChanged.emit()
        self.populate_treeview()

    def add_new_item(self) -> None:
        """
        Add a new item.
        """
        selected_indexes: typing.List[QModelIndex] = self.treeview.selectionModel().selectedIndexes()
        if not selected_indexes:
            GuiUtils.show_error("No item selected.")
            return

        selected_index: QModelIndex = selected_indexes[0]
        model: TreeViewStandardItemModel = self.treeview.model()
        parent_item = model.itemFromIndex(selected_index)

        new_item_form = MenuItemForm()
        new_item_form.setFixedSize(600, 500)
        dialog_result = new_item_form.exec()
        if dialog_result == QDialog.DialogCode.Accepted:
            new_item = MenuItem(
                name=new_item_form.name,
                icon=new_item_form.icon,
                models=new_item_form.models,
                capture_mode=new_item_form.capture_mode,
                system_instruction=new_item_form.system_instruction,
                guidance_prompt=new_item_form.guidance_prompt,
                parent_id=parent_item.tag.id if parent_item else None
            )
            self.save_or_update_item(new_item)

    def populate_treeview(self) -> None:
        """
        Populate the treeview with data from the database.
        """
        work = Worker(self.do_fetch_tree_data)
        work.signals.result.connect(self.on_tree_data_fetched)
        self.thread_pool.start(work)

    def do_fetch_tree_data(self) -> typing.List[MenuItem]:
        """
        Do the work -> fetch the data from the database.
        :return:
        """
        with get_db_session() as session:
            return MenuItemRepository.fetch_tree_data(session)

    def on_tree_data_fetched(self, result: typing.List[MenuItem]) -> None:
        """
        Handle the completion of tree data fetch operation.
        :param result:
        :return:
        """
        self.treeview.model().reset_model()

        # Main iteration to populate the root items
        for tree_item_data in result:
            treeview_item = QStandardItem(tree_item_data.name)
            treeview_item.setCheckable(True)
            treeview_item_icon = QIcon(":/icons/gears.png")
            if tree_item_data.icon:
                treeview_item_icon = QIcon(tree_item_data.icon)
            treeview_item.setIcon(treeview_item_icon)
            treeview_item.tag = tree_item_data
            self.treeview.model().appendRow(treeview_item)
            self.populate_children(tree_item_data, treeview_item)

    def populate_children(self,tree_item_data: MenuItem, parent_item: QStandardItem) -> None:
        """
        Populate the children of the tree item in an optimized, non-recursive manner.
        :param tree_item_data: The MenuItem containing child items.
        :param parent_item: The QStandardItem that will be the parent of child items.
        :return: None
        """
        items_to_add = []

        # Pre-create child items and prepare them for appending
        for child_item_data in tree_item_data.children:
            child_item = QStandardItem(child_item_data.name)
            child_item.setCheckable(True)

            treeview_item_icon = QIcon(":/icons/gears.png")
            if child_item_data.icon:
                treeview_item_icon = QIcon(child_item_data.icon)
            child_item.setIcon(treeview_item_icon)
            child_item.tag = child_item_data
            items_to_add.append(child_item)

        # Append all child items at once
        if items_to_add:
            parent_item.appendRows(items_to_add)

        # Now populate the children for all the new child items in a non-recursive manner
        for child_item, child_data in zip(items_to_add, tree_item_data.children):
            self.populate_children(child_data, child_item)
