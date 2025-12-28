"""
Tests for the end() method of InterviewClient.
Focuses on the operations_map processing and LLM interaction.
"""
import sys
import os
import pytest
import json
from unittest.mock import MagicMock, patch, ANY

# Add src to python path to allow imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src"))
# Corrects path to point to interview-ai/src
sys.path.pop() # Remove previous incorrect append if any (safety)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

# MOCK EVERYTHING BEFORE IMPORTING
# This is necessary because operators.py instantiates Model() at module level
mock_operators = MagicMock()
sys.modules["interview_ai.core.operators"] = mock_operators

mock_server = MagicMock()
# Create the interviewbot mock that will be imported
mock_interviewbot_instance = MagicMock()
mock_server.interviewbot = mock_interviewbot_instance
sys.modules["interview_ai.servers"] = mock_server
sys.modules["interview_ai.servers.interview_server"] = mock_server

# Now safety import
from interview_ai.clients.interview_client import InterviewClient

@pytest.fixture
def mock_interviewbot():
    """Return the mocked interviewbot."""
    return mock_interviewbot_instance

@pytest.fixture
def mock_cache():
    """Mock the cache system."""
    with patch("interview_ai.clients.interview_client.load_cache") as mock:
        yield mock

@pytest.fixture
def mock_settings():
    """Mock settings."""
    with patch("interview_ai.core.settings.Settings") as mock:
        yield mock

class TestInterviewClientEnd:
    """Test suite for InterviewClient.end() method."""
    
    def setup_method(self):
        # Reset mocks
        mock_interviewbot_instance.reset_mock()
        
        # Patch load_interview_rules to avoid disk I/O
        self.rules_patcher = patch("interview_ai.clients.interview_client.load_interview_rules")
        self.mock_rules = self.rules_patcher.start()
        self.mock_rules.return_value = {"no_of_questions": 5, "time_frame": 10}
        
        # Patch settings
        self.settings_patcher = patch("interview_ai.clients.interview_client.settings")
        self.mock_settings = self.settings_patcher.start()
        self.mock_settings.max_intro_questions = 3
        
        self.client = InterviewClient()
        self.interview_config = {"configurable": {"thread_id": "test_thread"}}
        
    def teardown_method(self):
        self.rules_patcher.stop()
        self.settings_patcher.stop()

    def test_end_basic_flow(self, mock_interviewbot, mock_cache):
        """Test basic end flow without operations."""
        mock_cache.return_value = {
            "last_message": {"text": '{"rating": "Good"}'},
            "count": 5
        }
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = json.dumps({"evaluation": '{"rating": "Good"}'})
        # Note: In real code, end() parses response["messages"][-1].content
        # If operations map is empty, end() still invokes bot
        mock_interviewbot.invoke.return_value = {"messages": [mock_response]}
        
        result = self.client.end(self.interview_config)
        
        assert "evaluation" in result
        assert result["evaluation"] == '{"rating": "Good"}'

    def test_operations_map_email_processing(self, mock_interviewbot, mock_cache):
        """Test processing of email operations."""
        mock_cache.return_value = {"last_message": {"text": "eval"}, "count": 5}
        
        operations = [{
            "type": "email",
            "receiver_name": "Test Recipient",
            "receiver_relation_to_interview": "HR",
            "template": "Hello {name}"
        }]
        
        # Mock LLM response for reporting phase
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "email": [{"subject": "Test", "body": "Body", "attachment": {"file_path": "path.pdf"}}],
            "pdf": {"file_path": "path.pdf"}
        })
        mock_interviewbot.invoke.return_value = {"messages": [mock_response]}
        
        self.client.end(self.interview_config, operations)
        
        # Verify correct message context was sent to LLM
        call_args = mock_interviewbot.invoke.call_args_list[0]
        sent_message = json.loads(call_args[0][0]["messages"][0].content)
        
        assert "email" in sent_message
        assert sent_message["email"][0]["receiver_name"] == "Test Recipient"
        assert sent_message["attachment"] == "Generate Evaluation PDF"

    def test_operations_map_api_placeholder_processing(self, mock_interviewbot, mock_cache):
        """Test processing of API operations with placeholders."""
        mock_cache.return_value = {"last_message": {"text": "eval"}, "count": 5}
        
        operations = [{
            "type": "api",
            "endpoint": "https://api.test/v1",
            "body": {
                "static": "value",
                "dynamic": "#Description# Generate a summary #Description#"
            },
            "attachment": "#Evaluation PDF#"
        }]
        
        # Mock LLM response with generated values
        mock_response_content = {
            "description_value": [
                {
                    "endpoint": "https://api.test/v1",
                    "key": "dynamic",
                    "value": "Generated Summary"
                }
            ],
            "pdf": {"file_path": "/tmp/test.pdf"},
            "error_report": ""
        }
        mock_response = MagicMock()
        mock_response.content = json.dumps(mock_response_content)
        mock_interviewbot.invoke.return_value = {"messages": [mock_response]}
        
        self.client.end(self.interview_config, operations)
        
        # Verify first call for generation requests description values
        first_call = mock_interviewbot.invoke.call_args_list[0]
        sent_request = json.loads(first_call[0][0]["messages"][0].content)
        
        assert "description_value" in sent_request
        # Check specific structure based on implementation: 
        # user_message["description_value"] is a list of dicts
        assert sent_request["description_value"][0]["dynamic"] == "#Description# Generate a summary #Description#"
        
        # Verify second call executes the API tool with filled values
        second_call = mock_interviewbot.invoke.call_args_list[1]
        api_call_msg = json.loads(second_call[0][0]["messages"][0].content.replace("Call these APIs:\n", ""))
        
        assert api_call_msg["body"]["dynamic"] == "Generated Summary"
        assert api_call_msg["attachment"] == "/tmp/test.pdf"

    def test_whatsapp_operation_structure(self, mock_interviewbot, mock_cache):
        """Test that WhatsApp operations are correctly structured."""
        mock_cache.return_value = {"last_message": {"text": "eval"}, "count": 5}
        
        operations = [{
            "type": "whatsapp",
            "receiver_name": "Test User",
            "receiver_relation_to_interview": "Candidate"
        }]
        
        mock_response = MagicMock()
        mock_response.content = json.dumps({"whatsapp": [], "pdf": {}})
        mock_interviewbot.invoke.return_value = {"messages": [mock_response]}
        
        self.client.end(self.interview_config, operations)
        
        call_args = mock_interviewbot.invoke.call_args_list[0]
        sent_message = json.loads(call_args[0][0]["messages"][0].content)
        
        assert "whatsapp" in sent_message
        assert sent_message["whatsapp"][0]["receiver_name"] == "Test User"
