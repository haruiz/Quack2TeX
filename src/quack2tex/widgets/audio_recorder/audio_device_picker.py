import sounddevice as sd
from quack2tex.pyqt import (
    QComboBox,
)


def list_mic_devices():
    """
    Returns a list of microphone devices available on the system.

    Each entry in the list is a dictionary containing the index and name of the microphone.
    """
    devices = sd.query_devices()
    mic_devices = []
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:  # Filter input devices
            mic_devices.append(device)
    return mic_devices

class AudioDevicePicker(QComboBox):
    """
    A custom combobox widget to list the available microphone devices on the system.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        for device in list_mic_devices():
            self.addItem(device["name"], device)

    def current_device(self):
        """
        Returns the currently selected microphone device.
        :return:
        """
        return self.currentData()

    def current_device_name(self):
        """
        Returns the currently selected microphone device.
        :return:
        """
        return self.currentData()["name"]

    def set_device_by_name(self, name: str):
        index = self.findText(name)
        if index != -1:
            self.setCurrentIndex(index)
