from typing import AsyncIterator

from .session_manager import SessionManager
from quack2tex.utils import LibUtils
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession

_, db_async_connection_string = LibUtils.get_db_connection_string()
sessionmanager = SessionManager(
    url=db_async_connection_string,
    async_mode=True,
    engine_kwargs={"echo": False, "poolclass": NullPool},
)


async def get_db_session(*args, **kwargs)-> AsyncIterator[AsyncSession]:
    """
    Get database session
    """
    drop_all = kwargs.pop("drop_all", False)
    await sessionmanager.async_init(drop_all=drop_all)
    async with sessionmanager.async_session(*args, **kwargs) as session:
        yield session
