import os

import typer
from dotenv import load_dotenv, find_dotenv
from typing_extensions import Annotated
import quack2tex

app = typer.Typer(invoke_without_command=True)


@app.command()
def start(
    google_api_key: str = typer.Option(None, envvar="GOOGLE_API_KEY"),
    openai_api_key: str = typer.Option(None, envvar="OPENAI_API_KEY"),
    model: str = "models/gemini-1.5-flash-latest",
):
    """
    Run the application.
    :param model: The model to use.
    :param google_api_key: The Google API key.
    :param openai_api_key: The OpenAI API key.
    """
    if google_api_key:
        os.environ["GOOGLE_API_KEY"] = google_api_key
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    quack2tex.run_app(model)


def run():
    """
    Run the application.
    :return:
    """
    load_dotenv(find_dotenv())
    app()


if __name__ == "__main__":
    run()
