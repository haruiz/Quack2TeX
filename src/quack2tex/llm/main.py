from quack2tex.llm import OpenAIClient, OllamaClient, GoogleClient
from dotenv import find_dotenv, load_dotenv
import os
from PIL import Image
import openai
import google.generativeai as genai


if __name__ == "__main__":
    load_dotenv(find_dotenv())

    # Configure API keys
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    openai.api_key = os.getenv("OPENAI_API_KEY")

    image = Image.open("test_image2.png")
    # prompt = ["generate the latex code from the following image: ", image]
    # prompt = ["describe following image:", image]
    prompt = "who are you?"

    # Example usage of Google LLM
    google_available_models = GoogleClient.list_models()
    gemini = GoogleClient.get_model(
        "models/gemini-1.5-flash-latest",
        system_instruction="generate the output in markdown format",
    )
    print(gemini(prompt))

    # Example usage of OpenAI LLM
    open_ai_available_models = OpenAIClient.list_models()
    gpt4o = OpenAIClient.get_model(
        "gpt-4o", system_instruction="generate the output in markdown format"
    )
    print(gpt4o(prompt))

    # Example usage of Ollama LLM
    ollama_available_models = OllamaClient.list_models()
    llama3 = OllamaClient.get_model(
        "llama3.1:latest", system_instruction="generate the output in markdown format"
    )
    print(llama3(["generate the latex code for the equation 2 + 2 = 4"]))

    llava = OllamaClient.get_model(
        "llava:34b", system_instruction="generate the output in markdown format"
    )
    print(llava(prompt))
