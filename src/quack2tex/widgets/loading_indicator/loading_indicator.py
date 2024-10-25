import io

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QMovie, QCloseEvent, QShowEvent, QShortcut
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PIL import Image
from PySide6.QtCore import QResource

from quack2tex.utils import GuiUtils


class LoadingIndicator(QWidget):
    """
    A loading indicator that displays a GIF animation
    """

    def __init__(self, gif_path, gif_size=QSize(100, 100), parent=None):
        super().__init__(parent)

        self.setWindowTitle("Loading Indicator")
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        resource = QResource(gif_path)
        image_data = resource.data()
        image_bytes = io.BytesIO(image_data)
        gif_img = Image.open(image_bytes)
        gif_full_sz = QSize(gif_img.size[0], gif_img.size[1])
        del gif_img
        target_sz = GuiUtils.calculate_new_size(gif_full_sz, gif_size)
        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: rgba(255, 255, 255, 0)")
        self.label.setFixedSize(target_sz)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(target_sz)
        self.label.setMovie(self.movie)
        # Create a layout and add the QLabel to it
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.adjustSize()

        QShortcut("Ctrl+C", self, self.close)

    def start(self):
        """
        Start the loading animation
        """
        if self.movie.state() == QMovie.NotRunning:
            self.movie.start()

    def stop(self):
        """
        Stop the loading animation
        """
        if self.movie.state() == QMovie.Running:
            self.movie.stop()

    def showEvent(self, e: QShowEvent):
        """
        :param e: QShowEvent
        """
        self.start()
        super().showEvent(e)

    def keyPressEvent(self, event):
        """
        :param event: QKeyEvent
        """
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, e: QCloseEvent):
        """
        :param e: QCloseEvent
        """

        self.stop()

        super().closeEvent(e)
