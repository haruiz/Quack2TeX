import typing

import ollama
import tenacity
from PIL.Image import Image as PILImage

from quack2tex.llm.base import LLMClient, LLMSchema
from quack2tex.utils import ImageUtils


class OllamaClient(LLMClient):
    """A class for the Ollama client."""

    def __init__(self, model_name: str, **kwargs) -> None:
        super().__init__(model_name)
        self.api_client = ollama.Client()
        self.system_instruction = kwargs.get("system_instruction", "")

    @staticmethod
    def _normalized_prompt_content(prompt: typing.Any) -> dict:
        """
        Normalize the prompt.
        :param prompt:
        :return:
        """
        if isinstance(prompt, str):
            return {"role": "user", "content": prompt}
        elif isinstance(prompt, PILImage):
            return {
                "role": "user",
                "content": "",
                "images": [ImageUtils.image_to_base64_url(prompt)],
            }
        elif isinstance(prompt, list):
            images = [img for img in prompt if isinstance(img, PILImage)]
            texts = [txt for txt in prompt if isinstance(txt, str)]
            return {
                "role": "user",
                "content": "".join(texts),
                "images": [ImageUtils.image_to_base64(img) for img in images],
            }
        else:
            raise ValueError("Unsupported prompt type")

    @tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(3), reraise=True)
    def ask(self, prompt: typing.Any, *args, **kwargs) -> str:
        messages_queue = (
            [{"role": "system", "content": self.system_instruction}]
            if self.system_instruction
            else []
        )
        normalized_prompt = self._normalized_prompt_content(prompt)
        messages_queue.append(normalized_prompt)
        response = self.api_client.chat(
            model=self.model_name, messages=messages_queue, **kwargs
        )
        ai_message = response.get("message", {})
        return ai_message.get("content", "")

    @staticmethod
    def list_models() -> typing.List[LLMSchema]:
        ollama_models = ollama.list()
        return [
            LLMSchema(name=model_info["model"], display_name=model_info["name"], client="ollama")
            for model_info in ollama_models["models"]
        ]
