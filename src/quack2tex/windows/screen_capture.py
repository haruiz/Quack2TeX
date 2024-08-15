from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtWidgets import QDialog, QRubberBand


class ScreenCaptureWindow(QDialog):
    """
    A semi-transparent window that allows the user to select a region to capture
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Region to Capture")
        self.setWindowOpacity(0.3)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.selected_region = None

    def mousePressEvent(self, event):
        """
        Start the rubber band selection on mouse press
        :param event:
        :return:
        """
        self.start_point = event.pos()
        self.rubber_band.setGeometry(QRect(self.start_point, QSize()))
        self.rubber_band.show()

    def mouseMoveEvent(self, event):
        """
        Update the rubber band selection on mouse move
        :param event:
        :return:
        """
        self.rubber_band.setGeometry(QRect(self.start_point, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        """
        Capture the selected region on mouse release
        :param event:
        :return:
        """
        self.end_point = event.pos()
        self.selected_region = self.capture_region()
        self.close()

    def keyPressEvent(self, event):
        """
        Close the window on escape key press
        :param event:
        :return:
        """
        if event.key() == Qt.Key_Escape:
            self.selected_region = None
            self.close()

    def capture_region(self):
        """
        Capture the selected region
        :return:
        """
        x1 = min(self.start_point.x(), self.end_point.x())
        y1 = min(self.start_point.y(), self.end_point.y())
        x2 = max(self.start_point.x(), self.end_point.x())
        y2 = max(self.start_point.y(), self.end_point.y())

        # # relative to the screen
        # left_percent = x1 / self.screen().geometry().width()
        # top_percent = y1 / self.screen().geometry().height()
        # width_percent = (x2 - x1) / self.screen().geometry().width()
        # height_percent = (y2 - y1) / self.screen().geometry().height()

        return (x1, y1, x2 - x1, y2 - y1)
