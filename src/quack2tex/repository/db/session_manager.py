import contextlib
from typing import Any, AsyncIterator

from sqlalchemy import event, NullPool, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from .registry import mapper_registry
from quack2tex.utils import Singleton


class SessionManager(metaclass=Singleton):
    """
    A context manager for creating database sessions
    """

    def __init__(
        self,
        url: str,
        enable_foreign_keys: bool = True,
        async_mode: bool = False,
        session_kwargs: dict | None = None,
        engine_kwargs: dict | None = None,
    ):
        """
        Initialize the SessionManager.

        :param url: Database URL
        :param enable_foreign_keys: Enable foreign key constraints
        :param async_mode: Enable asynchronous mode
        :param session_kwargs: Additional session keyword arguments
        :param engine_kwargs: Additional engine keyword arguments
        """
        self._async_mode = async_mode
        engine_kwargs = engine_kwargs or {}
        session_kwargs = session_kwargs or {
            "autocommit": False,
            "autoflush": False,
            "expire_on_commit": False,
        }

        # Create the appropriate engine based on async_mode.
        if self._async_mode:
            self._engine = create_async_engine(url, **engine_kwargs)
            SessionFactory = async_sessionmaker
        else:
            self._engine = create_engine(url, **engine_kwargs)
            SessionFactory = sessionmaker

        # Apply common session settings
        self._session_maker = SessionFactory(**session_kwargs, bind=self._engine)
        self._session = None
        if enable_foreign_keys:
            engine = self._engine if not self._async_mode else self._engine.sync_engine

            @event.listens_for(
                engine,
                "connect",
            )
            def _fk_pragma_on_connect(dbapi_con, con_record):
                dbapi_con.execute("pragma foreign_keys=ON")

    @classmethod
    def create(cls, *args, **kwargs):
        """
        Create a new SessionManager instance and initialize it.

        :return: Initialized SessionManager instance
        """
        session_manager = cls(*args, **kwargs)
        session_manager.init()
        return session_manager

    @classmethod
    async def async_create(cls, *args, **kwargs):
        """
        Create a new SessionManager instance and initialize it asynchronously.

        :return: Initialized SessionManager instance
        """
        session_manager = cls(*args, **kwargs)
        await session_manager.async_init()
        return session_manager

    def __enter__(self):
        """
        Enter the context manager, creating a new session.

        :return: Database session
        """
        assert not self._async_mode, "Asynchronous mode is enabled"
        self._session = self._session_maker()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager, closing the session.

        :param exc_type: Exception type
        :param exc_val: Exception value
        :param exc_tb: Exception traceback
        """
        if exc_val:
            self._session.rollback()
        self._session.close()

    async def __aenter__(self):
        """
        Enter the async context manager, creating a new async session.

        :return: Async database session
        """
        assert self._async_mode, "Asynchronous mode is not enabled"
        self._session = self._session_maker()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the async context manager, closing the async session.

        :param exc_type: Exception type
        :param exc_val: Exception value
        :param exc_tb: Exception traceback
        """
        if exc_val:
            await self._session.rollback()
        await self._session.close()

    @contextlib.asynccontextmanager
    async def async_session(self, *args, **kwargs) -> AsyncIterator[AsyncSession]:
        """
        Create an async session.

        :yield: Async database session
        """
        assert self._async_mode, "Asynchronous mode is not enabled"
        async with self._session_maker(*args, **kwargs) as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    @contextlib.contextmanager
    def session(self, *args, **kwargs) -> Any:
        """
        Create a session.

        :yield: Database session
        """
        assert not self._async_mode, "Asynchronous mode is enabled"
        session = self._session_maker(*args, **kwargs)
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def async_init(self, drop_all: bool = False):
        """
        Initialize the database asynchronously.

        :param drop_all: Drop all tables before creating them
        :return: Self
        """
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        async with self._engine.begin() as conn:
            if drop_all:
                await conn.run_sync(mapper_registry.metadata.drop_all)
            await conn.run_sync(mapper_registry.metadata.create_all)
        return self

    def init(self, drop_all: bool = False):
        """
        Initialize the database.

        :param drop_all: Drop all tables before creating them
        :return: Self
        """
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        if drop_all:
            mapper_registry.metadata.drop_all(self._engine)
        mapper_registry.metadata.create_all(self._engine)
        return self

    async def async_close(self):
        """
        Close the database asynchronously.
        """
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()
        self._engine = None
        self._session_maker = None

    def close(self):
        """
        Close the database.
        """
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        self._engine.dispose()
        self._engine = None
        self._session_maker = None

    @contextlib.asynccontextmanager
    async def async_connect(self) -> AsyncIterator[AsyncConnection]:
        """
        Connect to the database asynchronously.

        :yield: Async database connection
        """
        assert self._async_mode, "Asynchronous mode is not enabled"
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.contextmanager
    def connect(self) -> Any:
        """
        Connect to the database.

        :yield: Database connection
        """
        assert not self._async_mode, "Asynchronous mode is enabled"
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        connection = self._engine.connect()
        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

