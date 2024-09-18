from PySide6 import QtCore
from PySide6.QtWidgets import QWidget
from .floating_menu_item import FloatingMenuItem


class FloatingMenu(QWidget):
    """
    A floating menu widget that displays a circular menu
    """
    item_clicked = QtCore.Signal(dict)

    def __init__(self, root_item : FloatingMenuItem =None, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.root_item = root_item

    def set_root(self, root_item: FloatingMenuItem):
        """
        Set the root item of the menu.
        :param root_item:
        :return:
        """
        self.root_item = root_item
        self.root_item.setParent(self)

    def handle_item_click(self):
        """
        Handle the item click event.
        :return:
        """
        if current_item := self.sender():
            current_item.toggle()
            data = current_item.data
            if data:
                self.item_clicked.emit(data)
                self.toggle_item(current_item)

            if current_item == self.root_item and self.root_item.is_expanded():
                self.root_item.toggle()

    def toggle_item(self, item):
        """
        Recursively toggle the root item.
        :param item:
        :return:
        """
        if item.root:
            item.root.toggle()
            self.toggle_item(item.root)


    def draw_item_children(self, parent_item: FloatingMenuItem, center):
        """
        Draw the children of a given item.
        :param parent_item:
        :param center:
        :return:
        """
        for item in parent_item.children:
            item.doubleClicked.connect(self.handle_item_click)
            item.setParent(self)
            item.root = parent_item
            item.move(center.x() - item.width() // 2, center.y() - item.height() // 2)
            item.hide()
            if item.children:
                self.draw_item_children(item, center)

    def draw_menu(self):
        """
        Draw the menu
        :return:
        """
        assert self.root_item is not None, "Root item is not set"
        center = self.geometry().center()
        self.root_item.move(center.x() - self.root_item.width() // 2, center.y() - self.root_item.height() // 2)
        self.root_item.doubleClicked.connect(self.handle_item_click)
        self.root_item.show()
        if self.root_item.children:
            self.draw_item_children(self.root_item, center)
