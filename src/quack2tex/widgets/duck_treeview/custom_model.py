import itertools
import typing

from PySide6 import QtCore
from PySide6.QtCore import QModelIndex, QObject, Signal
from PySide6.QtGui import Qt, QIcon

from .custom_node import CustomNode


class CustomModel(QtCore.QAbstractItemModel, QObject):
    """
    Custom model class
    """
    data_changed = Signal(CustomNode, int, object, object)

    def __init__(self, columns):
        """
        Initialize the custom model with the given columns.
        """
        QtCore.QAbstractItemModel.__init__(self)
        self._root = CustomNode(list(itertools.repeat("", len(columns))))
        self._columns = columns

    @property
    def root(self):
        """
        Return the root node of the model.
        """
        return self._root

    def check_all_items(self):
        """
        Check all items in the model.
        """
        self.root.checked = True
        self.refresh_model()

    def uncheck_all_items(self):
        """
        Uncheck all items in the model.
        """
        self.root.checked = False
        self.refresh_model()

    def refresh_model(self):
        """
        Refresh the model layout.
        """
        self.layoutChanged.emit()

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...) -> typing.Any:
        """
        Return the header data for the given section and orientation.
        """
        if role == QtCore.Qt.DisplayRole:
            return self._columns[section]
        return super(CustomModel, self).headerData(section, orientation, role)

    def addChild(self, node, parent=None):
        """
        Add a child node to the given parent node.
        """
        try:
            if parent and parent.isValid():
                parent_item = parent.internalPointer()
            else:
                parent_item = self._root

            # Determine the new row index
            new_row = parent_item.child_count()
            # Notify views that we're about to insert rows
            self.beginInsertRows(self.createIndex(parent_item.child_number(), 0, parent_item), new_row, new_row)
            # Add the new node
            # Add the child node
            parent_item.add_child(node)

            # Notify views that the insertion is complete
            self.endInsertRows()
            #parent_item.add_child(node)
        except Exception as e:
            print(e)


    def setData(self, index: QModelIndex, value, role: int) -> bool:
        """
        Set the data for the specified index and role.
        """
        if not index.isValid():
            return False
        item: CustomNode = self.get_item_from_index(index)
        if role == Qt.CheckStateRole:
            old_val = item.checked
            new_value = value == Qt.CheckState.Checked.value
            item.checked = new_value
            self.data_changed.emit(item, old_val, new_value, role)
            self.layoutChanged.emit()
            return True
        elif role == Qt.EditRole and value:
            old_val = item.data(index.column())
            new_value = value
            item.set_data(index.column(), value)
            self.data_changed.emit(item, old_val, new_value, role)
            self.layoutChanged.emit()
            return True
        return False

    def removeChild(self, index: QModelIndex):
        """
        Remove the child node at the given index.
        """
        self.beginRemoveRows(index.parent(), index.row(), index.row())
        success = self.removeRow(index.row(), parent=index.parent())
        self.endRemoveRows()
        return success

    def removeRow(self, row, parent):
        """
        Remove the row at the given index from the parent node.
        """
        if not parent.isValid():
            parent_node = self._root
        else:
            parent_node = parent.internalPointer()
        parent_node.remove_child(row)
        return True

    def data(self, index: QModelIndex, role=None):
        """
        Return the data for the given index and role.
        """
        if not index.isValid():
            return None
        node: CustomNode = index.internalPointer()
        if role == Qt.DisplayRole:
            return node.data(index.column())
        elif role == Qt.DecorationRole and index.column() == 0:
            return QIcon(node.icon)
        elif role == Qt.ToolTipRole:
            if node.tag and node.tooltip_attr:
                return getattr(node.tag, node.tooltip_attr)
        elif role == Qt.CheckStateRole and index.column() == 0:
            if node.checked:
                return Qt.CheckState.Checked
            else:
                return Qt.CheckState.Unchecked
        return None

    def get_item_from_index(self, index: QModelIndex = QModelIndex()) -> CustomNode:
        """
        Return the item from the specified index.
        """
        if index.isValid():
            item: CustomNode = index.internalPointer()
            if item:
                return item
        return self.root

    def get_index_from_item(self, item: CustomNode) -> QModelIndex:
        """
        Return the index of the specified item.
        """
        if not item:
            return QModelIndex()
        if item.parent() is None:
            return QModelIndex()
        return self.createIndex(item.child_count(), 0, item)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Return the flags for the specified index.
        """
        if not index.isValid():
            return Qt.NoItemFlags
        flags: Qt.ItemFlags = super(CustomModel, self).flags(index)
        flags &= ~Qt.ItemIsSelectable
        node: CustomNode = index.internalPointer()
        if node and node.enabled:
            flags |= Qt.ItemIsSelectable
        return flags | Qt.ItemIsEditable | Qt.ItemIsUserCheckable

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs):
        """
        Return the number of rows under the given parent.
        """
        if parent and parent.isValid():
            child: CustomNode = parent.internalPointer()
            return child.child_count()
        return self._root.child_count()

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs):
        """
        Return the number of columns for the children of the given parent.
        """
        if parent.isValid():
            return parent.internalPointer().column_count()
        return self._root.column_count()

    def parent(self, in_index: QModelIndex = None):
        """
        Return the parent of the given index.
        """
        try:
            if in_index.isValid():
                parent = in_index.internalPointer().parent()
                if parent:
                    return QtCore.QAbstractItemModel.createIndex(
                        self, parent.child_number(), 0, parent
                    )
            return QtCore.QModelIndex()
        except Exception as e:
            print(e)
            return QtCore.QModelIndex()

    def index(self, row: int, column: int, parent=None, *args, **kwargs):
        """
        Return the index of the item in the model specified by the given row, column, and parent index.
        """
        if not parent or not parent.isValid():
            parent_node = self._root
        else:
            parent_node = parent.internalPointer()
        if parent and not QtCore.QAbstractItemModel.hasIndex(self, row, column, parent):
            return QtCore.QModelIndex()
        child = parent_node.child(row)
        if child:
            return QtCore.QAbstractItemModel.createIndex(self, row, column, child)
        else:
            return QtCore.QModelIndex()

    def reset(self):
        """
        Reset the model to its initial state.
        """
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)
        while self.rowCount() > 0:
            index = self.index(0, 0)
            self.removeChild(index)
        self.endRemoveRows()



    def checked_nodes(self, root_node=None):
        """
        Return a list of all checked nodes starting from the given root node.
        """
        list_checked_items = []
        if root_node is None:
            root_node = self._root
        for child_node in root_node.child_items:
            if child_node.checked:
                list_checked_items.append(child_node)
            list_checked_items += self.checked_nodes(child_node)
        return list_checked_items

