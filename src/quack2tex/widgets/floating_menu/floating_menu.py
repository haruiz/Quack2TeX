import weakref

from PyQt6.QtCore import QTimer

from quack2tex.pyqt import Signal, QWidget
from .floating_menu_item import FloatingMenuItem


class FloatingMenu(QWidget):
    """
    A floating menu widget that displays a circular menu
    """
    item_clicked = Signal(dict)

    def __init__(self, root_item: FloatingMenuItem = None, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.root_item = weakref.ref(root_item) if root_item else None  # Safely create weakref if root_item is not None


    def set_root(self, root_item: FloatingMenuItem):
        """
        Set the root item of the menu.
        :param root_item:
        :return:
        """
        self.root_item = weakref.ref(root_item) if root_item else None  # Safely create weakref if root_item is not None
        if self.root_item:
            self.root_item().setParent(self)  # Dereference before use

    def handle_item_click(self):
        """
        Handle the item click event.
        :return:
        """
        try:
            if current_item := self.sender():
                current_item.toggle()
                data = current_item.data
                if data:
                    self.toggle_item(current_item)
                    if current_item != self.root_item():
                        self.item_clicked.emit(data)

                if current_item == self.root_item() and self.root_item() and self.root_item().is_expanded():
                    self.root_item().toggle()
        except Exception as e:
            print(e)

    def toggle_item(self, item):
        """
        Recursively toggle the root item.
        :param item:
        :return:
        """
        if item.root:
            if item.root is not None:  # Check if the root item still exists
                item.root.toggle()
                self.toggle_item(item.root)

    def draw_item_children(self, parent_item: FloatingMenuItem, center):
        """
        Draw the children of a given item.
        :param parent_item:
        :param center:
        :return:
        """
        try:
            for item in parent_item.children:
                if item is not None:  # Check if item is valid before using
                    item.doubleClicked.connect(self.handle_item_click)
                    item.setParent(self)
                    item.root = parent_item
                    item.move(center.x() - item.width() // 2, center.y() - item.height() // 2)
                    item.hide()
                    if item.children:
                        self.draw_item_children(item, center)
        except Exception as e:
            print(e)

    def draw_menu(self):
        """
        Draw the menu
        :return:
        """
        try:
            if self.root_item() is not None:  # Check if root item is valid before using
                center = self.geometry().center()
                self.root_item().move(center.x() - self.root_item().width() // 2, center.y() - self.root_item().height() // 2)
                self.root_item().doubleClicked.connect(self.handle_item_click)
                self.root_item().show()
                if self.root_item().children:
                    self.draw_item_children(self.root_item(), center)
            else:
                raise Exception("Root item not set or invalid.")
        except Exception as e:
            print(e)