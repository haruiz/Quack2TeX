import os

import typer
from dotenv import load_dotenv, find_dotenv

import quack2tex

app = typer.Typer(invoke_without_command=True)


@app.command()
def start(
    gemini_api_key: str = typer.Option(None, envvar="GEMINI_API_KEY", help="Google Gemini API key"),
    openai_api_key: str = typer.Option(None, envvar="OPENAI_API_KEY", help="OpenAI API key"),
    anthropic_api_key: str = typer.Option(None, envvar="ANTHROPIC_API_KEY", help="Anthropic API key"),
    groq_api_key: str = typer.Option(None, envvar="GROQ_API_KEY", help="Groq API key"),
):
    """
    Start the Quack2Tex application with optional LLM API keys.
    You can provide keys via command-line or environment variables.
    """
    # Set API keys in environment if provided
    api_keys = {
        "GEMINI_API_KEY": gemini_api_key,
        "OPENAI_API_KEY": openai_api_key,
        "ANTHROPIC_API_KEY": anthropic_api_key,
        "GROQ_API_KEY": groq_api_key,
    }

    for key, value in api_keys.items():
        if value:
            os.environ[key] = value

    # Start the main app
    quack2tex.run_app()


def run():
    """
    Entry point: Load environment variables and invoke CLI app.
    """
    load_dotenv(find_dotenv())
    app()


if __name__ == "__main__":
    run()
