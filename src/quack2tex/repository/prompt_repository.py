from io import BytesIO
from typing import List, Optional, Union
from pathlib import Path

from sqlalchemy import desc
from sqlalchemy.orm import Session
from quack2tex.repository.models import Prompt, Response
from quack2tex.repository.db.sync_session import get_db_session
from sqlalchemy.orm import selectinload
from PIL.Image import Image as PILImage


class PromptRepository:
    """Persist and query saved prompts and model responses."""

    @classmethod
    def get_prompt_by_id(cls, session: Session, prompt_id: int) -> Optional[Prompt]:
        """Retrieve a prompt by id.

        Args:
            session: Active SQLAlchemy session.
            prompt_id: Prompt primary key.

        Returns:
            Prompt row when found, otherwise None.
        """
        return session.query(Prompt).filter(Prompt.id == prompt_id).first()

    @classmethod
    def get_all_prompts(cls, session: Session) -> List[Prompt]:
        """Retrieve all prompts with eager-loaded responses.

        Args:
            session: Active SQLAlchemy session.

        Returns:
            Prompts sorted newest first.
        """
        return (
            session.query(Prompt)
            .options(selectinload(Prompt.responses))
            .order_by(desc(Prompt.created_at))  # Sort newest first
            .all()
        )


    @classmethod
    def add_prompt(
        cls,
        session: Session,
        system_instruction: str,
        guidance_prompt: str,
        input_data: Union[str, Path],
        capture_mode: str,
        title: str | None = None,
    ) -> int:
        """Add a prompt with text, image, or file input.

        Args:
            session: Active SQLAlchemy session.
            system_instruction: System instruction used for the model call.
            guidance_prompt: User-facing action prompt.
            input_data: Prompt input as text, a file path, or a PIL image.
            capture_mode: Metadata describing how the input was captured.
            title: Optional display title generated from model output.

        Returns:
            Database id of the persisted prompt.

        Raises:
            ValueError: If `input_data` is not supported.
        """
        if isinstance(input_data, PILImage):
            image_format = input_data.format if input_data.format else "PNG"
            buffer = BytesIO()
            input_data.save(buffer, format=image_format)
            binary_data = buffer.getvalue()
        elif isinstance(input_data, str):
            binary_data = input_data.encode("utf-8")
        elif isinstance(input_data, Path) or Path(input_data).is_file():
            with open(input_data, "rb") as f:
                binary_data = f.read()
        else:
            raise ValueError("input_data must be a string, Path, or PIL Image")

        prompt = Prompt(
            system_instruction=system_instruction,
            guidance_prompt=guidance_prompt,
            prompt_input=binary_data,
            capture_mode=capture_mode,
            title=title,
        )
        session.add(prompt)
        session.flush()  # Pushes to DB and populates new_prompt.id

        return prompt.id

    @classmethod
    def delete_prompt(cls, session: Session, prompt_id: int) -> None:
        """Delete a prompt and its associated responses.

        Args:
            session: Active SQLAlchemy session.
            prompt_id: Prompt primary key.
        """
        prompt = cls.get_prompt_by_id(session, prompt_id)
        if prompt:
            session.delete(prompt)
            session.commit()

    @classmethod
    def delete_response(cls, session: Session, response_id: int) -> None:
        """Delete a single model response.

        Args:
            session: Active SQLAlchemy session.
            response_id: Response primary key.
        """
        response = session.query(Response).filter(Response.id == response_id).first()
        if response:
            session.delete(response)
            session.commit()

    @classmethod
    def add_response(cls, session: Session, prompt_id: int, model_name: str, model_output: str) -> Response:
        """Add a model response to a saved prompt.

        Args:
            session: Active SQLAlchemy session.
            prompt_id: Parent prompt id.
            model_name: Model identifier that produced the output.
            model_output: Markdown/text output returned by the model.

        Returns:
            Persisted response with primary key populated.
        """
        response = Response(
            prompt_id=prompt_id,
            model=model_name,
            output=model_output,
        )
        session.add(response)
        session.flush()
        return response

    @classmethod
    def get_response(
        cls,
        session: Session,
        prompt_id: int,
        model_name: str,
        model_output: str,
    ) -> Optional[Response]:
        """Retrieve an existing response for the exact prompt, model, and output.

        Args:
            session: Active SQLAlchemy session.
            prompt_id: Parent prompt id.
            model_name: Model identifier that produced the output.
            model_output: Markdown/text output returned by the model.

        Returns:
            Matching response when found, otherwise None.
        """
        return (
            session.query(Response)
            .filter(
                Response.prompt_id == prompt_id,
                Response.model == model_name,
                Response.output == model_output,
            )
            .first()
        )

    @classmethod
    def get_or_add_response(
        cls,
        session: Session,
        prompt_id: int,
        model_name: str,
        model_output: str,
    ) -> tuple[Response, bool]:
        """Return an existing response or save a new one.

        Args:
            session: Active SQLAlchemy session.
            prompt_id: Parent prompt id.
            model_name: Model identifier that produced the output.
            model_output: Markdown/text output returned by the model.

        Returns:
            Response row and a flag that is True when a new row was created.
        """
        response = cls.get_response(session, prompt_id, model_name, model_output)
        if response is not None:
            return response, False
        return cls.add_response(session, prompt_id, model_name, model_output), True

    @classmethod
    def get_responses_for_prompt(cls, session: Session, prompt_id: int) -> List[Response]:
        """Retrieve responses for a prompt.

        Args:
            session: Active SQLAlchemy session.
            prompt_id: Prompt primary key.

        Returns:
            Response rows for the prompt, or an empty list if the prompt is absent.
        """
        prompt = cls.get_prompt_by_id(session, prompt_id)
        return prompt.responses if prompt else []


if __name__ == '__main__':
    with get_db_session() as session:
        prompt_id = PromptRepository.add_prompt(
            session,
            system_instruction="Answer concisely.",
            guidance_prompt="Summarize the input.",
            input_data="This is a sample user input.",
            capture_mode="manual",
            title="Sample Summary",
        )
        PromptRepository.add_response(session, prompt_id, "example-model", "This is a sample response.")
        session.commit()

        all_prompts = PromptRepository.get_all_prompts(session)
        print(all_prompts)
