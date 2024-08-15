from .openai_client import OpenAIClient
from .google_client import GoogleClient
from .ollama_client import OllamaClient


class LLM:
    """
    A factory class for creating model instances.
    """

    _clients = {"openai": OpenAIClient, "google": GoogleClient, "ollama": OllamaClient}

    @staticmethod
    def create(model: str, **kwargs):
        """
        Create a model instance.

        :param model: The model name to create an instance of.
        :param kwargs: Additional keyword arguments to pass to the model's `get_model` method.
        :return: The created model instance.
        :raises ValueError: If the model is not found in any client.
        """

        # Cache available models for each client

        # Find the correct client based on the model name
        for client_name, client_class in LLM._clients.items():
            try:
                return client_class.get_model(model, **kwargs)
            except ValueError:
                pass
        # If the model is not found in any of the clients, raise an error
        raise ValueError(f"Model '{model}' is not available in any registered client.")
