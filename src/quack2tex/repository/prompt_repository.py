from io import BytesIO
from typing import List, Optional, Union
from pathlib import Path

from sqlalchemy import desc
from sqlalchemy.orm import Session
from quack2tex.repository.models import Prompt, Response
from quack2tex.repository.db.sync_session import get_db_session
from sqlalchemy.orm import selectinload
from PIL.Image import Image as PILImage
from PIL import Image


class PromptRepository:
    """
    Repository class for handling operations related to Prompts and their Responses.
    """

    @classmethod
    def get_prompt_by_id(cls, session: Session, prompt_id: int) -> Optional[Prompt]:
        """
        Retrieves a prompt by its ID.
        """
        return session.query(Prompt).filter(Prompt.id == prompt_id).first()

    @classmethod
    def get_all_prompts(cls, session: Session) -> List[Prompt]:
        """
        Retrieves all prompts in the database.
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
        capture_mode: str
    ) -> int:
        """
        Adds a new prompt with either text or binary input (image, file, etc.)

        Args:
            session (Session): The database session.
            system_instruction (str): System instruction string.
            guidance_prompt (str): Guidance text.
            input_data (str or Path): Text string or path to a binary file.
            capture_mode (str): Metadata on how the prompt was captured.

        Returns:
            Prompt: The persisted prompt.
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
        )
        session.add(prompt)
        session.flush()  # Pushes to DB and populates new_prompt.id

        return prompt.id

    @classmethod
    def delete_prompt(cls, session: Session, prompt_id: int) -> None:
        """
        Deletes a prompt and its associated responses from the database.
        """
        prompt = cls.get_prompt_by_id(session, prompt_id)
        if prompt:
            session.delete(prompt)
            session.commit()

    @classmethod
    def add_response(cls, session: Session, prompt_id: int, model_name: str, model_output: str) -> Response:
        """
        Adds a response to a given prompt.
        """
        response = Response(
            prompt_id=prompt_id,
            model=model_name,
            output=model_output,
        )
        session.add(response)

    @classmethod
    def get_responses_for_prompt(cls, session: Session, prompt_id: int) -> List[Response]:
        """
        Retrieves all responses for a given prompt.
        """
        prompt = cls.get_prompt_by_id(session, prompt_id)
        return prompt.responses if prompt else []


if __name__ == '__main__':
    with get_db_session() as session:
        # Example: Save a text prompt
        PromptRepository.add_prompt_from_input(
            session,
            system_instruction="Answer concisely.",
            guidance_prompt="Summarize the input.",
            input_data="This is a sample user input.",
            capture_mode="manual"
        )

        # Example: Save an image prompt
        PromptRepository.add_prompt_from_input(
            session,
            system_instruction="Describe the image.",
            guidance_prompt="What is shown in the picture?",
            input_data=Path("/Users/haruiz/Desktop/cat.png"),
            capture_mode="image-upload"
        )

        all_prompts = PromptRepository.get_all_prompts(session)
        print(all_prompts)
