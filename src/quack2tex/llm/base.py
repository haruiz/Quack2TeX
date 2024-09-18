import typing
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class LLMSchema(BaseModel):
    client: str = Field(
        ..., title="Client Name", description="The name of the client that provides the model"
    )
    name: str = Field(
        ..., title="Model Name", description="The name of the model to use"
    )
    display_name: str = Field(
        ..., title="Display Name", description="The display name of the model"
    )
    description: typing.Optional[str] = Field(
        None, title="Model Description", description="A description of the model"
    )


# Abstract Base Class for LLM
class LLMClient(ABC):
    """Base class for all LLM clients."""

    def __init__(self, model_name: str, *args, **kwargs) -> None:
        self.model_name = model_name
        available_model_names = [m.name for m in self.list_models()]
        if model_name not in available_model_names:
            raise ValueError(
                f"Model {model_name} not available. Available models: {available_model_names}"
            )

    def __new__(cls, *args, **kwargs):
        raise TypeError("Direct instantiation is not allowed. Use 'get_model' method.")

    @classmethod
    def get_model(cls, *args, **kwargs):
        """Get a model instance."""
        if not issubclass(cls, LLMClient):
            raise TypeError("Method can only be called on subclasses of LLM")
        instance = super().__new__(cls)
        instance.__init__(*args, **kwargs)
        return instance

    @staticmethod
    @abstractmethod
    def list_models() -> typing.List[LLMSchema]:
        """
        List available models.
        :return:  List of available models
        """
        pass

    @abstractmethod
    def ask(self, prompt: typing.Any, *args, **kwargs) -> str:
        """
        Ask the model a question.
        :param prompt:
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def __call__(self, prompt: typing.Any, *args, **kwargs):
        return self.ask(prompt, *args, **kwargs)
