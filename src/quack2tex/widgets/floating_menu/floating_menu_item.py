import math

from PySide6 import QtCore
from PySide6.QtCore import QSize, QParallelAnimationGroup, QPropertyAnimation, QPoint, QEasingCurve, QTimer, QRect
from PySide6.QtGui import QColor, QRegion, QPainter, QBrush
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect

from quack2tex.widgets import ImageButton


class FloatingMenuItem(ImageButton):
    """
    A floating menu item that displays an icon and can have children items.
    """

    def __init__(self, icon_path: str, icon_size: QSize, distance_to_center=100, start_angle=0, end_angle=360, root=None, parent=None, data=None):
        super().__init__(icon_path, icon_size, parent)
        self.distance_to_center = distance_to_center
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.children = []
        self.root = root
        self.clicked.connect(self.addGlowEffect)
        self.data = data
        self._expanded = False
        self._collapsed = True



    @property
    def data(self):
        return self.property("data")

    @data.setter
    def data(self, data):
        self.setProperty("data", data)


    def addGlowEffect(self):
        """
        Add a glow effect to the button
        :return:
        """
        # Create a shadow effect to simulate the glow
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(40)  # Increase blur radius for a strong glow effect
        glow.setColor(QColor(255, 255, 224))  # Neon cyan color (RGB: 0, 255, 255)
        glow.setOffset(0, 0)  # No offset, straight glow around the button
        # Apply the effect to the button
        self.setGraphicsEffect(glow)
        # Remove the glow after 1 second
        QTimer.singleShot(1000, self.removeGlowEffect)

    def removeGlowEffect(self):
        """
        Remove the glow effect from the button
        :return:
        """
        # Remove the shadow effect, returning the button to its normal state
        self.setGraphicsEffect(None)

    def fade(self):
        """
        Fade the button
        :return:
        """
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.animation = QtCore.QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.start()

    def unfade(self):
        """
        Unfade the button
        :return:
        """

        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.animation = QtCore.QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def add_child(self, child: "FloatingMenuItem"):
        """
        Add a child item to the menu item.
        :param child:  the child item to add
        :return:
        """
        self.children.append(child)

    def is_collapsed(self) -> bool:
        """
        Returns True if all children are hidden (collapsed).
        :return:
        """
        #return any(not child.isVisible() for child in self.children)
        return self._collapsed

    def is_expanded(self) -> bool:
        """
        Returns True if at least one child is visible (expanded).
        :return:
        """
        #return any(child.isVisible() for child in self.children)
        return self._expanded

    def get_items_angles(self, num_items):
        """
        Get the angles for the items
        :param num_items: number of items
        :return: list of angles
        """
        angle_range = self.end_angle - self.start_angle
        full_menu = self.start_angle == 0 and self.end_angle == 360
        angle_increment = angle_range / (
            num_items if full_menu else max(1, num_items - 1)
        )
        angles_rad = [math.radians(self.start_angle + i * angle_increment) for i in range(num_items)]
        return angles_rad

    def expand(self):
        """
        Expand the item and show its children with animation.
        :return:
        """
        if self.is_expanded() or not self.children:
            return

        self.raise_()
        center = self.geometry().center()
        num_children = len(self.children)
        angles_rad = self.get_items_angles(num_children)
        animation_group = QParallelAnimationGroup(self)
        for i, child in enumerate(self.children):
            child.move(QPoint(center.x() - child.width() // 2, center.y() - child.height() // 2))
            x = center.x() + self.distance_to_center * math.cos(angles_rad[i]) - child.width() // 2
            y = center.y() + self.distance_to_center * math.sin(angles_rad[i]) - child.height() // 2
            child.show()

            anim = QPropertyAnimation(child, b"pos")
            anim.setEndValue(QPoint(x, y))
            anim.setDuration(500)
            anim.setEasingCurve(QEasingCurve.OutBounce)
            animation_group.addAnimation(anim)
            animation_group.finished.connect(lambda: self.expand_animation_group_finished(child))

        animation_group.start()

    def expand_animation_group_finished(self, child):
        """
        Handle the animation group finished event
        :return:
        """
        self._expanded = True
        self._collapsed = False
        self.raise_()



    def collapse(self):
        """
        Collapse the item and hide its children with animation.
        :return:
        """

        if self.is_collapsed() or not self.children:
            return

        center = self.geometry().center()
        animation_group = QParallelAnimationGroup(self)

        for child in self.children:
            anim = QPropertyAnimation(child, b"pos")
            anim.setEndValue(QPoint(center.x() - child.width() // 2, center.y() - child.height() // 2))
            anim.setDuration(500)
            anim.setEasingCurve(QEasingCurve.OutBounce)
            anim.finished.connect(lambda: self.collapse_animation_group_finished(child))
            animation_group.addAnimation(anim)

        animation_group.start()

    def collapse_animation_group_finished(self, child):
        """
        Handle the animation group finished event
        :return:
        """
        child.hide()
        self._expanded = False
        self._collapsed = True


    def hide_children(self, parent_item: "FloatingMenuItem"):
        """
        Hide the children of a given item.
        :param parent_item:
        :return:
        """
        for child in parent_item.children:
            child.hide()
            if child.children:
                self.hide_children(child)

    def collapse_siblings(self):
        """
        Collapse the siblings of this item.
        :return:
        """
        center = self.root.geometry().center()
        group = QParallelAnimationGroup(self)
        siblings = [child for child in self.root.children if child != self]
        for sibling in siblings:
            anim = QPropertyAnimation(sibling, b"pos")
            anim.setEndValue(QPoint(center.x() - sibling.width() // 2, center.y() - sibling.height() // 2))
            anim.setDuration(500)
            anim.setEasingCurve(QEasingCurve.OutBounce)
            anim.finished.connect(sibling.hide)
            group.addAnimation(anim)
        group.start()

    def expand_siblings(self):
        """
        Expand the siblings of this item.
        :return:
        """
        root_center = self.root.geometry().center()
        num_siblings = len(self.root.children)
        angles_rad = self.get_items_angles(num_siblings)

        for i, sibling in enumerate(self.root.children):
            if sibling == self:
                continue
            x = root_center.x() + self.root.distance_to_center * math.cos(angles_rad[i]) - sibling.width() // 2
            y = root_center.y() + self.root.distance_to_center * math.sin(angles_rad[i]) - sibling.height() // 2
            sibling.move(x, y)
            sibling.setVisible(True)
            sibling.unfade()

    def mousePressEvent(self, e):
        """
        Triggered when the user presses the mouse button
        :param e:
        :return:
        """
        # Propagate the event to the parent window
        if self.window() is not None:
            self.window().mousePressEvent(e)
        super().mousePressEvent(e)

    def toggle(self):
        """
        Toggle the item between expanded and collapsed states.
        :return:
        """
        if self.is_collapsed():
            self.handle_expand()
        else:
            self.handle_collapse()

    def handle_expand(self):
        """Handle the logic for expanding the item."""
        if self.children:
            if self.root:
                self.collapse_siblings()
            self.expand()
            self.raise_()

    def handle_collapse(self):
        """Handle the logic for collapsing the item."""
        if self.children:
            for child in self.children:
                self.hide_children(child)
            self.collapse()
            self.raise_()

        if self.root:
            if self.is_expanded():
                self.expand_siblings()



