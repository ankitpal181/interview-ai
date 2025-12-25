"""
Tests for interview_ai.cli.setup module.
Tests the CLI setup command that initializes the interview_ai directory.
"""
import pytest
import os
import json
import tempfile
import importlib.util
from unittest.mock import patch
from io import StringIO


def _import_cli_setup():
    """Import the CLI setup module directly to avoid full package import chain."""
    setup_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src", "interview_ai", "cli", "setup.py"
    )
    spec = importlib.util.spec_from_file_location("cli_setup", setup_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCliSetup:
    """Test suite for CLI setup command."""

    def test_creates_interview_ai_directory(self):
        """Test that interview_ai directory is created."""
        cli_setup = _import_cli_setup()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.getcwd', return_value=tmpdir):
                with patch('sys.stdout', new_callable=StringIO):
                    cli_setup.main()
                
                interview_dir = os.path.join(tmpdir, "interview_ai")
                assert os.path.isdir(interview_dir)

    def test_creates_config_json(self):
        """Test that config.json is created with correct content."""
        cli_setup = _import_cli_setup()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.getcwd', return_value=tmpdir):
                with patch('sys.stdout', new_callable=StringIO):
                    cli_setup.main()
                
                config_path = os.path.join(tmpdir, "interview_ai", "config.json")
                assert os.path.isfile(config_path)
                
                with open(config_path, "r") as f:
                    config = json.load(f)
                
                assert "llm_model_name" in config
                assert "storage_mode" in config
                assert "internet_search" in config
                assert config["llm_model_name"] == "gpt-4.1-mini"
                assert config["storage_mode"] == "memory"
                assert config["internet_search"] == "duckduckgo"

    def test_creates_interview_rules_json(self):
        """Test that interview_rules.json is created with correct formats."""
        cli_setup = _import_cli_setup()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.getcwd', return_value=tmpdir):
                with patch('sys.stdout', new_callable=StringIO):
                    cli_setup.main()
                
                rules_path = os.path.join(tmpdir, "interview_ai", "interview_rules.json")
                assert os.path.isfile(rules_path)
                
                with open(rules_path, "r") as f:
                    rules = json.load(f)
                
                assert "short" in rules
                assert "long" in rules
                assert "coding" in rules
                assert rules["short"]["time_frame"] == 1
                assert rules["long"]["time_frame"] == 10
                assert rules["coding"]["time_frame"] == 30

    def test_creates_example_env(self):
        """Test that .example-env is created."""
        cli_setup = _import_cli_setup()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.getcwd', return_value=tmpdir):
                with patch('sys.stdout', new_callable=StringIO):
                    cli_setup.main()
                
                env_path = os.path.join(tmpdir, "interview_ai", ".example-env")
                assert os.path.isfile(env_path)
                
                with open(env_path, "r") as f:
                    content = f.read()
                
                assert "OPENAI_API_KEY" in content
                assert "GOOGLE_API_KEY" in content
                assert "POSTGRES_CONNECTION_URI" in content
                assert "MONGODB_CONNECTION_URI" in content

    def test_creates_tools_py(self):
        """Test that tools.py is created with user_tools list."""
        cli_setup = _import_cli_setup()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.getcwd', return_value=tmpdir):
                with patch('sys.stdout', new_callable=StringIO):
                    cli_setup.main()
                
                tools_path = os.path.join(tmpdir, "interview_ai", "tools.py")
                assert os.path.isfile(tools_path)
                
                with open(tools_path, "r") as f:
                    content = f.read()
                
                assert "user_tools = []" in content
                assert "StructuredTool" in content

    def test_prints_success_messages(self):
        """Test that success messages are printed."""
        cli_setup = _import_cli_setup()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.getcwd', return_value=tmpdir):
                output = StringIO()
                with patch('sys.stdout', output):
                    cli_setup.main()
                
                output_str = output.getvalue()
                assert "Interview AI Setup" in output_str
                assert "interview_ai/ created!" in output_str
                assert "config.json created!" in output_str
                assert "interview_rules.json created!" in output_str
                assert "Setup Completed Successfully" in output_str

    def test_fails_if_directory_exists(self):
        """Test that setup fails if interview_ai directory already exists."""
        cli_setup = _import_cli_setup()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-create the directory
            os.makedirs(os.path.join(tmpdir, "interview_ai"))
            
            with patch('os.getcwd', return_value=tmpdir):
                with pytest.raises(FileExistsError):
                    cli_setup.main()


class TestConfigJsonStructure:
    """Test suite for config.json structure validation."""

    def test_config_has_comments_section(self):
        """Test that config.json includes comments section."""
        cli_setup = _import_cli_setup()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.getcwd', return_value=tmpdir):
                with patch('sys.stdout', new_callable=StringIO):
                    cli_setup.main()
                
                config_path = os.path.join(tmpdir, "interview_ai", "config.json")
                with open(config_path, "r") as f:
                    config = json.load(f)
                
                assert "comments" in config
                assert "llm_model_name" in config["comments"]
                assert "storage_mode" in config["comments"]


class TestInterviewRulesStructure:
    """Test suite for interview_rules.json structure validation."""

    def test_each_format_has_required_fields(self):
        """Test that each format in interview_rules has required fields."""
        cli_setup = _import_cli_setup()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.getcwd', return_value=tmpdir):
                with patch('sys.stdout', new_callable=StringIO):
                    cli_setup.main()
                
                rules_path = os.path.join(tmpdir, "interview_ai", "interview_rules.json")
                with open(rules_path, "r") as f:
                    rules = json.load(f)
                
                required_fields = ["format", "time_frame", "no_of_questions", "questions_type"]
                
                for format_name in ["short", "long", "coding"]:
                    for field in required_fields:
                        assert field in rules[format_name], f"{field} missing in {format_name}"
