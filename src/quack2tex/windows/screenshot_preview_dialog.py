from io import BytesIO

from PIL.Image import Image as PILImage

from quack2tex.pyqt import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPixmap,
    QVBoxLayout,
    Qt,
)


class ScreenshotPreviewDialog(QDialog):
    """
    Confirmation dialog shown before a screen capture is sent to a model.
    """

    def __init__(self, image: PILImage, parent=None):
        super().__init__(parent)
        self.setObjectName("screenshotPreviewDialog")
        self.setWindowTitle("Confirm Screenshot")
        self.setMinimumSize(720, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        preview = QLabel(self)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setMinimumSize(680, 420)
        preview.setScaledContents(False)

        buffer = BytesIO()
        image.save(buffer, format=image.format or "PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        preview.setPixmap(
            pixmap.scaled(
                preview.minimumSize(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        layout.addWidget(preview)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Send")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
