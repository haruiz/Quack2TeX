import typing
import os
import shutil
import subprocess

import whisper
from google.cloud import texttospeech


class MissingFFmpegError(RuntimeError):
    """Raised when Whisper transcription cannot find a runnable FFmpeg binary."""
    pass


class SpeechProcessor:
    """
    A class that provides speech-to-text (STT) and text-to-speech (TTS) capabilities
    using OpenAI Whisper and Google Cloud Text-to-Speech.
    """

    def __init__(self, whisper_model: str = "medium") -> None:
        """Load the requested Whisper model.

        Args:
            whisper_model: Whisper model name accepted by `whisper.load_model`.
        """
        self.whisper_model = whisper.load_model(whisper_model)
        self._tts_client: texttospeech.TextToSpeechClient | None = None

    @property
    def tts_client(self) -> texttospeech.TextToSpeechClient:
        """Return a lazily initialized Google Text-to-Speech client."""
        if self._tts_client is None:
            self._tts_client = texttospeech.TextToSpeechClient()
        return self._tts_client

    def synthesize_speech(
            self,
            text: str,
            voice_params: texttospeech.VoiceSelectionParams,
            encoding: texttospeech.AudioEncoding = texttospeech.AudioEncoding.MP3
    ) -> bytes:
        """
        Convert input text into speech audio using Google Cloud TTS.

        :param text: The text to convert to speech.
        :param voice_params: Voice configuration (e.g., language and gender).
        :param encoding: Desired audio encoding (default: MP3).
        :return: Audio content in bytes.
        """
        synthesis_input = texttospeech.SynthesisInput(text=text)
        audio_config = texttospeech.AudioConfig(audio_encoding=encoding)

        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )
        return response.audio_content

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio to text using the Whisper model.

        :param audio_path: Path to the audio file to transcribe.
        :return: Transcribed text.
        """
        self.ensure_ffmpeg_available()
        result = self.whisper_model.transcribe(audio_path)
        return result.get("text", "")

    @staticmethod
    def ensure_ffmpeg_available() -> None:
        """Ensure Whisper can execute FFmpeg.

        The configured Preferences path is honored first. When no path is
        configured, common Homebrew/system locations and PATH entries are
        searched, with pyenv shims checked last.

        Raises:
            MissingFFmpegError: If no runnable FFmpeg executable is available.
        """
        install_hint = (
            "On macOS, install it with `brew install ffmpeg`, or add the "
            "directory containing ffmpeg to PATH before launching Quack2Tex."
        )
        configured_path = SpeechProcessor.configured_ffmpeg_path()
        if configured_path:
            if not SpeechProcessor.is_runnable_ffmpeg(configured_path):
                raise MissingFFmpegError(
                    "Whisper requires ffmpeg to transcribe audio, but the configured "
                    f"ffmpeg path could not be executed: {configured_path}. "
                    "Update the FFmpeg Path in Settings, clear it to auto-detect, "
                    f"or install ffmpeg. {install_hint}"
                )
            ffmpeg_path = configured_path
        else:
            ffmpeg_path = SpeechProcessor.find_runnable_ffmpeg()

        if ffmpeg_path is None:
            raise MissingFFmpegError(
                "Whisper requires ffmpeg to transcribe audio, but ffmpeg was not "
                f"found on PATH. {install_hint}"
            )

        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        path_parts = os.environ.get("PATH", "").split(os.pathsep)
        if not path_parts or path_parts[0] != ffmpeg_dir:
            os.environ["PATH"] = os.pathsep.join([ffmpeg_dir, *path_parts])

    @staticmethod
    def configured_ffmpeg_path() -> str:
        """Return the user-configured FFmpeg path from preferences."""
        from quack2tex.preferences import Preferences

        return Preferences.ffmpeg_path()

    @staticmethod
    def is_runnable_ffmpeg(ffmpeg_path: str) -> bool:
        """Check whether a path points to an executable FFmpeg command.

        Args:
            ffmpeg_path: Candidate executable path.

        Returns:
            True when `ffmpeg_path -version` succeeds.
        """
        try:
            subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                check=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return False
        return True

    @staticmethod
    def find_runnable_ffmpeg() -> str | None:
        """Find the first runnable FFmpeg candidate.

        Returns:
            Executable path when found, otherwise None.
        """
        candidates = SpeechProcessor.ffmpeg_candidates()
        for ffmpeg_path in candidates:
            if SpeechProcessor.is_runnable_ffmpeg(ffmpeg_path):
                return ffmpeg_path
        return None

    @staticmethod
    def ffmpeg_candidates() -> list[str]:
        """Build ordered FFmpeg candidate paths.

        Returns:
            Candidate executable paths, preferring real Homebrew/system binaries
            before pyenv shims.
        """
        candidates = []
        for ffmpeg_path in (
            "/opt/homebrew/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/usr/bin/ffmpeg",
        ):
            if os.path.exists(ffmpeg_path) and ffmpeg_path not in candidates:
                candidates.append(ffmpeg_path)

        shim_candidates = []
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for directory in path_dirs:
            if not directory:
                continue
            ffmpeg_path = shutil.which("ffmpeg", path=directory)
            if not ffmpeg_path or ffmpeg_path in candidates:
                continue
            if "/.pyenv/shims/" in ffmpeg_path:
                shim_candidates.append(ffmpeg_path)
                continue
            if ffmpeg_path not in candidates:
                candidates.append(ffmpeg_path)

        for ffmpeg_path in shim_candidates:
            if ffmpeg_path not in candidates:
                candidates.append(ffmpeg_path)

        return candidates

    @staticmethod
    def list_available_whisper_models() -> typing.List[str]:
        """
        List available Whisper models.

        :return: List of available Whisper model names.
        """
        return whisper.available_models()

    def list_available_voices(self) -> dict[str, dict[str, list[str]]]:
        """Fetch available Google Cloud Text-to-Speech voices.

        Returns:
            Mapping of language code to gender to voice names.
        """
        request = texttospeech.ListVoicesRequest()
        response = self.tts_client.list_voices(request=request)

        voices_data = {}
        for voice in response.voices:
            lang_code = voice.language_codes[0]  # Use first language code
            gender = texttospeech.SsmlVoiceGender(voice.ssml_gender).name  # Convert enum to string

            if lang_code not in voices_data:
                voices_data[lang_code] = {}

            if gender not in voices_data[lang_code]:
                voices_data[lang_code][gender] = []

            voices_data[lang_code][gender].append(voice.name)

        return voices_data
