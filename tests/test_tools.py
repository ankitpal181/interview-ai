"""
Tests for the custom tools in interview_ai.core.tools.
"""
import pytest
import os
import sys
import json
from unittest.mock import MagicMock, patch

# Add src to python path to allow imports
# Corrects path to point to interview-ai/src
# Add src to python path to allow imports
# Corrects path to point to interview-ai/src
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

# Clean up sys.modules to ensure we load the real tools module
# This protects against pollution from other tests running in the same suite
modules_to_reload = [
    "interview_ai.core.tools",
    "interview_ai.core.utilities",
    "interview_ai.core.schemas",
    "interview_ai.core.operators"
]
for mod in modules_to_reload:
    if mod in sys.modules:
        del sys.modules[mod]

from interview_ai.core.tools import call_api_endpoint, generate_csv_file, generate_pdf_file

class TestTools:
    """Test suite for core tools."""

    @patch("interview_ai.core.tools.requests.request")
    @patch("builtins.open", new_callable=MagicMock)
    def test_call_api_endpoint_success(self, mock_open, mock_request):
        """Test successful API call."""
        # Setup mock file
        mock_file = MagicMock()
        mock_open.return_value = mock_file
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_request.return_value = mock_response
        
        api_details = {
            "method": "POST",
            "endpoint": "https://api.test/data",
            "headers": {"Content-Type": "application/json"},
            "body": {"key": "value"},
            "attachment": {"file": "/path/to/file.pdf"}
        }
        
        result = call_api_endpoint(api_details)
        
        assert result == {"status": "success"}
        
        # Dictionary iteration order not guaranteed, but we only have one item
        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        assert kwargs["method"] == "POST"
        assert kwargs["url"] == "https://api.test/data"
        assert kwargs["headers"] == {"Content-Type": "application/json"}
        assert kwargs["data"] == {"key": "value"}
        assert "file" in kwargs["files"]
        assert kwargs["files"]["file"] == mock_file

    @patch("interview_ai.core.tools.requests.request")
    def test_call_api_endpoint_failure(self, mock_request):
        """Test API call failure handling."""
        mock_request.side_effect = Exception("Connection error")
        
        api_details = {
            "method": "GET",
            "endpoint": "https://api.test/fail",
            "headers": {},
            "body": {},
            "attachment": ""
        }
        
        result = call_api_endpoint(api_details)
        
        assert "error" in result
        assert result["error"] == "Failed to call API endpoint"

    @patch("pandas.DataFrame.to_csv")
    def test_generate_csv_file(self, mock_to_csv):
        """Test CSV generation."""
        data = {
            "Name": ["Alice", "Bob"],
            "Score": [90, 85]
        }
        
        result = generate_csv_file(data)
        
        assert result["file_name"] == "Interview_AI.csv"
        assert result["mime"] == "text/csv"
        mock_to_csv.assert_called_once()
        # Verify path construction
        assert result["file_path"].endswith("interview_ai/Interview_AI.csv")

    @patch("interview_ai.core.tools.HTML")
    def test_generate_pdf_file(self, mock_html_cls):
        """Test PDF generation."""
        mock_html_instance = MagicMock()
        mock_html_cls.return_value = mock_html_instance
        
        template = "<html><body>Test</body></html>"
        
        result = generate_pdf_file(template)
        
        assert result["file_name"] == "Interview_AI.pdf"
        assert result["mime"] == "application/pdf"
        mock_html_instance.write_pdf.assert_called_once()
        assert result["file_path"].endswith("interview_ai/Interview_AI.pdf")
