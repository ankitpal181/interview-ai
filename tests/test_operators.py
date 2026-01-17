"""
Tests for interview_ai.core.operators module.
Focuses on error handling and logic verification, mocking heavy dependencies.
"""
import sys
import os
import pytest
import json
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

# Clean up sys.modules to ensure we load the real operators module
# even if other tests mocked it globally
modules_to_remove = [
    "interview_ai.core.operators",
    "interview_ai.core.llms",
    "interview_ai.core.prompts",
    "interview_ai.core.tools",
    "interview_ai.core.schemas"
]
for mod in modules_to_remove:
    if mod in sys.modules:
        del sys.modules[mod]

# Mock LLMs to prevent heavy loading
mock_llms = MagicMock()
class MockModel:
    def __init__(self, tools=[], output_schema=None):
        self.tools = tools
        self.model = MagicMock()

mock_llms.Model = MockModel
sys.modules["interview_ai.core.llms"] = mock_llms

# Mock prompts to control constant values
mock_prompts = MagicMock()
mock_prompts.REPORTING_PROMPT = "Format: {pdf} {email} {whatsapp} {description_value}"
mock_prompts.REPORTING_PROMPT_MAP = {
    "pdf": "PDF_Instructions",
    "email": "Email_Instructions",
    "whatsapp": "Whatsapp_Instructions",
    "description_value": "Description_Instructions"
}
mock_prompts.INTERVIEWBOT_PROMPT = "InterviewBot Prompt {role}"
sys.modules["interview_ai.core.prompts"] = mock_prompts

# Mock tools with proper name attributes for ToolNode
mock_tools_module = MagicMock()

def create_mock_tool_func(name):
    def mock_tool_func(*args, **kwargs):
        """Mock tool docstring."""
        return "mock_tool_output"
    mock_tool_func.__name__ = name
    mock_tool_func.name = name
    mock_tool_func.description = f"Mock tool {name}"
    return mock_tool_func

mock_tools_module.search_internet = create_mock_tool_func("search_internet")
mock_tools_module.generate_csv_tool = create_mock_tool_func("generate_csv_tool")
mock_tools_module.generate_pdf_tool = create_mock_tool_func("generate_pdf_tool")
mock_tools_module.call_api_tool = create_mock_tool_func("call_api_tool")
mock_tools_module.user_tools = []

sys.modules["interview_ai.core.tools"] = mock_tools_module
sys.modules["interview_ai.core.schemas"] = MagicMock()

# Now import operators
from interview_ai.core.operators import (
    question_generation_function, 
    reporting_perception_function,
    questioner_tools_operator,
    reporting_tools_operator
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

class TestQuestionGenerationFunction:
    """Test suite for question_generation_function."""

    def test_handles_generation_error(self):
        """Test that the function catches exceptions and returns an error message."""
        state = {"messages": [HumanMessage(content="start")]}
        
        # Make the first invoke raise an exception
        # questioner_tools_operator is an instance of MockModel from our mock above
        # The code calls: questioner_tools_operator.model.invoke(messages)
        
        questioner_tools_operator.model.invoke.side_effect = Exception("Simulated API Error")
        
        result = question_generation_function(state)
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)
        assert "Error while generating questions" in result["messages"][0].content
        assert "Simulated API Error" in result["messages"][0].content

    def test_successful_generation(self):
        """Test successful path (sanity check)."""
        state = {"messages": [HumanMessage(content="start")]}
        
        # Reset side effect
        questioner_tools_operator.model.invoke.side_effect = None
        
        # Mock returns
        mock_tools_resp = AIMessage(content="tools output") # No tool calls
        questioner_tools_operator.model.invoke.return_value = mock_tools_resp
        
        # We need to mock questioner_model too, but it's not exported directly by name in the import above
        # accessing via module import would be better, but we mocked the module deps. 
        # Actually operators.py defines 'questioner_model' global.
        import interview_ai.core.operators as ops
        
        mock_q_resp = MagicMock()
        mock_q_resp.model_dump_json.return_value = '{"questions": []}'
        mock_q_resp.questions = []
        ops.questioner_model.model.invoke.return_value = mock_q_resp
        
        result = question_generation_function(state)
        
        assert "questions" in result


class TestReportingPerceptionFunction:
    """Test suite for reporting_perception_function."""
    
    def test_always_includes_description_value(self):
        """Test that description_value is included even if not in reporting data."""
        # reporting_data without description_value
        reporting_data = {"pdf": True} 
        last_message = AIMessage(content=json.dumps(reporting_data))
        state = {"messages": [last_message]}
        
        result = reporting_perception_function(state)
        
        # Check the inserted system prompt
        # It's inserted at -1 (before the last message)
        # So messages list size increases by 1
        messages = result["messages"]
        system_msg = messages[-2] # index -1 was the AIMessage
        
        assert isinstance(system_msg, SystemMessage)
        assert "Description_Instructions" in system_msg.content
