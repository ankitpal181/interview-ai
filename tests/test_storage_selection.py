"""
Tests for the Storage class initialization logic.
"""
import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Add src to python path to allow imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src"))

from interview_ai.core.storage import Storage

class TestStorageInitialization:
    """Test suite for Storage class backend selection."""

    def test_memory_storage_selection(self):
        """Test initialization of in-memory storage."""
        with patch("interview_ai.core.storage.InMemorySaver") as mock_saver:
            storage = Storage(mode="memory")
            
            mock_saver.assert_called_once()
            assert storage.storage == mock_saver.return_value

    def test_sqlite_storage_selection(self):
        """Test initialization of SQLite storage."""
        with patch("interview_ai.core.storage.SqliteSaver") as mock_saver, \
             patch("sqlite3.connect") as mock_connect:
            
            storage = Storage(mode="database", database="sqlite")
            
            mock_connect.assert_called_with("interview_ai.db", check_same_thread=False)
            mock_saver.assert_called_once_with(mock_connect.return_value)
            assert storage.storage == mock_saver.return_value

    def test_mongo_storage_selection(self):
        """Test initialization of MongoDB storage."""
        with patch("interview_ai.core.storage.MongoDBSaver") as mock_saver, \
             patch("interview_ai.core.storage.MongoClient") as mock_client, \
             patch("interview_ai.core.storage.settings") as mock_settings:
            
            mock_settings.database_uri = "mongodb://localhost:27017"
            
            storage = Storage(mode="database", database="mongo")
            
            mock_client.assert_called_with("mongodb://localhost:27017")
            mock_saver.assert_called_once_with(client=mock_client.return_value)

    def test_postgres_storage_selection(self):
        """Test initialization of PostgreSQL storage."""
        with patch("interview_ai.core.storage.PostgresSaver") as mock_saver, \
             patch("interview_ai.core.storage.psycopg.connect") as mock_connect, \
             patch("interview_ai.core.storage.settings") as mock_settings:
            
            mock_settings.database_uri = "postgresql://localhost:5432"
            
            storage = Storage(mode="database", database="postgres")
            
            mock_connect.assert_called_with("postgresql://localhost:5432")
            mock_saver.assert_called_once_with(mock_connect.return_value)
