from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from quack2tex import LLM
from quack2tex.llm import OpenAIClient, OllamaClient, GoogleClient
from dotenv import find_dotenv, load_dotenv
import os
import openai
import google.generativeai as genai
from tqdm import tqdm

if __name__ == "__main__":
    load_dotenv(find_dotenv())

    # Configure API keys
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    openai.api_key = os.getenv("OPENAI_API_KEY")

    #image = Image.open("test_image2.png")
    # prompt = ["generate the latex code from the following image: ", image]
    # prompt = ["describe following image:", image]
    # prompt = "who are you?"
    #
    # # Example usage of Google LLM
    # google_available_models = GoogleClient.list_models()
    # gemini = GoogleClient.get_model(
    #     "models/gemini-1.5-flash-latest",
    #     system_instruction="generate the output in markdown format",
    # )
    # print(gemini(prompt))
    #
    # # Example usage of OpenAI LLM
    # open_ai_available_models = OpenAIClient.list_models()
    # print(open_ai_available_models)
    # gpt4o = OpenAIClient.get_model(
    #     "gpt-4o", system_instruction="generate the output in markdown format"
    # )
    # print(gpt4o(prompt))
    #
    # # Example usage of Ollama LLM
    # ollama_available_models = OllamaClient.list_models()
    # llama3 = OllamaClient.get_model(
    #     "llama3.1:latest", system_instruction="generate the output in markdown format"
    # )
    # print(llama3(prompt))
    #
    # llava = OllamaClient.get_model(
    #     "llava:34b", system_instruction="generate the output in markdown format"
    # )
    # print(llava(prompt))

    # models = ["gpt-4o", "llama3.1:latest", "llava:34b", "models/gemini-1.5-flash-latest"]
    #
    # def call_llm(model, system_instruction, prompt):
    #     llm = LLM.create(model, system_instruction=system_instruction)
    #     return llm(prompt)
    #
    # system_instruction = "generate the output in json format"
    # prompt = "who are you?"
    #
    # with ThreadPoolExecutor() as executor:
    #     futures = {
    #         executor.submit(call_llm, model, system_instruction, prompt): model
    #         for model in models
    #     }
    #     results = {}
    #     for future in tqdm(as_completed(futures), total=len(futures)):
    #         model_name = futures[future]
    #         task_exception = future.exception()
    #         results[model_name] = task_exception or future.result()
    #
    # for model, result in results.items():
    #     print(f"{model}: {result}")