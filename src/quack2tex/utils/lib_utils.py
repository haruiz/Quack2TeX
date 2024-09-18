import os
from pathlib import Path

class LibUtils:
    """
    Library utilities
    """

    @classmethod
    def get_lib_home(cls):
        """
        it returns the path to the library home
        :return:
        """

        default_folder = Path.home() / ".quack2tex"
        lib_home = Path(os.getenv("QUACK_HOME", default_folder))
        lib_home.mkdir(parents=True, exist_ok=True)
        return lib_home

    @classmethod
    def get_db_connection_string(cls):
        """
        Get the database and artifacts location
        :return:
        """
        lib_home = cls.get_lib_home()
        db_file = lib_home / "quack2tex.db"
        default_db_sync_connection_string = f"sqlite:///{db_file}"
        default_db_async_connection_string = f"sqlite+aiosqlite:///{db_file}"
        db_async_connections_string = os.getenv(
            "QUACK2TEX_ASYNC_DB_CONNECTION_STRING", default_db_async_connection_string
        )
        db_sync_connections_string = os.getenv(
            "QUACK2TEX_SYNC_DB_CONNECTION_STRING", default_db_sync_connection_string
        )
        return db_sync_connections_string, db_async_connections_string
