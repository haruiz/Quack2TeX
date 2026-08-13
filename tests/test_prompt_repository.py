from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from quack2tex.repository.models import Base, Response
from quack2tex.repository.prompt_repository import PromptRepository


def test_get_or_add_response_reuses_same_model_output_for_prompt() -> None:
    """Saving the same model output for a prompt should not create duplicates."""
    engine = create_engine("sqlite:///:memory:")
    Base.registry.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        prompt_id = PromptRepository.add_prompt(
            session=session,
            system_instruction="Answer concisely.",
            guidance_prompt="Summarize this.",
            input_data="Prompt input",
            capture_mode="text",
            title="Short Summary",
        )

        first_response, first_created = PromptRepository.get_or_add_response(
            session=session,
            prompt_id=prompt_id,
            model_name="models/example",
            model_output="The same output.",
        )
        second_response, second_created = PromptRepository.get_or_add_response(
            session=session,
            prompt_id=prompt_id,
            model_name="models/example",
            model_output="The same output.",
        )

        assert first_created is True
        assert second_created is False
        assert second_response.id == first_response.id
        assert session.query(Response).count() == 1


def test_response_schema_rejects_duplicate_model_output_for_prompt() -> None:
    """The database should reject exact duplicate model outputs for a prompt."""
    engine = create_engine("sqlite:///:memory:")
    Base.registry.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        prompt_id = PromptRepository.add_prompt(
            session=session,
            system_instruction="Answer concisely.",
            guidance_prompt="Summarize this.",
            input_data="Prompt input",
            capture_mode="text",
            title="Short Summary",
        )
        PromptRepository.add_response(
            session=session,
            prompt_id=prompt_id,
            model_name="models/example",
            model_output="The same output.",
        )

        try:
            PromptRepository.add_response(
                session=session,
                prompt_id=prompt_id,
                model_name="models/example",
                model_output="The same output.",
            )
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("Expected duplicate response insert to fail")
