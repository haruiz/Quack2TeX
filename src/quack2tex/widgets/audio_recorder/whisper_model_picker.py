from quack2tex.pyqt import (
    QComboBox,
)
from .speech_processor import SpeechProcessor


class WhisperPicker(QComboBox):
    """
    A custom combobox widget to list the available microphone devices on the system.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        for model in SpeechProcessor.list_available_whisper_models():
            self.addItem(model, model)
