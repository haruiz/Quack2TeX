import math
from PySide6.QtCore import (
    Signal,
    QSize,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
)
from PySide6.QtWidgets import QWidget
from .image_button import ImageButton


class FloatingMenu(QWidget):
    """
    A floating menu widget that displays a central button and surrounding item buttons.
    """

    item_clicked = Signal(str, dict)

    def __init__(
        self,
        menu_icon: str,
        central_button_size: QSize = QSize(64, 64),
        item_button_size: QSize = QSize(32, 32),
        start_angle=0,
        end_angle=180,
        parent=None,
    ):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.item_button_size = item_button_size
        self.central_button = ImageButton(menu_icon, central_button_size, self)
        self.central_button.doubleClicked.connect(self.toggle_buttons_visibility)
        self.items_distance_to_center = 100
        self.buttons = []
        self.is_animating = False
        self.start_angle = start_angle
        self.end_angle = end_angle

    def add_menu_item(
        self, item_icon: str, item_value: str, tooltip: str = "", data=None
    ):
        """
        Add a new item to the menu.
        """
        button = ImageButton(item_icon, self.item_button_size, self)
        button.setToolTip(tooltip)
        button.setProperty("value", item_value)
        button.setProperty("data", data)
        button.clicked.connect(self.handle_item_click)
        button.setVisible(False)
        self.buttons.append(button)

    def adjust_widget_size(self):
        """
        Adjust the size of the widget to fit the central and item buttons.
        """
        self.setFixedSize(
            self.items_distance_to_center * 2 + self.item_button_size.width(),
            self.items_distance_to_center * 2 + self.item_button_size.height(),
        )

    def draw_menu(self):
        """
        Draw the menu items around the central button.
        """
        self.adjust_widget_size()
        widget_center = self.geometry().center()
        self.central_button.move(
            widget_center.x() - self.central_button.width() // 2,
            widget_center.y() - self.central_button.height() // 2,
        )
        for button in self.buttons:
            button.resize(self.item_button_size)
            button.move(
                self.central_button.geometry().center().x() - button.width() // 2,
                self.central_button.geometry().center().y() - button.height() // 2,
            )

    def handle_item_click(self):
        """
        Handle the item click event.
        """
        button = self.sender()
        self.item_clicked.emit(button.property("value"), button.property("data"))
        self.toggle_buttons_visibility()

    def toggle_buttons_visibility(self):
        """
        Toggle the visibility of the menu items.
        """

        if self.is_animating:
            return

        self.is_animating = True

        # Safeguard against zero division
        num_buttons = len(self.buttons)
        if num_buttons == 0:
            self.is_animating = False
            return  # No buttons to animate

        angle_range = self.end_angle - self.start_angle
        full_menu = self.start_angle == 0 and self.end_angle == 360
        angle_separation = angle_range / (
            num_buttons if full_menu else max(1, num_buttons - 1)
        )

        center_x = self.central_button.geometry().center().x()
        center_y = self.central_button.geometry().center().y()

        for i, button in enumerate(self.buttons):
            animation_group = QParallelAnimationGroup(self)
            geo_animation = QPropertyAnimation(button, b"geometry")
            geo_animation.setDuration(700)
            geo_animation.setEasingCurve(QEasingCurve.OutBounce)

            if not button.isVisible():
                button.setVisible(True)
                angle = math.radians(self.end_angle + angle_separation * i)
                x = (
                    center_x
                    + self.items_distance_to_center * math.cos(angle)
                    - button.width() // 2
                )
                y = (
                    center_y
                    + self.items_distance_to_center * math.sin(angle)
                    - button.height() // 2
                )
                geo_animation.setStartValue(button.geometry())
                geo_animation.setEndValue(
                    QRect(int(x), int(y), button.width(), button.height())
                )
            else:
                geo_animation.setStartValue(button.geometry())
                geo_animation.setEndValue(
                    QRect(
                        center_x - button.width() // 2,
                        center_y - button.height() // 2,
                        button.width(),
                        button.height(),
                    )
                )
                geo_animation.finished.connect(lambda b=button: b.setVisible(False))

            animation_group.addAnimation(geo_animation)
            animation_group.finished.connect(self.animation_finished)
            animation_group.start()

        self.central_button.raise_()

    def animation_finished(self):
        """
        Slot to be called when the animation is finished.
        """
        self.is_animating = False
