import contextlib
import weakref

from quack2tex.pyqt import QPoint, QRect, Qt, Signal, QWidget
from .floating_menu_item import FloatingMenuItem


class FloatingMenu(QWidget):
    """
    A floating menu widget that displays a circular menu
    """
    item_clicked = Signal(dict)

    def __init__(self, root_item: FloatingMenuItem = None, parent=None):
        super().__init__(parent)
        self.setObjectName("floatingMenu")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.setStyleSheet("#floatingMenu { background: transparent; }")
        self.setContentsMargins(0, 0, 0, 0)
        self.root_item = weakref.ref(root_item) if root_item else None  # Safely create weakref if root_item is not None
        self._suspend_window_reposition = False


    def set_root(self, root_item: FloatingMenuItem):
        """
        Set the root item of the menu.
        :param root_item:
        :return:
        """
        self.root_item = weakref.ref(root_item) if root_item else None  # Safely create weakref if root_item is not None
        if self.root_item:
            self.root_item().setParent(self)  # Dereference before use

    def connect_menu_item(self, item: FloatingMenuItem) -> None:
        """
        Connect item signals once for the current menu instance.
        """
        if item.property("_quack2tex_menu_connected"):
            return
        item.doubleClicked.connect(self.handle_item_click)
        item.expanded.connect(self.fit_to_visible_items)
        item.collapsed.connect(self.fit_to_visible_items)
        item.setProperty("_quack2tex_menu_connected", True)

    def detach_menu_item(self, item: FloatingMenuItem) -> None:
        """
        Disconnect and hide an item before deferred Qt deletion.
        """
        item.hide()
        with contextlib.suppress(TypeError):
            item.doubleClicked.disconnect(self.handle_item_click)
        with contextlib.suppress(TypeError):
            item.expanded.disconnect(self.fit_to_visible_items)
        with contextlib.suppress(TypeError):
            item.collapsed.disconnect(self.fit_to_visible_items)
        item.setProperty("_quack2tex_menu_connected", False)
        item.setParent(None)

    def _all_menu_items(self):
        """
        Return all menu items that belong to this floating menu.
        """
        return self.findChildren(FloatingMenuItem)

    def _visible_menu_items(self):
        """
        Return visible menu items, falling back to the root item while rebuilding.
        """
        items = [item for item in self._all_menu_items() if item.isVisible()]
        if not items and self.root_item and self.root_item():
            items = [self.root_item()]
        return items

    def _move_window_by(self, delta: QPoint):
        """
        Move the top-level window by a local widget delta so buttons do not jump
        on screen when the floating widget is resized around them.
        """
        if self._suspend_window_reposition:
            return
        window = self.window()
        if window is not None and window is not self:
            window.move(window.pos() + delta)
        else:
            self.move(self.pos() + delta)

    def fit_to_items(self, items=None, extra_rects=None, padding=28):
        """
        Resize the transparent widget to fit the supplied/visible buttons.
        :param items: Menu items to include in the bounds.
        :param extra_rects: Future item rectangles to include before animation.
        :param padding: Extra transparent space around the buttons.
        :return: The local translation applied to child items.
        """
        items = items or self._visible_menu_items()
        rects = [item.geometry() for item in items]
        if extra_rects:
            rects.extend(extra_rects)
        if not rects:
            return QPoint(0, 0)

        bounds = QRect(rects[0])
        for rect in rects[1:]:
            bounds = bounds.united(rect)

        target_top_left = QPoint(padding, padding)
        delta = bounds.topLeft() - target_top_left
        if delta != QPoint(0, 0):
            for item in self._all_menu_items():
                item.move(item.pos() - delta)
            self._move_window_by(delta)

        new_size = bounds.size()
        new_size.setWidth(new_size.width() + padding * 2)
        new_size.setHeight(new_size.height() + padding * 2)
        self.setFixedSize(new_size)
        window = self.window()
        if window is not None and window is not self:
            window.setFixedSize(new_size)
        return delta

    def fit_to_visible_items(self):
        """
        Resize the floating widget to exactly fit the buttons that are visible.
        """
        self.fit_to_items()

    def prepare_expand_bounds(self, parent_item: FloatingMenuItem, child_positions):
        """
        Include soon-to-be-visible submenu buttons before their animation starts.
        """
        rects = [
            QRect(position, child.size())
            for child, position in child_positions
        ]
        self.fit_to_items(
            items=self._visible_menu_items() + list(parent_item.children),
            extra_rects=rects,
        )

    def handle_item_click(self):
        """
        Handle the item click event.
        :return:
        """
        try:
            current_item = self.sender()
            if not isinstance(current_item, FloatingMenuItem):
                return

            # If item is a leaf node (no children) and has data, it's an action.
            if not current_item.children and current_item.data:
                self.item_clicked.emit(current_item.data)
                # After action, collapse the whole menu if it's expanded.
                if self.root_item and self.root_item() and self.root_item().is_expanded():
                    self.root_item().toggle()
                return

            # If item has children, just toggle it.
            current_item.toggle()
        except Exception as e:
            print(e)

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
                    self.connect_menu_item(item)
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
                self.root_item().move(0, 0)
                center = self.root_item().geometry().center()
                self.connect_menu_item(self.root_item())
                self.root_item().show()
                if self.root_item().children:
                    self.draw_item_children(self.root_item(), center)
                self.fit_to_visible_items()
            else:
                raise Exception("Root item not set or invalid.")
        except Exception as e:
            print(e)
