
import numpy as np
import sounddevice as sd
import wave
import typing
from pathlib import Path
from quack2tex.pyqt import (
    QThread,
    Signal
)

# Worker Thread for Recording
class AudioRecorder(QThread):
    """
    A worker thread to record audio from the microphone.
    """
    data_ready = Signal(np.ndarray)
    recording_started = Signal()
    recording_stopped = Signal()

    def __init__(self, audio_device_info: dict, channels: int =1, sample_width: int =2, audio_chunk_size: int =512):
        super().__init__()
        self.is_recording = False
        self.audio_device_info = audio_device_info
        self.audio_stream = None
        self.audio_chunk_size = audio_chunk_size
        self.audio_data_buffer = []  # Buffer to store audio data
        self.channels = channels
        self.sample_width = sample_width
        self.sample_rate = int(audio_device_info['default_samplerate'])



    def run(self):
        """
        The main thread function that records audio from the microphone.
        :return:
        """
        self.is_recording = True
        self.recording_started.emit()
        self.audio_data_buffer = []  # Reset audio data buffer
        try:
            # Open the audio stream
            with sd.InputStream(
                samplerate=self.sample_rate,
                device=self.audio_device_info['index'],
                channels=self.channels,
                callback=self.audio_callback,
                blocksize=self.audio_chunk_size
            ):
                while self.is_recording:
                    sd.sleep(100)
        finally:
            self.recording_stopped.emit()

    def audio_callback(self, indata, frames, time, status):
        """
        The audio callback function that is called by the audio stream.
        :param indata:
        :param frames:
        :param time:
        :param status:
        :return:
        """
        if self.is_recording:
            data_chunk = indata.copy()
            self.data_ready.emit(data_chunk[:, 0])  # Send audio data for visualization
            self.audio_data_buffer.append(data_chunk)  # Append audio data to buffer

    def stop(self):
        """
        Stop the audio recording process.
        :return:
        """
        self.is_recording = False

    def save_audio(self, output_file : typing.Union[str, Path]):
        """
        Save the recorded audio to a file
        :param output_file: The output file path
        :return:
        """
        with wave.open(output_file, "wb") as wf:
            wf.setnchannels(self.channels)  # Mono audio
            wf.setsampwidth(self.sample_width)  # Sample width in bytes (int16 = 2 bytes)
            wf.setframerate(self.sample_rate)
            int_data = np.concatenate(self.audio_data_buffer)[:, 0]
            int_data = np.int16(int_data * 32767)  # Scale float32 to int16 range
            wf.writeframes(int_data.tobytes())

