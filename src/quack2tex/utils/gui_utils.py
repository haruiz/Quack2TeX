import mss
from PIL import Image
from PySide6.QtCore import QSize, QObject, QRect
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QLayout


class GuiUtils:
    """
    Utility functions for the GUI.
    """

    @classmethod
    def clear_layout(cls, layout: QLayout):
        """
        clear a pyqt layout
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


    @staticmethod
    def get_current_monitor_index(widget: QWidget) -> int:
        """
        Get the index of the monitor where the widget is located.
        :param widget: The widget whose monitor index is needed.
        :return: Index of the monitor containing the widget.
        """
        window_geometry = widget.frameGeometry()
        screens = QApplication.screens()
        for i, screen in enumerate(screens):
            if screen.geometry().contains(window_geometry.topLeft()):
                return i
        return -1  # Return -1 if no monitor is found (edge case).

    @staticmethod
    def get_current_monitor_geometry(widget: QWidget) -> QRect:
        """
        Get the geometry of the monitor where the widget is located.
        :param widget: The widget whose monitor geometry is needed.
        :return: Geometry of the monitor containing the widget.
        """
        current_monitor_index = GuiUtils.get_current_monitor_index(widget)
        return QApplication.screens()[current_monitor_index].availableGeometry()


    @staticmethod
    def get_screen_capture_image(screen_region, monitor_index):
        """
        Capture the screen region
        :param screen_region:
        :param monitor_index:
        :return:
        """
        # TODO: Add support for multiple monitors and DPI scaling factors

        with mss.mss() as sct:
            monitor = {
                "top": screen_region[1],
                "left": screen_region[0],
                "width": screen_region[2],
                "height": screen_region[3],
            }
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.format = "PNG"
            return img

    @staticmethod
    def move_window_to_center(window: QWidget):
        """
        Move the window to the center of the screen.
        :param window: The window to move.
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = screen_geometry.width() // 2 - window.width() // 2
        y = screen_geometry.height() // 2 - window.height() // 2
        window.move(x, y)

    @staticmethod
    def move_window_to_top_center(widget: QWidget):
        """
        Move the window to the top center of the screen.
        :param widget: The widget to move.
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = screen_geometry.width() // 2 - widget.width() // 2
        y = screen_geometry.top()
        widget.move(x, y)

    @classmethod
    def move_widget_to_center(cls, widget: QWidget):
        """
        Center the widget on its current screen.
        :param widget: The widget to move.
        """
        screen_geometry = cls.get_current_monitor_geometry(widget)
        x = screen_geometry.center().x() - widget.width() // 2
        y = screen_geometry.center().y() - widget.height() // 2
        widget.move(x, y)

    @classmethod
    def move_widget_to_widget_bottom(cls, widget: QWidget, parent_widget: QWidget):
        """
        Move the widget to the bottom center of the parent widget.
        :param widget: The widget to move.
        :param parent_widget: The parent widget used as reference.
        """
        x = parent_widget.x() + (parent_widget.width() - widget.width()) // 2
        y = parent_widget.y() + parent_widget.height() - widget.height()
        widget.move(x, y)

    @staticmethod
    def calculate_new_size(image_sz: QSize, target_sz: QSize) -> QSize:
        """
        Calculate the new size of an image to fit into a target rectangle while preserving the aspect ratio.
        :param image_sz: The size of the image.
        :param target_sz: The size of the target rectangle.
        :return: The new QSize with the aspect ratio preserved.
        """
        image_aspect_ratio = image_sz.width() / image_sz.height()
        target_aspect_ratio = target_sz.width() / target_sz.height()

        if image_aspect_ratio > target_aspect_ratio:
            new_width = target_sz.width()
            new_height = int(new_width / image_aspect_ratio)
        else:
            new_height = target_sz.height()
            new_width = int(new_height * image_aspect_ratio)

        return QSize(new_width, new_height)

    @classmethod
    def move_widget_to_center_top(cls, widget: QWidget):
        """
        Center the widget at the top of its current screen.
        :param widget: The widget to move.
        """
        screen_geometry = cls.get_current_monitor_geometry(widget)
        x = screen_geometry.center().x() - widget.width() // 2
        y = screen_geometry.top()
        widget.move(x, y)

    @classmethod
    def move_widget_to_center_bottom(cls, widget: QWidget):
        """
        Center the widget at the bottom of its current screen.
        :param widget: The widget to move.
        """
        screen_geometry = cls.get_current_monitor_geometry(widget)
        x = screen_geometry.center().x() - widget.width() // 2
        y = screen_geometry.bottom() - widget.height()
        widget.move(x, y)



    @staticmethod
    def get_clipboard_text():
        """
        Get the text from the clipboard.
        :return: The text from the clipboard.
        """
        clipboard = QApplication.clipboard()
        return clipboard.text()

    @staticmethod
    def bind(objectName, propertyName, propertyType):
        """
        Bind a property of a widget to a property of the parent widget.
        :param objectName:
        :param propertyName:
        :param propertyType:
        :return:
        """
        def getter(self):
            widget = self.findChild(QObject, objectName)
            prop_value = widget.property(propertyName)
            return propertyType(prop_value)

        def setter(self, value):
            self.findChild(QObject, objectName).setProperty(propertyName, value)

        return property(getter, setter)


    @staticmethod
    def show_error(message: str):
        """
        Show an error message dialog.
        :param message: The error message to display.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.exec()

    @staticmethod
    def show_info(message: str):
        """
        Show an information message dialog.
        :param message: The information message to display.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle("Information")
        msg.exec()


