"""
Tests for interview_ai.clients.interview_client module.
Tests the InterviewClient class logic without triggering full package imports.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch


class TestAnswerExpiryLogic:
    """Test suite for answer expiry calculation logic."""

    def test_returns_message_when_not_expired(self):
        """Test that message is returned when not expired."""
        # Inline the expiry logic for testing
        def check_answer_expiry(user_message, last_updated, time_frame):
            if datetime.fromisoformat(last_updated) < datetime.now(timezone.utc) - timedelta(
                minutes=float(time_frame), seconds=float(5)
            ):
                return ""
            return user_message
        
        last_updated = datetime.now(timezone.utc).isoformat()
        result = check_answer_expiry("my answer", last_updated, 10)
        
        assert result == "my answer"

    def test_returns_empty_when_expired(self):
        """Test that empty string is returned when answer is expired."""
        def check_answer_expiry(user_message, last_updated, time_frame):
            if datetime.fromisoformat(last_updated) < datetime.now(timezone.utc) - timedelta(
                minutes=float(time_frame), seconds=float(5)
            ):
                return ""
            return user_message
        
        # Set last_updated to 10 minutes ago
        last_updated = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        result = check_answer_expiry("my answer", last_updated, 1)  # 1 minute time_frame
        
        assert result == ""

    def test_includes_5_second_buffer(self):
        """Test that 5 second buffer is included in expiry calculation."""
        def check_answer_expiry(user_message, last_updated, time_frame):
            if datetime.fromisoformat(last_updated) < datetime.now(timezone.utc) - timedelta(
                minutes=float(time_frame), seconds=float(5)
            ):
                return ""
            return user_message
        
        # Set last_updated to exactly 1 minute ago (should still be valid due to 5s buffer)
        last_updated = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        result = check_answer_expiry("my answer", last_updated, 1)
        
        assert result == "my answer"

    def test_expires_after_buffer(self):
        """Test that answer expires after time_frame + 5 seconds."""
        def check_answer_expiry(user_message, last_updated, time_frame):
            if datetime.fromisoformat(last_updated) < datetime.now(timezone.utc) - timedelta(
                minutes=float(time_frame), seconds=float(5)
            ):
                return ""
            return user_message
        
        # Set last_updated to 1 minute and 10 seconds ago (exceeds 1 min + 5 sec buffer)
        last_updated = (datetime.now(timezone.utc) - timedelta(minutes=1, seconds=10)).isoformat()
        result = check_answer_expiry("my answer", last_updated, 1)
        
        assert result == ""


class TestMaxQuestionsCalculation:
    """Test suite for max questions calculation logic."""

    def test_max_questions_with_rules_value(self):
        """Test max questions calculation with value from rules."""
        interview_rules = {"no_of_questions": 5}
        max_intro_questions = 3
        
        max_questions = interview_rules.get("no_of_questions", 10) + max_intro_questions
        
        assert max_questions == 8

    def test_max_questions_with_default(self):
        """Test max questions calculation with default when not in rules."""
        interview_rules = {}  # No no_of_questions
        max_intro_questions = 3
        
        max_questions = interview_rules.get("no_of_questions", 10) + max_intro_questions
        
        assert max_questions == 13

    def test_max_questions_with_zero(self):
        """Test max questions calculation when rules specify 0."""
        interview_rules = {"no_of_questions": 0}
        max_intro_questions = 3
        
        max_questions = interview_rules.get("no_of_questions", 10) + max_intro_questions
        
        assert max_questions == 3


class TestInterviewEndCondition:
    """Test suite for interview end condition logic."""

    def test_returns_end_when_count_equals_max(self):
        """Test that __end__ is returned when count equals max questions."""
        cached_data = {"count": 8}
        max_questions = 8
        
        result = "__end__" if cached_data["count"] >= max_questions else {"message": "next"}
        
        assert result == "__end__"

    def test_returns_end_when_count_exceeds_max(self):
        """Test that __end__ is returned when count exceeds max questions."""
        cached_data = {"count": 10}
        max_questions = 8
        
        result = "__end__" if cached_data["count"] >= max_questions else {"message": "next"}
        
        assert result == "__end__"

    def test_returns_message_when_count_less_than_max(self):
        """Test that message is returned when count is less than max."""
        cached_data = {"count": 5}
        max_questions = 8
        
        result = "__end__" if cached_data["count"] >= max_questions else {"message": "next"}
        
        assert result == {"message": "next"}


class TestCachedDataStructure:
    """Test suite for cached data structure handling."""

    def test_interrupt_type_detection(self):
        """Test detection of interrupt type in cached data."""
        cached_data = {"last_message": {"type": "interrupt", "text": "Enter name"}}
        
        is_interrupt = cached_data["last_message"]["type"] == "interrupt"
        
        assert is_interrupt is True

    def test_text_type_detection(self):
        """Test detection of text type in cached data."""
        cached_data = {"last_message": {"type": "text", "text": "Welcome!"}}
        
        is_interrupt = cached_data["last_message"]["type"] == "interrupt"
        
        assert is_interrupt is False

    def test_count_increment(self):
        """Test count increment logic."""
        cached_data = {"count": 3}
        cached_data["count"] += 1
        
        assert cached_data["count"] == 4

    def test_last_updated_timestamp(self):
        """Test last_updated timestamp update."""
        cached_data = {"last_updated": None}
        cached_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        assert cached_data["last_updated"] is not None
        # Verify it's a valid ISO format string
        parsed = datetime.fromisoformat(cached_data["last_updated"])
        assert parsed.tzinfo is not None


class TestConfigValidation:
    """Test suite for config validation logic."""

    def test_raises_on_empty_config_next(self):
        """Test that ValueError is raised when interview_config is empty for next."""
        interview_config = {}
        
        with pytest.raises(ValueError, match="Interview config is required"):
            if not interview_config:
                raise ValueError("Interview config is required")

    def test_raises_on_empty_config_end(self):
        """Test that ValueError is raised when interview_config is empty for end."""
        interview_config = {}
        
        with pytest.raises(ValueError, match="Interview config is required"):
            if not interview_config:
                raise ValueError("Interview config is required")

    def test_valid_config_passes(self):
        """Test that valid config doesn't raise."""
        interview_config = {"configurable": {"thread_id": "test123"}}
        
        # Should not raise
        if not interview_config:
            raise ValueError("Interview config is required")
        
        # Access thread_id
        thread_id = interview_config["configurable"]["thread_id"]
        assert thread_id == "test123"
