from .session_manager import SessionManager
from quack2tex.utils import LibUtils
from sqlalchemy import inspect, text
from sqlalchemy.pool import NullPool
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session


db_sync_connection_string, _ = LibUtils.get_db_connection_string()
sessionmanager = SessionManager(
    url=db_sync_connection_string,
    async_mode=False,
    engine_kwargs={"echo": False, "poolclass": NullPool},
)
def init_db(drop_all: bool = False) -> None:
    """Initialize the synchronous database schema.

    Args:
        drop_all: Whether to drop all mapped tables before recreating them.
    """
    sessionmanager.init(drop_all=drop_all)
    ensure_prompt_title_column()
    ensure_response_unique_index()

def get_db_session(*args: object, **kwargs: object) -> AbstractContextManager[Session]:
    """Create a synchronous database session context manager.

    Args:
        *args: Positional arguments passed to the session factory.
        **kwargs: Keyword arguments passed to the session factory.

    Returns:
        Context manager yielding a SQLAlchemy session.
    """
    return sessionmanager.session(*args, **kwargs)

def ensure_prompt_title_column() -> None:
    """Add `prompt.title` to existing local SQLite databases.

    SQLAlchemy `create_all` does not add columns to existing tables, so this
    idempotent upgrade keeps older local history databases readable without
    dropping saved prompts.
    """
    engine = sessionmanager._engine
    inspector = inspect(engine)
    if not inspector.has_table("prompt"):
        return
    columns = {column["name"] for column in inspector.get_columns("prompt")}
    if "title" in columns:
        return
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE prompt ADD COLUMN title VARCHAR"))


def ensure_response_unique_index() -> None:
    """Prevent duplicate saved responses in existing local SQLite databases.

    SQLAlchemy `create_all` applies the unique constraint only for new
    databases. This idempotent upgrade removes exact duplicate response rows
    created by older versions and then creates the matching unique index.
    """
    engine = sessionmanager._engine
    inspector = inspect(engine)
    if not inspector.has_table("response"):
        return

    index_names = {index["name"] for index in inspector.get_indexes("response")}
    constraint_names = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("response")
    }
    if "uq_response_prompt_model_output" in index_names | constraint_names:
        return

    with engine.begin() as connection:
        connection.execute(text(
            """
            DELETE FROM response
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM response
                GROUP BY prompt_id, model, output
            )
            """
        ))
        connection.execute(text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_response_prompt_model_output
            ON response (prompt_id, model, output)
            """
        ))
