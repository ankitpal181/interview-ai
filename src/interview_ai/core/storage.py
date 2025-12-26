import sqlite3, os, psycopg
from pymongo import MongoClient
from typing import Literal
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import InMemorySaver
from .settings import settings


class Storage:
    """
    Storage class to load the system configurations and environment variables. 
    """

    def __init__(
        self,
        mode: Literal["memory", "database"],
        database: Literal["sqlite", "mongo", "postgres"] = "sqlite"
    ) -> None:
        """
        Initialize the storage class instance.

        Args:
            mode (Literal["memory", "database"]): Storage mode.
            database (Literal["sqlite", "mongo", "postgres"]): Database type.
        
        Returns:
            None
        """
        if mode == "memory": self.storage = InMemorySaver()
        else:
            if database == "mongo": self.storage = self._set_mongo_storage()
            elif database == "postgres": self.storage = self._set_postgres_storage()
            else: self.storage = self._set_sqlite_storage()
    
    def _set_sqlite_storage(self) -> SqliteSaver:
        """
        Set the storage to SQLite.

        Returns:
            SqliteSaver: SQLite storage object.
        """
        connection = sqlite3.connect("interview_ai.db", check_same_thread=False)
        return SqliteSaver(connection)
    
    def _set_mongo_storage(self) -> MongoDBSaver:
        """
        Set the storage to MongoDB.

        Returns:
            MongoDBSaver: MongoDB storage object.
        """
        connection = MongoClient(settings.database_uri)
        return MongoDBSaver(client=connection)
    
    def _set_postgres_storage(self) -> PostgresSaver:
        """
        Set the storage to PostgreSQL.

        Returns:
            PostgresSaver: PostgreSQL storage object.
        """
        connection = psycopg.connect(settings.database_uri)
        return PostgresSaver(connection)
