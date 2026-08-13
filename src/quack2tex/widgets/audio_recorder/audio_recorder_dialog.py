import typing
import json
import os
import numpy as np

from quack2tex.pyqt import (
    QColor,
    QFont,
    QWidget,
    QDialog,
    Qt,
    QDialogButtonBox,
    QPushButton,
    QThreadPool,
    QVBoxLayout,
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
    QPoint,
    QSize,
)

from quack2tex.utils import GuiUtils, Worker
from quack2tex.widgets.audio_recorder.audio_device_picker import AudioDevicePicker
from quack2tex.widgets.audio_recorder.whisper_model_picker import WhisperPicker
from quack2tex.widgets.audio_recorder.audio_recorder import AudioRecorder
from quack2tex.widgets.audio_recorder.speech_processor import SpeechProcessor
import pyqtgraph as pg


class AudioRecorderDialog(QDialog):
    def __init__(self, parent=None, recording_settings_file = "recording_settings.json", recording_audio_file = "recording.wav"):
        super().__init__(parent)
        self.setObjectName("voiceInputDialog")
        self.setWindowTitle("Voice input")
        self.setFixedSize(440, 560)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Use Text")
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Dismiss")
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.status_label = QLabel("ready", self)
        self.status_label.setObjectName("voiceStatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("Voice Input", self)
        self.title_label.setObjectName("voiceTitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.Medium)
        self.title_label.setFont(title_font)

        # Recording settings
        self.recording_settings_widget = QWidget()
        self.recording_settings_widget.setMinimumHeight(138)
        self.recording_settings_layout = QGridLayout(self.recording_settings_widget)
        self.recording_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.recording_settings_layout.setHorizontalSpacing(12)
        self.recording_settings_layout.setVerticalSpacing(24)
        self.recording_settings_layout.setColumnStretch(0, 0)
        self.recording_settings_layout.setColumnStretch(1, 1)
        self.recording_settings_layout.setRowMinimumHeight(0, 48)
        self.recording_settings_layout.setRowMinimumHeight(1, 48)

        self.device_label = QLabel("Device")
        self.device_label.setObjectName("voiceFieldLabel")
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.devices_combobox = AudioDevicePicker()
        self.devices_combobox.setMinimumHeight(44)
        self.recording_settings_layout.addWidget(self.device_label, 0, 0)
        self.recording_settings_layout.addWidget(self.devices_combobox, 0, 1)

        self.whisper_label = QLabel("Whisper")
        self.whisper_label.setObjectName("voiceFieldLabel")
        self.whisper_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.whisper_model_combobox = WhisperPicker()
        self.whisper_model_combobox.setMinimumHeight(44)
        self.recording_settings_layout.addWidget(self.whisper_label, 1, 0)
        self.recording_settings_layout.addWidget(self.whisper_model_combobox, 1, 1)

        # Action buttons
        self.actions_widget = QWidget()
        self.actions_widget.setFixedHeight(54)
        self.actions_layout = QGridLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setHorizontalSpacing(10)

        self.start_record_button = QPushButton("Record")
        self.start_record_button.setObjectName("voicePrimaryButton")
        self.start_record_button.setIcon(self.control_icon("record", QColor(52, 211, 153)))
        self.start_record_button.setIconSize(QSize(18, 18))
        self.stop_record_button = QPushButton("Stop")
        self.stop_record_button.setObjectName("voiceSecondaryButton")
        self.stop_record_button.setIcon(self.control_icon("stop", QColor(248, 113, 113)))
        self.stop_record_button.setIconSize(QSize(18, 18))
        self.stop_record_button.setEnabled(False)
        self.actions_layout.addWidget(self.start_record_button, 0, 0)
        self.actions_layout.addWidget(self.stop_record_button, 0, 1)

        self.start_record_button.clicked.connect(self.start_recording_action)
        self.stop_record_button.clicked.connect(self.stop_recording_action)

        # Save defaults button
        self.btn_save_defaults = QPushButton("Save Defaults")
        self.btn_save_defaults.setObjectName("voiceGhostButton")
        self.btn_save_defaults.clicked.connect(self.save_defaults)

        # Waveform visualization
        self.waveform_frame = QFrame()
        self.waveform_frame.setObjectName("voiceWaveformFrame")
        self.waveform_frame.setFixedHeight(104)
        waveform_layout = QVBoxLayout(self.waveform_frame)
        waveform_layout.setContentsMargins(12, 10, 12, 12)
        waveform_layout.setSpacing(8)
        self.waveform_label = QLabel("Audio waveform")
        self.waveform_label.setObjectName("voiceWaveformLabel")
        self.waveform_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setObjectName("voiceWaveformPlot")
        self.plot_widget.setMinimumHeight(54)
        self.plot_widget.setYRange(-1, 1)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.setBackground(QColor(8, 13, 26))
        self.plot_widget.plotItem.hideAxis('left')
        self.plot_widget.plotItem.hideAxis('bottom')
        self.plot_widget.plotItem.setContentsMargins(0, 0, 0, 0)
        self.waveform_plot = self.plot_widget.plot(pen=pg.mkPen(QColor(14, 165, 233), width=2))
        self.waveform_data = np.zeros(1024)
        waveform_layout.addWidget(self.waveform_label)
        waveform_layout.addWidget(self.plot_widget)

        # Internal state
        self.audio_recorder = None
        self.recording_audio_file = recording_audio_file
        self.recording_settings_file = recording_settings_file
        self.transcribed_text = None
        self.threadpool = QThreadPool()
        self._recording_failed = False
        self._is_transcribing = False

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 24, 28, 26)
        layout.setSpacing(12)
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.recording_settings_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.actions_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.btn_save_defaults, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.waveform_frame, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.button_box, alignment=Qt.AlignmentFlag.AlignBottom)
        self.setLayout(layout)
        self.apply_style()

        # Load saved defaults
        self.load_defaults()

    def apply_style(self) -> None:
        self.setStyleSheet("""
            QDialog#voiceInputDialog {
                background: transparent;
            }
            QLabel {
                color: rgb(226, 232, 240);
                letter-spacing: 0px;
            }
            QLabel#voiceStatusLabel {
                color: rgb(56, 189, 248);
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
            }
            QLabel#voiceTitleLabel {
                color: rgb(248, 250, 252);
            }
            QLabel#voiceWaveformLabel {
                color: rgba(226, 232, 240, 175);
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#voiceFieldLabel {
                color: rgb(203, 213, 225);
                font-size: 13px;
            }
            QFrame#voiceWaveformFrame {
                background: rgba(15, 23, 42, 235);
                border: 1px solid rgba(71, 85, 105, 210);
                border-radius: 10px;
            }
            QComboBox {
                min-height: 34px;
                color: rgb(248, 250, 252);
                background: rgba(15, 23, 42, 245);
                border: 1px solid rgba(71, 85, 105, 220);
                border-radius: 8px;
                padding: 4px 12px;
            }
            QComboBox:focus {
                border: 1px solid rgba(14, 165, 233, 210);
            }
            QComboBox::drop-down {
                border: 0px;
                width: 24px;
            }
            QPushButton {
                min-height: 36px;
                color: rgb(248, 250, 252);
                background: rgba(15, 23, 42, 245);
                border: 1px solid rgba(71, 85, 105, 220);
                border-radius: 8px;
                padding: 4px 14px;
                font-weight: 600;
            }
            QPushButton#voicePrimaryButton {
                background: rgb(14, 165, 233);
                border-color: rgb(14, 165, 233);
                color: white;
            }
            QPushButton#voiceSecondaryButton {
                border-color: rgba(148, 163, 184, 145);
            }
            QPushButton#voiceGhostButton {
                color: rgb(226, 232, 240);
                background: rgba(30, 41, 59, 240);
            }
            QPushButton:hover {
                background: rgba(51, 65, 85, 245);
            }
            QPushButton#voicePrimaryButton:hover {
                background: rgb(2, 132, 199);
                border-color: rgb(2, 132, 199);
            }
            QPushButton:disabled {
                color: rgba(148, 163, 184, 115);
                border-color: rgba(100, 116, 139, 70);
                background: rgba(15, 23, 42, 105);
            }
        """)

    def control_icon(self, name: str, color: QColor):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(color, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(color)

        if name == "record":
            painter.drawEllipse(QPoint(12, 12), 6, 6)
        elif name == "stop":
            painter.drawRoundedRect(7, 7, 10, 10, 2, 2)

        painter.end()
        return QIcon(pixmap)

    def start_recording_action(self):
        self._recording_failed = False
        self.transcribed_text = None
        self.start_record_button.setEnabled(False)
        self.stop_record_button.setEnabled(True)
        self.btn_save_defaults.setEnabled(False)
        self.button_box.setEnabled(False)
        try:
            self.audio_recorder = AudioRecorder(self.devices_combobox.current_device())
            self.audio_recorder.data_ready.connect(self.on_data_ready)
            self.audio_recorder.recording_started.connect(self.on_recording_started_handler)
            self.audio_recorder.recording_stopped.connect(self.on_recording_stopped_handler)
            self.audio_recorder.recording_error.connect(self.on_recording_error_handler)
            self.audio_recorder.start()
        except Exception as error:
            self.fail_task("Recording failed", str(error))

    def stop_recording_action(self):
        if self.audio_recorder:
            self.stop_record_button.setEnabled(False)
            self.update_progress("Saving audio...")
            self.audio_recorder.stop()

    def on_data_ready(self, data):
        self.waveform_data = np.roll(self.waveform_data, -len(data))
        self.waveform_data[-len(data):] = data
        self.waveform_plot.setData(self.waveform_data)

    def on_recording_started_handler(self):
        self.update_progress("Listening...")

    def on_recording_stopped_handler(self):
        self.stop_record_button.setEnabled(False)
        if self._recording_failed:
            return
        self.update_progress("Saving audio...")
        self.start_record_button.setEnabled(True)
        try:
            self.audio_recorder.save_audio(self.recording_audio_file)
        except Exception as error:
            self.fail_task("Recording failed", str(error))
            return
        self.update_progress("Recording complete")

        self.button_box.setEnabled(False)
        self._is_transcribing = True
        worker = Worker(self.transcribe_audio, progress_callback=True)
        worker.signals.result.connect(self.transcribe_audio_done)
        worker.signals.error.connect(self.transcribe_audio_error)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.threadpool.clear)
        self.threadpool.start(worker)

    def on_recording_error_handler(self, message: str) -> None:
        self.fail_task("Recording failed", message)

    def transcribe_audio(self, progress_callback: typing.Callable[[typing.Any], None]):
        progress_callback.emit("Transcribing audio...")
        audio_processor = SpeechProcessor(whisper_model=self.whisper_model_combobox.currentText())
        self.transcribed_text = audio_processor.transcribe_audio(self.recording_audio_file)


    def transcribe_audio_done(self):
        self._is_transcribing = False
        self.update_progress("Transcription complete")
        self.start_record_button.setEnabled(True)
        self.stop_record_button.setEnabled(True)
        self.button_box.setEnabled(True)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        self.accept()

    def transcribe_audio_error(self, error_info: tuple) -> None:
        _, error, _ = error_info
        self._is_transcribing = False
        self.fail_task("Transcription failed", str(error))

    def fail_task(self, title: str, message: str) -> None:
        self._recording_failed = True
        if self.audio_recorder and self.audio_recorder.isRunning():
            self.audio_recorder.stop()
        self.update_progress(title)
        self.start_record_button.setEnabled(True)
        self.stop_record_button.setEnabled(False)
        self.btn_save_defaults.setEnabled(True)
        self.button_box.setEnabled(True)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        GuiUtils.show_error(f"{title}: {message}")

    def update_progress(self, message: str):
        self.setWindowTitle(message)
        self.status_label.setText(message)
        self.update()

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
            self.status_label.setText("Defaults saved")
        except Exception as e:
            print(f"Error saving settings: {e}")
            self.fail_task("Failed to save settings", str(e))

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
            self.fail_task("Failed to load defaults", str(e))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(5, 5, -5, -5)
        painter.setBrush(QColor(15, 23, 42, 248))
        painter.setPen(QPen(QColor(51, 65, 85, 235), 1.2))
        painter.drawRoundedRect(rect, 18, 18)
        super().paintEvent(event)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    win = AudioRecorderDialog()
    if win.exec() == QDialog.DialogCode.Accepted:
        print("Recording accepted: ", win.transcribed_text)
    sys.exit(app.exec())
