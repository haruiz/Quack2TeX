import typing
import json
import os
import numpy as np

from quack2tex.pyqt import (
    QWidget,
    QFormLayout,
    QDialog,
    Qt,
    QDialogButtonBox,
    QHBoxLayout,
    QPushButton,
    QThreadPool,
    QVBoxLayout,
    QApplication
)

from quack2tex.utils import Worker
from quack2tex.widgets.audio_recorder.audio_device_picker import AudioDevicePicker
from quack2tex.widgets.audio_recorder.whisper_model_picker import WhisperPicker
from quack2tex.widgets.audio_recorder.audio_recorder import AudioRecorder
from quack2tex.widgets.audio_recorder.speech_processor import SpeechProcessor
import pyqtgraph as pg


class AudioRecorderDialog(QDialog):
    def __init__(self, parent=None, recording_settings_file = "recording_settings.json", recording_audio_file = "recording.wav"):
        super().__init__(parent)
        self.setWindowTitle("Audio Recorder")
        self.setFixedSize(400, 300)

        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)


        # Recording settings
        self.recording_settings_widget = QWidget()
        self.recording_settings_layout = QFormLayout(self.recording_settings_widget)
        self.recording_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.recording_settings_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.devices_combobox = AudioDevicePicker()
        self.recording_settings_layout.addRow("Select Device:", self.devices_combobox)

        self.whisper_model_combobox = WhisperPicker()
        self.recording_settings_layout.addRow("Select Whisper Model:", self.whisper_model_combobox)

        # Action buttons
        self.actions_widget = QWidget()
        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)

        self.start_record_button = QPushButton("Record")
        self.stop_record_button = QPushButton("Stop")
        self.actions_layout.addWidget(self.start_record_button)
        self.actions_layout.addWidget(self.stop_record_button)

        self.start_record_button.clicked.connect(self.start_recording_action)
        self.stop_record_button.clicked.connect(self.stop_recording_action)

        # Save defaults button
        self.btn_save_defaults = QPushButton("Save Defaults")
        self.btn_save_defaults.clicked.connect(self.save_defaults)

        # Waveform visualization
        self.plot_widget = pg.PlotWidget(title="Audio Waveform")
        self.plot_widget.setYRange(-1, 1)
        self.plot_widget.plotItem.hideAxis('left')
        self.plot_widget.plotItem.hideAxis('bottom')
        self.waveform_plot = self.plot_widget.plot(pen='y')
        self.waveform_data = np.zeros(1024)

        # Internal state
        self.audio_recorder = None
        self.recording_audio_file = recording_audio_file
        self.recording_settings_file = recording_settings_file
        self.transcribed_text = None
        self.threadpool = QThreadPool()

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.recording_settings_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.actions_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.btn_save_defaults, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.plot_widget, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.button_box, alignment=Qt.AlignmentFlag.AlignBottom)
        self.setLayout(layout)

        # Load saved defaults
        self.load_defaults()

    def start_recording_action(self):
        self.start_record_button.setEnabled(False)
        self.button_box.setEnabled(False)
        self.audio_recorder = AudioRecorder(self.devices_combobox.current_device())
        self.audio_recorder.data_ready.connect(self.on_data_ready)
        self.audio_recorder.recording_started.connect(self.on_recording_started_handler)
        self.audio_recorder.recording_stopped.connect(self.on_recording_stopped_handler)
        self.audio_recorder.start()

    def stop_recording_action(self):
        if self.audio_recorder:
            self.audio_recorder.stop()

    def on_data_ready(self, data):
        self.waveform_data = np.roll(self.waveform_data, -len(data))
        self.waveform_data[-len(data):] = data
        self.waveform_plot.setData(self.waveform_data)

    def on_recording_started_handler(self):
        self.setWindowTitle("Listening...")

    def on_recording_stopped_handler(self):
        self.setWindowTitle("Recording audio...")
        self.start_record_button.setEnabled(True)
        self.audio_recorder.save_audio(self.recording_audio_file)
        self.setWindowTitle("Recording complete")

        self.button_box.setEnabled(False)
        worker = Worker(self.transcribe_audio, progress_callback=True)
        worker.signals.result.connect(self.transcribe_audio_done)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.threadpool.clear)
        self.threadpool.start(worker)

    def transcribe_audio(self, progress_callback: typing.Callable[[typing.Any], None]):
        progress_callback.emit("Transcribing audio...")
        audio_processor = SpeechProcessor(whisper_model=self.whisper_model_combobox.currentText())
        self.transcribed_text = audio_processor.transcribe_audio(self.recording_audio_file)


    def transcribe_audio_done(self):
        self.setWindowTitle("Transcription complete")
        self.start_record_button.setEnabled(True)
        self.stop_record_button.setEnabled(True)
        self.button_box.setEnabled(True)
        self.accept()

    def update_progress(self, message: str):
        self.setWindowTitle(message)

    def closeEvent(self, event):
        if self.audio_recorder and self.audio_recorder.isRunning():
            self.audio_recorder.stop()
        super().closeEvent(event)

    def accept(self):
        if self.audio_recorder and self.audio_recorder.isRunning():
            self.audio_recorder.stop()
        super().accept()

    def save_defaults(self):
        settings = {
            "device_name": self.devices_combobox.current_device_name(),
            "whisper_model": self.whisper_model_combobox.currentText()
        }
        try:
            with open(self.recording_settings_file, "w") as f:
                json.dump(settings, f, indent=2)
            self.setWindowTitle("Defaults saved.")
        except Exception as e:
            print(f"Error saving settings: {e}")
            self.setWindowTitle("Failed to save settings.")

    def load_defaults(self):
        if not os.path.exists(self.recording_settings_file):
            return
        try:
            with open(self.recording_settings_file, "r") as f:
                settings = json.load(f)

            device_name = settings.get("device_name")
            whisper_model = settings.get("whisper_model")

            if device_name:
                self.devices_combobox.set_device_by_name(device_name)

            if whisper_model:
                self.whisper_model_combobox.setCurrentText(whisper_model)

        except Exception as e:
            print(f"Error loading settings: {e}")
            self.setWindowTitle("Failed to load defaults")


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    win = AudioRecorderDialog()
    if win.exec() == QDialog.DialogCode.Accepted:
        print("Recording accepted: ", win.transcribed_text)
    sys.exit(app.exec())
