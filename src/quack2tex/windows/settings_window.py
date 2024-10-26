import sys
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import QModelIndex, QThreadPool, Qt, QSize, Signal
from PySide6.QtGui import QIcon, QStandardItem
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QToolBar, QMessageBox, QApplication, QTreeView
from PIL import Image

from quack2tex.repository import MenuItemRepository
from quack2tex.repository.db.sync_session import get_db_session
from quack2tex.repository.models import MenuItem
from quack2tex.utils import Worker, LibUtils, work_exception, GuiUtils
from quack2tex.widgets.forms import MenuItemForm
from quack2tex.resources import resources_rc # noqa

from quack2tex.utils import TreeViewStandardItemModel  # Replace CustomModel with this


class SettingsWindow(QDialog):
    """
    Main application window.
    """
    on_settings_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(800, 600)
        self.setWindowTitle("Settings")

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.toolbar = QToolBar()
        self.treeview = QTreeView()

        self.layout.addWidget(self.toolbar)

        self.btn_check_all = QPushButton()
        self.btn_check_all.setIcon(QIcon(":/icons/check-all.png"))
        self.btn_check_all.setIconSize(QSize(16, 16))
        self.btn_check_all.clicked.connect(self.check_all_items)
        self.toolbar.addWidget(self.btn_check_all)

        self.btn_uncheck_all = QPushButton()
        self.btn_uncheck_all.setIcon(QIcon(":/icons/uncheck-all.png"))
        self.btn_uncheck_all.setIconSize(QSize(16, 16))
        self.btn_uncheck_all.clicked.connect(self.uncheck_all_items)
        self.toolbar.addWidget(self.btn_uncheck_all)

        self.btn_delete = QPushButton()
        self.btn_delete.setIcon(QIcon(":/icons/delete.png"))
        self.btn_delete.setIconSize(QSize(16, 16))
        self.btn_delete.clicked.connect(self.delete_selected_items)
        self.toolbar.addWidget(self.btn_delete)

        self.btn_add = QPushButton()
        self.btn_add.setIcon(QIcon(":/icons/add.png"))
        self.btn_add.setIconSize(QSize(16, 16))
        self.btn_add.clicked.connect(self.add_new_item)
        self.toolbar.addWidget(self.btn_add)

        self.btn_edit = QPushButton()
        self.btn_edit.setIcon(QIcon(":/icons/edit.png"))
        self.btn_edit.setIconSize(QSize(16, 16))
        self.btn_edit.clicked.connect(self.edit_selected_item)
        self.toolbar.addWidget(self.btn_edit)

        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(QIcon(":/icons/refresh.png"))
        self.btn_refresh.setIconSize(QSize(16, 16))
        self.btn_refresh.clicked.connect(self.populate_treeview)
        self.toolbar.addWidget(self.btn_refresh)

        self.btn_clear_selection = QPushButton()
        self.btn_clear_selection.setIconSize(QSize(16, 16))
        self.btn_clear_selection.setIcon(QIcon(":/icons/broom.png"))
        self.btn_clear_selection.clicked.connect(self.treeview.clearSelection)
        self.toolbar.addWidget(self.btn_clear_selection)

        self.thread_pool = QThreadPool()
        model = TreeViewStandardItemModel(["Name"])
        self.treeview.setModel(model)

        self.layout.addWidget(self.treeview)
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
        treeview_item = model.itemFromIndex(selected_index)

        item_model: MenuItem = treeview_item.tag
        edit_item_form = MenuItemForm()
        edit_item_form.setFixedSize(600, 500)
        edit_item_form.form_data = {
            "name": item_model.name,
            "icon": item_model.icon,
            "models": item_model.models,
            "capture_mode": item_model.capture_mode,
            "system_instruction": item_model.system_instruction,
            "guidance_prompt": item_model.guidance_prompt
        }
        dialog_result = edit_item_form.exec()
        if dialog_result == QDialog.Accepted:
            item_model.name = edit_item_form.name
            item_model.icon = edit_item_form.icon
            item_model.models = edit_item_form.models
            item_model.capture_mode = edit_item_form.capture_mode
            item_model.system_instruction = edit_item_form.system_instruction
            item_model.guidance_prompt = edit_item_form.guidance_prompt
            self.save_or_update_item(item_model)

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
    def do_save_or_update_item(self, item):
        """
        Do the work -> save or update the item.
        :param item:
        :return:
        """
        icon_in_path = Path(item.icon)
        quack2tex_home = LibUtils.get_lib_home()
        icons_folder = quack2tex_home / "icons"
        icons_folder.mkdir(exist_ok=True, parents=True)
        image = Image.open(str(icon_in_path))
        image.thumbnail((64, 64))
        icon_out_path = icons_folder / f"{icon_in_path.name}"
        image.save(str(icon_out_path))
        item.icon = str(icon_out_path)

        try:
            with get_db_session() as session:
                if item.id:
                    print("Updating item")
                    new_item = MenuItemRepository.update_item(session, item)
                else:
                    new_item = MenuItemRepository.add_item(session, item)
            print(f"Item saved: {new_item}")
            return new_item
        except Exception as e:
            if icon_out_path.exists():
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
        self.on_settings_changed.emit()

    def delete_selected_items(self) -> None:
        """
        Delete selected items.
        """
        model: TreeViewStandardItemModel = self.treeview.model()
        checked_items = model.find_checked_nodes_recursive()
        if not checked_items:
            GuiUtils.show_error("No items selected.")
            return

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
        self.on_settings_changed.emit()
        model: TreeViewStandardItemModel = self.treeview.model()
        model.remove_checked_items()
        model.layoutChanged.emit()

    def add_new_item(self) -> None:
        """
        Add a new item.
        """
        selected_indexes: List[QModelIndex] = self.treeview.selectionModel().selectedIndexes()
        parent_item: Optional[QStandardItem] = None
        if selected_indexes:
            selected_index: QModelIndex = selected_indexes[0]
            model: TreeViewStandardItemModel = self.treeview.model()
            parent_item = model.itemFromIndex(selected_index)

        new_item_form = MenuItemForm()
        new_item_form.setFixedSize(600, 500)
        dialog_result = new_item_form.exec()
        if dialog_result == QDialog.Accepted:
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

    def do_fetch_tree_data(self) -> List[MenuItem]:
        """
        Do the work -> fetch the data from the database.
        :return:
        """
        with get_db_session() as session:
            return MenuItemRepository.build_tree(session)

    def on_tree_data_fetched(self, result: List[MenuItem]) -> None:
        """
        Handle the completion of tree data fetch operation.
        :param result:
        :return:
        """
        self.treeview.model().reset_model()

        def populate_children(tree_item_data: MenuItem, parent_item: QStandardItem) -> None:
            """
            Populate the children of the tree item.
            :param tree_item_data:
            :param parent_item:
            :return:
            """
            for child_item_data in tree_item_data.children:
                child_item = QStandardItem(child_item_data.name)
                child_item.setCheckable(True)
                child_item.setIcon(QIcon(child_item_data.icon))
                child_item.tag = child_item_data
                parent_item.appendRow(child_item)
                populate_children(child_item_data, child_item)

        for tree_item_data in result:
            treeview_item = QStandardItem(tree_item_data.name)
            treeview_item.setCheckable(True)
            treeview_item.setIcon(QIcon(tree_item_data.icon))
            treeview_item.tag = tree_item_data
            self.treeview.model().appendRow(treeview_item)
            populate_children(tree_item_data, treeview_item)


if __name__ == '__main__':
    app = QApplication([])
    win = SettingsWindow()
    win.show()
    sys.exit(app.exec())