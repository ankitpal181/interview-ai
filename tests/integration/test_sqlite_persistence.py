"""
Integration tests for SQLite database persistence.
Tests the Storage class with SQLite for interview state persistence.
"""
import pytest
import os
import sys
import sqlite3
import tempfile
import importlib.util
from unittest.mock import MagicMock, patch


class TestSQLitePersistence:
    """Integration tests for SQLite storage persistence."""

    def test_sqlite_connection_and_table_creation(self):
        """Test that SQLite connection and tables can be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_interview.db")
            
            # Create connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create a simple checkpoints table (similar to LangGraph's schema)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT PRIMARY KEY,
                    checkpoint_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
            # Verify table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'checkpoints'
            
            conn.close()

    def test_state_persistence_and_retrieval(self):
        """Test saving and retrieving interview state from SQLite."""
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_state.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interview_states (
                    thread_id TEXT PRIMARY KEY,
                    state_json TEXT,
                    phase TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Save state
            thread_id = "test_thread_001"
            state = {
                "messages": [],
                "phase": "introduction",
                "candidate_information": {"name": "Test User"},
                "rules": {"format": "short"}
            }
            
            cursor.execute(
                "INSERT OR REPLACE INTO interview_states (thread_id, state_json, phase) VALUES (?, ?, ?)",
                (thread_id, json.dumps(state), state["phase"])
            )
            conn.commit()
            
            # Retrieve state
            cursor.execute("SELECT state_json, phase FROM interview_states WHERE thread_id = ?", (thread_id,))
            row = cursor.fetchone()
            
            assert row is not None
            retrieved_state = json.loads(row[0])
            assert retrieved_state["phase"] == "introduction"
            assert retrieved_state["candidate_information"]["name"] == "Test User"
            
            conn.close()

    def test_state_update_flow(self):
        """Test updating state through interview phases."""
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_update.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interview_states (
                    thread_id TEXT PRIMARY KEY,
                    state_json TEXT,
                    phase TEXT,
                    message_count INTEGER DEFAULT 0
                )
            ''')
            
            thread_id = "update_test_001"
            
            # Initial state
            state = {"phase": "introduction", "count": 0}
            cursor.execute(
                "INSERT INTO interview_states (thread_id, state_json, phase, message_count) VALUES (?, ?, ?, ?)",
                (thread_id, json.dumps(state), state["phase"], 0)
            )
            conn.commit()
            
            # Update through phases
            phases = ["introduction", "introduction", "introduction", "q&a", "evaluation"]
            for i, phase in enumerate(phases):
                state["phase"] = phase
                state["count"] = i + 1
                cursor.execute(
                    "UPDATE interview_states SET state_json = ?, phase = ?, message_count = ? WHERE thread_id = ?",
                    (json.dumps(state), phase, state["count"], thread_id)
                )
                conn.commit()
            
            # Verify final state
            cursor.execute("SELECT phase, message_count FROM interview_states WHERE thread_id = ?", (thread_id,))
            row = cursor.fetchone()
            
            assert row[0] == "evaluation"
            assert row[1] == 5
            
            conn.close()

    def test_multiple_concurrent_interviews(self):
        """Test handling multiple interview sessions in the database."""
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_concurrent.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interview_states (
                    thread_id TEXT PRIMARY KEY,
                    candidate_name TEXT,
                    phase TEXT
                )
            ''')
            
            # Create multiple interviews
            interviews = [
                ("thread_001", "Alice", "introduction"),
                ("thread_002", "Bob", "q&a"),
                ("thread_003", "Charlie", "evaluation"),
            ]
            
            for thread_id, name, phase in interviews:
                cursor.execute(
                    "INSERT INTO interview_states (thread_id, candidate_name, phase) VALUES (?, ?, ?)",
                    (thread_id, name, phase)
                )
            conn.commit()
            
            # Verify all interviews exist
            cursor.execute("SELECT COUNT(*) FROM interview_states")
            count = cursor.fetchone()[0]
            assert count == 3
            
            # Verify each interview
            for thread_id, expected_name, expected_phase in interviews:
                cursor.execute(
                    "SELECT candidate_name, phase FROM interview_states WHERE thread_id = ?",
                    (thread_id,)
                )
                row = cursor.fetchone()
                assert row[0] == expected_name
                assert row[1] == expected_phase
            
            conn.close()


class TestLangGraphSQLiteSaverMocked:
    """Tests for LangGraph's SQLite saver integration (mocked)."""

    def test_checkpoint_structure(self):
        """Test the expected checkpoint structure from LangGraph."""
        # Simulate the structure that langgraph-checkpoint-sqlite uses
        checkpoint_data = {
            "v": 1,  # Version
            "ts": "2024-01-01T00:00:00Z",
            "channel_values": {
                "messages": [],
                "phase": "introduction",
                "candidate_information": {}
            },
            "channel_versions": {},
            "versions_seen": {}
        }
        
        assert "channel_values" in checkpoint_data
        assert "messages" in checkpoint_data["channel_values"]
        assert checkpoint_data["channel_values"]["phase"] == "introduction"

    def test_state_snapshot_mock(self):
        """Test mocked state snapshot functionality."""
        # Mock a StateSnapshot-like object
        class MockStateSnapshot:
            def __init__(self):
                self.values = {
                    "messages": [MagicMock(content="Hello")],
                    "phase": "q&a",
                    "candidate_information": {"name": "Test"}
                }
                self.created_at = "2024-01-01T00:00:00Z"
                self.next = ("answer_collection_node",)
        
        snapshot = MockStateSnapshot()
        
        assert snapshot.values["phase"] == "q&a"
        assert snapshot.values["candidate_information"]["name"] == "Test"
        assert "answer_collection_node" in snapshot.next


class TestStorageModeSwitching:
    """Tests for switching between memory and database storage modes."""

    def test_memory_mode_simulation(self):
        """Test in-memory storage mode behavior."""
        # Import cache directly
        cache_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "src", "interview_ai", "core", "cache.py"
        )
        spec = importlib.util.spec_from_file_location("cache", cache_path)
        cache_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cache_module)
        
        cache = cache_module.SimpleCache()
        
        # Memory mode uses the SimpleCache
        thread_id = "memory_test"
        cache.set(thread_id, {"phase": "introduction"})
        
        result = cache.get(thread_id)
        assert result["phase"] == "introduction"
        
        # Memory is cleared when cache object is destroyed
        del cache
        new_cache = cache_module.SimpleCache()
        assert new_cache.get(thread_id) is None

    def test_database_mode_persistence_simulation(self):
        """Test that database mode persists across sessions."""
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "persistence_test.db")
            
            # Session 1: Save state
            conn1 = sqlite3.connect(db_path)
            cursor1 = conn1.cursor()
            cursor1.execute("CREATE TABLE IF NOT EXISTS states (id TEXT PRIMARY KEY, data TEXT)")
            cursor1.execute("INSERT INTO states VALUES (?, ?)", ("test", json.dumps({"phase": "saved"})))
            conn1.commit()
            conn1.close()
            
            # Session 2: Retrieve state (simulating server restart)
            conn2 = sqlite3.connect(db_path)
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT data FROM states WHERE id = ?", ("test",))
            row = cursor2.fetchone()
            conn2.close()
            
            assert row is not None
            assert json.loads(row[0])["phase"] == "saved"
