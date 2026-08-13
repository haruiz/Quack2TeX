import math

from quack2tex.preferences import Preferences
from quack2tex.pyqt import (
    QGraphicsDropShadowEffect,
    QPainter,
    QPen,
    QRadialGradient,
    QRect,
    QColor,
    QEvent,
    QTimer,
    QSize,
    QParallelAnimationGroup,
    QGraphicsOpacityEffect,
    QPropertyAnimation,
    QPoint,
    QEasingCurve,
    Signal,
    Qt
)
from quack2tex.widgets import ImageButton


class FloatingMenuItem(ImageButton):
    """
    A floating menu item that displays an icon and can have children items.
    """
    on_hold = Signal()
    expanded = Signal()
    collapsed = Signal()

    def __init__(
        self,
        icon_path: str,
        icon_size: QSize,
        distance_to_center=100,
        start_angle=0,
        end_angle=360,
        root=None,
        parent=None,
        data=None,
        on_hold_timeout=1000,
        icon_scale: float = 0.78,
    ):

        super().__init__(icon_path, icon_size, parent)
        button_padding = max(16, icon_size.width() // 3)
        self.setObjectName("floatingMenuItem")
        self._menu_icon_size = QSize(
            max(24, int(icon_size.width() * icon_scale)),
            max(24, int(icon_size.height() * icon_scale)),
        )
        self._trimmed_icon_pixmap = None
        self.setIconSize(self._menu_icon_size)
        self.setStyleSheet("""
            QPushButton#floatingMenuItem {
                background: transparent;
                border: none;
                padding: 0;
            }
        """)
        self.setFixedSize(
            icon_size.width() + button_padding,
            icon_size.height() + button_padding,
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.distance_to_center = distance_to_center
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.children = []
        self.root = root
        self.clicked.connect(self.addGlowEffect)
        self.data = data
        self._expanded = False
        self._collapsed = True
        self._animating = False
        self._active_animation_groups = []
        self._base_glow_radius = 22
        self._hover_glow_radius = 36
        self._click_glow_radius = 56
        self._hovered = False
        self._glow_animation = None
        self._glow_restore_timer = QTimer(self)
        self._glow_restore_timer.setSingleShot(True)
        self._glow_restore_timer.timeout.connect(self.restoreGlowEffect)
        self.installEventFilter(self)
        self.applyGlowEffect()

        self.hold_timer = QTimer(self)
        self.hold_timer.setInterval(on_hold_timeout)  # 2000 ms = 2 seconds
        self.hold_timer.setSingleShot(True)
        self.hold_timer.timeout.connect(self.on_hold_handler)

    def theme_colors(self) -> dict[str, QColor]:
        theme = Preferences.theme()
        palettes = {
            "neon": {
                "glow": QColor(74, 222, 255, 190),
                "ring": QColor(56, 189, 248, 150),
                "ring_active": QColor(125, 211, 252, 210),
                "inner": QColor(30, 41, 59, 220),
                "inner_active": QColor(56, 189, 248, 92),
            },
            "glass": {
                "glow": QColor(255, 255, 255, 145),
                "ring": QColor(226, 232, 240, 135),
                "ring_active": QColor(255, 255, 255, 210),
                "inner": QColor(51, 65, 85, 205),
                "inner_active": QColor(148, 163, 184, 110),
            },
            "minimal": {
                "glow": QColor(148, 163, 184, 110),
                "ring": QColor(100, 116, 139, 130),
                "ring_active": QColor(203, 213, 225, 180),
                "inner": QColor(15, 23, 42, 230),
                "inner_active": QColor(30, 41, 59, 190),
            },
            "classic": {
                "glow": QColor(250, 204, 21, 155),
                "ring": QColor(234, 179, 8, 160),
                "ring_active": QColor(253, 224, 71, 220),
                "inner": QColor(30, 41, 59, 220),
                "inner_active": QColor(250, 204, 21, 100),
            },
        }
        return palettes.get(theme, palettes["neon"])

    def paintEvent(self, event):
        """
        Paint a glassy circular target behind the icon.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        inset = 5
        rect = self.rect().adjusted(inset, inset, -inset, -inset)
        center = rect.center()
        radius = max(rect.width(), rect.height()) / 2

        gradient = QRadialGradient(float(center.x()), float(center.y()), radius)
        colors = self.theme_colors()
        if self.is_expanded() or self._hovered:
            gradient.setColorAt(0.0, colors["inner_active"])
            gradient.setColorAt(0.72, QColor(15, 23, 42, 225))
            ring_color = colors["ring_active"]
        else:
            gradient.setColorAt(0.0, colors["inner"])
            gradient.setColorAt(0.72, QColor(2, 6, 23, 214))
            ring_color = colors["ring"]

        gradient.setColorAt(1.0, QColor(15, 23, 42, 170))
        painter.setBrush(gradient)
        painter.setPen(QPen(ring_color, 1.5))
        painter.drawEllipse(rect)

        highlight_rect = rect.adjusted(6, 5, -6, -rect.height() // 2)
        painter.setBrush(QColor(255, 255, 255, 42))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(highlight_rect)

        icon_pixmap = self.trimmed_icon_pixmap().scaled(
            self._menu_icon_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        icon_rect = QRect(
            center.x() - icon_pixmap.width() // 2,
            center.y() - icon_pixmap.height() // 2,
            icon_pixmap.width(),
            icon_pixmap.height(),
        )
        painter.drawPixmap(icon_rect, icon_pixmap)

    def trimmed_icon_pixmap(self):
        """
        Crop transparent padding from source icons so visible artwork centers correctly.
        """
        if self._trimmed_icon_pixmap is not None:
            return self._trimmed_icon_pixmap

        source_size = QSize(
            max(256, self.iconSize().width() * 5),
            max(256, self.iconSize().height() * 5),
        )
        pixmap = self.icon().pixmap(source_size)
        image = pixmap.toImage()

        min_x = image.width()
        min_y = image.height()
        max_x = -1
        max_y = -1
        for y in range(image.height()):
            for x in range(image.width()):
                if QColor(image.pixel(x, y)).alpha() > 8:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        if max_x >= min_x and max_y >= min_y:
            self._trimmed_icon_pixmap = pixmap.copy(
                min_x,
                min_y,
                max_x - min_x + 1,
                max_y - min_y + 1,
            )
        else:
            self._trimmed_icon_pixmap = pixmap
        return self._trimmed_icon_pixmap

    @property
    def data(self):
        return self.property("data")

    @data.setter
    def data(self, data):
        self.setProperty("data", data)

    def mousePressEvent(self, event):
        """
        Triggered when the user presses the mouse button
        :param e:
        :return:
        """
        # Propagate the event to the parent window
        if self.window() is not None:
            self.window().mousePressEvent(event)

        if event.button() == Qt.MouseButton.LeftButton and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.hold_timer.start()

        super().mousePressEvent(event)


    def mouseReleaseEvent(self, e):
        """
        Triggered when the user releases the mouse button
        :param e:
        :return:
        """
        # Propagate the event to the parent window
        if self.window() is not None:
            self.window().mouseReleaseEvent(e)
        # Stop the hold timer if the mouse is released before 2 seconds
        if self.hold_timer.isActive():
            self.hold_timer.stop()
        super().mouseReleaseEvent(e)

    def on_hold_handler(self):
        """
        Function dispatched when the widget is held for the specified duration.
        """
        self.on_hold.emit()


    def applyGlowEffect(self, blur_radius: int = None):
        """
        Apply the persistent menu item glow.
        """
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(blur_radius or self._base_glow_radius)
        glow.setColor(self.theme_colors()["glow"])
        glow.setOffset(0, 0)
        self._glow_effect = glow
        self.setGraphicsEffect(self._glow_effect)

    def animateGlow(self, blur_radius: int, duration: int = 160):
        """
        Animate the current glow blur radius.
        """
        if not isinstance(self.graphicsEffect(), QGraphicsDropShadowEffect):
            self.applyGlowEffect()

        self._glow_restore_timer.stop()
        self._glow_animation = QPropertyAnimation(self.graphicsEffect(), b"blurRadius", self)
        self._glow_animation.setStartValue(self.graphicsEffect().blurRadius())
        self._glow_animation.setEndValue(blur_radius)
        self._glow_animation.setDuration(duration)
        self._glow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._glow_animation.start()

    def addGlowEffect(self):
        """
        Pulse the glow when the menu item is clicked.
        """
        self.animateGlow(self._click_glow_radius, 120)
        self._glow_restore_timer.start(260)

    def restoreGlowEffect(self):
        """
        Restore the steady glow after hover/click feedback.
        """
        target_radius = self._hover_glow_radius if self.underMouse() else self._base_glow_radius
        self.animateGlow(target_radius, 180)

    def removeGlowEffect(self):
        """
        Restore the base glow instead of removing visual depth.
        """
        self.animateGlow(self._base_glow_radius, 180)

    def eventFilter(self, watched, event):
        if watched is self:
            if event.type() == QEvent.Type.Enter:
                self._hovered = True
                self.update()
                self.animateGlow(self._hover_glow_radius)
            elif event.type() == QEvent.Type.Leave:
                self._hovered = False
                self.update()
                self.animateGlow(self._base_glow_radius)
        return super().eventFilter(watched, event)

    def fade(self):
        """
        Fade the button
        :return:
        """
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
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
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.finished.connect(self.applyGlowEffect)
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

    def _start_animation_group(self, animation_group, finished_callback, mark_animating: bool = True):
        """
        Keep animation groups alive until Qt emits finished.
        """
        self._active_animation_groups.append(animation_group)
        if mark_animating:
            self._animating = True

        def on_finished():
            try:
                finished_callback()
            finally:
                if mark_animating:
                    self._animating = False
                if animation_group in self._active_animation_groups:
                    self._active_animation_groups.remove(animation_group)
                animation_group.deleteLater()

        animation_group.finished.connect(on_finished)
        animation_group.start()

    def expand(self):
        """
        Expand the item and show its children with animation.
        :return:
        """
        if self._animating or self.is_expanded() or not self.children:
            return

        self.raise_()
        center = self.geometry().center()
        num_children = len(self.children)
        angles_rad = self.get_items_angles(num_children)
        target_positions = []
        for i, child in enumerate(self.children):
            x = math.ceil(center.x() + self.distance_to_center * math.cos(angles_rad[i]) - child.width() // 2)
            y = math.ceil(center.y() + self.distance_to_center * math.sin(angles_rad[i]) - child.height() // 2)
            target_positions.append((child, QPoint(x, y)))

        menu = self.parentWidget()
        if menu is not None and hasattr(menu, "prepare_expand_bounds"):
            menu.prepare_expand_bounds(self, target_positions)
            center = self.geometry().center()
            angles_rad = self.get_items_angles(num_children)
            target_positions = []
            for i, child in enumerate(self.children):
                x = math.ceil(center.x() + self.distance_to_center * math.cos(angles_rad[i]) - child.width() // 2)
                y = math.ceil(center.y() + self.distance_to_center * math.sin(angles_rad[i]) - child.height() // 2)
                target_positions.append((child, QPoint(x, y)))

        animation_group = QParallelAnimationGroup(self)
        for child, target_position in target_positions:
            child.move(QPoint(center.x() - child.width() // 2, center.y() - child.height() // 2))
            child.show()
            child.applyGlowEffect()
            child.raise_()

            anim = QPropertyAnimation(child, b"pos")
            anim.setStartValue(child.pos())
            anim.setEndValue(target_position)
            anim.setDuration(260)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation_group.addAnimation(anim)

        self._collapsed = False
        self._start_animation_group(animation_group, self.expand_animation_group_finished)

    def expand_animation_group_finished(self):
        """
        Handle the animation group finished event
        :return:
        """
        self._expanded = True
        self._collapsed = False
        self.update()
        self.raise_()
        self.expanded.emit()

    def collapse(self):
        """
        Collapse the item and hide its children with animation.
        :return:
        """

        if self._animating or self.is_collapsed() or not self.children:
            return

        center = self.geometry().center()
        animation_group = QParallelAnimationGroup(self)

        for child in self.children:
            anim = QPropertyAnimation(child, b"pos")
            anim.setStartValue(child.pos())
            anim.setEndValue(QPoint(center.x() - child.width() // 2, center.y() - child.height() // 2))
            anim.setDuration(220)
            anim.setEasingCurve(QEasingCurve.Type.InCubic)
            animation_group.addAnimation(anim)

        self._expanded = False
        self._start_animation_group(animation_group, self.collapse_animation_group_finished)

    def collapse_animation_group_finished(self):
        """
        Handle the animation group finished event
        :return:
        """
        for child in self.children:
            child.hide()
        self._expanded = False
        self._collapsed = True
        self.update()
        self.collapsed.emit()
        if self.root:
            self.root.raise_()
        else:
            self.raise_()

    def hide_children(self, parent_item: "FloatingMenuItem"):
        """
        Hide the children of a given item.
        :param parent_item:
        :return:
        """
        try:
            for child in parent_item.children:
                child.hide()
                child._expanded = False
                child._collapsed = True
                if child.children:
                    self.hide_children(child)
        except Exception as e:
            print(e)

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
            anim.setStartValue(sibling.pos())
            anim.setEndValue(QPoint(center.x() - sibling.width() // 2, center.y() - sibling.height() // 2))
            anim.setDuration(180)
            anim.setEasingCurve(QEasingCurve.Type.InCubic)
            anim.finished.connect(sibling.hide)
            group.addAnimation(anim)

        self._start_animation_group(group, lambda: None, mark_animating=False)

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
            x = math.ceil(root_center.x() + self.root.distance_to_center * math.cos(angles_rad[i]) - sibling.width() // 2)
            y = math.ceil(root_center.y() + self.root.distance_to_center * math.sin(angles_rad[i]) - sibling.height() // 2)
            sibling.move(x, y)
            sibling.setVisible(True)
            sibling.unfade()

    def toggle(self):
        """
        Toggle the item between expanded and collapsed states.
        :return:
        """
        if self._animating:
            return
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

        if self.root:
            if self.is_expanded():
                self.expand_siblings()
