import itertools
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon


class TreeViewStandardItemModel(QStandardItemModel):
    """
    Custom model class based on QStandardItemModel.
    """

    def __init__(self, columns):
        """
        Initialize the custom model with the given columns.
        """
        super().__init__(0, len(columns))  # Initialize model with given number of columns
        self._columns = columns
        self.setHorizontalHeaderLabels(columns)

    def reset_model(self):
        """
        Reset the model.
        """
        self.clear()
        self.setHorizontalHeaderLabels(self._columns)

    def flags(self, index):
        """
        Return the flags for the given index.
        """
        flags = super().flags(index)
        flags &= ~QtCore.Qt.ItemIsEditable
        return flags

    def remove_checked_items(self):
        """
        Remove all items that are checked.
        """
        def recursive_remove_items(parent: QStandardItem):
            """
            Recursively check all children and remove checked items.
            """
            rows_to_remove = []
            for row in range(parent.rowCount()):
                child_item = parent.child(row)
                # Check if the item is checked
                if child_item.checkState() == Qt.Checked:
                    rows_to_remove.append(row)
                else:
                    # Recursively check the item's children
                    recursive_remove_items(child_item)
            # Remove rows from the bottom to the top to prevent index issues
            for row in reversed(rows_to_remove):
                parent.removeRow(row)

        # Start the process from the root items in the model
        root = self.invisibleRootItem()
        recursive_remove_items(root)

    def check_all_items(self):
        """
        Check all items in the tree.
        """
        def recursive_check_items(parent: QStandardItem):
            for row in range(parent.rowCount()):
                child_item = parent.child(row)
                child_item.setCheckState(Qt.Checked)
                recursive_check_items(child_item)

        root = self.invisibleRootItem()
        recursive_check_items(root)

    def uncheck_all_items(self):
        """
        Uncheck all items in the tree.
        """
        def recursive_uncheck_items(parent: QStandardItem):
            for row in range(parent.rowCount()):
                child_item = parent.child(row)
                child_item.setCheckState(Qt.Unchecked)
                recursive_uncheck_items(child_item)

        root = self.invisibleRootItem()
        recursive_uncheck_items(root)

    def add_child(self, data, parent_item=None):
        """
        Add a child item with the given data.
        """
        new_item = QStandardItem(data)
        new_item.setCheckable(True)

        if parent_item is None:
            # Add as a top-level item
            self.appendRow(new_item)
        else:
            # Add as a child to the given parent item
            parent_item.appendRow(new_item)



    def find_checked_nodes_recursive(self, parent_item=None):
        """
        Find all checked items in the model.
        """
        checked_items = []
        if parent_item is None:
            parent_item = self.invisibleRootItem()

        for row in range(parent_item.rowCount()):
            child_item = parent_item.child(row)
            if child_item.checkState() == Qt.Checked:
                checked_items.append(child_item)
            checked_items += self.find_checked_nodes_recursive(child_item)

        return checked_items


    def set_data(self, index, value, role=Qt.EditRole):
        """
        Set the data for the given index and role.
        """
        item = self.itemFromIndex(index)
        if item:
            if role == Qt.CheckStateRole:
                item.setCheckState(Qt.Checked if value else Qt.Unchecked)
                return True
            elif role == Qt.EditRole:
                item.setText(value)
                return True
        return False

    def refresh_model(self):
        """
        Refresh the model layout.
        """
        self.layoutChanged.emit()
