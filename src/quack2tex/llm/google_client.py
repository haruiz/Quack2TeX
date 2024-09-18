import os
import typing

import tenacity
from google import generativeai as genai

from quack2tex.llm.base import LLMClient, LLMSchema


class GoogleClient(LLMClient):
    """A class for the Google Gemini client."""

    def __init__(self, model_name: str, *args, **kwargs) -> None:
        super().__init__(model_name)
        self.model = genai.GenerativeModel(model_name, *args, **kwargs)
        self._set_api_key()

    @staticmethod
    def _set_api_key() -> None:
        """Configure the API key for the Google Gemini client."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

    @tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(3), reraise=True)
    def ask(self, prompt: str, *args, **kwargs) -> str:
        response = self.model.generate_content(prompt, *args, **kwargs)
        return response.text

    @classmethod
    def list_models(cls) -> typing.List[LLMSchema]:
        cls._set_api_key()
        available_models = genai.list_models()
        return [
            LLMSchema(
                name=model_info.name,
                display_name=model_info.display_name,
                description=model_info.description,
                client="google",
            )
            for model_info in available_models
            if "generateContent" in model_info.supported_generation_methods
        ]
