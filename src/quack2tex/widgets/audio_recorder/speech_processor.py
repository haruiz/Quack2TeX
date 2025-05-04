import typing
import whisper
from google.cloud import texttospeech


class SpeechProcessor:
    """
    A class that provides speech-to-text (STT) and text-to-speech (TTS) capabilities
    using OpenAI Whisper and Google Cloud Text-to-Speech.
    """

    def __init__(self,whisper_model: str = "medium"):
        self.whisper_model = whisper.load_model(whisper_model)
        self.tts_client = texttospeech.TextToSpeechClient()

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
        result = self.whisper_model.transcribe(audio_path)
        return result.get("text", "")

    @staticmethod
    def list_available_whisper_models() -> typing.List[str]:
        """
        List available Whisper models.

        :return: List of available Whisper model names.
        """
        return whisper.available_models()

    def list_available_voices(self):
        """Fetch all available voices from Google Cloud."""
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
