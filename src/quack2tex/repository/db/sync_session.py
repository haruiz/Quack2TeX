from .session_manager import SessionManager
from quack2tex.utils import LibUtils
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import Session


db_sync_connection_string, _ = LibUtils.get_db_connection_string()
sessionmanager = SessionManager(
    url=db_sync_connection_string,
    async_mode=False,
    engine_kwargs={"echo": False, "poolclass": NullPool},
)

def get_db_session(*args, **kwargs) -> Session:
    """
    Get database session
    """
    drop_all = kwargs.pop("drop_all", False)
    sessionmanager.init(drop_all=drop_all)
    return sessionmanager.session(*args, **kwargs)