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

    @tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(3))
    def ask(self, prompt: str, *args, **kwargs) -> str:
        response = self.model.generate_content(prompt, *args, **kwargs)
        return response.text

    @staticmethod
    def list_models() -> typing.List[LLMSchema]:
        available_models = genai.list_models()
        return [
            LLMSchema(
                name=model_info.name,
                display_name=model_info.display_name,
                description=model_info.description,
            )
            for model_info in available_models
            if "generateContent" in model_info.supported_generation_methods
        ]
