"""
CLI script to setup Interview AI. Run init-agent to setup Interview AI.

**Note: Avoide running this script directly, always use provided commands like init-agent.
Running it twice will remove existing interview_ai directory and create a new one,
resulting in loss of existing data.**
"""
import os, json
from typing import List


def _setup_directories(paths: List[str]) -> None:
    """
    This function will create a interview_ai directory in the current directory[
    should be the root directory of the project, where your server resides].
    """
    print("Preparing directories...")
    for path in paths:
        os.mkdir(path)
        print(f"{path}/ created!")

def _setup_config(paths: List[str]) -> None:
    """
    This function will create a config.json file in the interview_ai directory.
    """
    for path in paths:
        with open(path, "w") as file:
            data = {
                "comments": {
                    "llm_model_name": "Model name to be used for llm. For local models, use model name from hugging-face. Agent will download and setup the model locally.",
                    "storage_mode": "[Options]: memory or database. To use database, add related database uri in environment variables. Supported databases are postgres, sqlite, mongodb. See .example-env for more details.",
                    "internet_search": "[Options]: duckduckgo, bing. To use bing, add BING_SUBSCRIPTION_KEY and BING_SEARCH_URL in environment variables. See .example-env for more details.",
                    "database_name": "[Options]: postgres, sqlite, mongodb. To use database, add related database uri in environment variables. See .example-env for more details.",
                    "use_toon_formatting": "[Options]: true, false. If true, all the llm inputs will be optimized using TOON data format conversions. This will reduce token consumtion for all the input messages but will add few static tokens as system message to explain the format to LLM."
                },
                "llm_model_name": "gpt-4.1-mini",
                "storage_mode": "memory",
                "internet_search": "duckduckgo",
                "database_name": "sqlite",
                "use_toon_formatting": False
            }
            file.write(json.dumps(data, indent=4))
        print(f"{path}/ created!")

def _setup_rules(paths: List[str]) -> None:
    """
    This function will create a interview_rules.json file in the interview_ai directory.
    """
    for path in paths:
        with open(path, "w") as file:
            data = {
                "comments": {
                    "format": "Interview format name that will be used for lookups. You can add multiple formats in interview_rules.json and your desired rule values.",
                    "time_frame": "Time limit for each question in minutes.",
                    "no_of_questions": "Number of questions to ask.",
                    "questions_type": "Type of questions to ask (multiple choice, theory, practical, both practical and theory)."
                },
                "short": {
                    "format": "short",
                    "time_frame": 1,
                    "no_of_questions": 5,
                    "questions_type": "both practical and theory"
                },
                "long": {
                    "format": "long",
                    "time_frame": 10,
                    "no_of_questions": 5,
                    "questions_type": "both practical and theory"
                },
                "coding": {
                    "format": "coding",
                    "time_frame": 30,
                    "no_of_questions": 1,
                    "questions_type": "coding"
                }
            }
            file.write(json.dumps(data, indent=4))
        print(f"{path}/ created!")

def _setup_env(paths: List[str]) -> None:
    """
    This function will create a .example-env file in the interview_ai directory.
    """
    for path in paths:
        with open(path, "w") as file:
            data = """# OPENAI_API_KEY is prioritized if both are present.\n# For local models, leave both OPENAI_API_KEY and GOOGLE_API_KEY blank.\n# The system will automatically fallback to loading a local model via Hugging Face.\nOPENAI_API_KEY = ""\nGOOGLE_API_KEY = ""\n\n# DATABASE [leave unchanged if using sqlite or in-memory storage]\nPOSTGRES_CONNECTION_URI = "postgresql://user:password@host:port/database" # If using postgres(must already have a running connection)\nMONGODB_CONNECTION_URI = "mongodb://user:password@host:port/database/?authSource=admin" # If using mongodb(must already have a running connection)\n\n# Tools [uncomment if you want to use bing search or use duckduckgo for unpaid search]\n# BING_SUBSCRIPTION_KEY = ""\n# BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search" # refer bing search api docs for verification\n\n# Uncomment these if you want to setup langsmith\n# LANGCHAIN_API_KEY = ""\n# LANGCHAIN_TRACING_V2 = "true"\n# LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"\n# LANGCHAIN_PROJECT = "interview-ai"\n"""
            file.write(data)
        print(f"{path}/ created!")

def _setup_tools(paths: List[str]) -> None:
    """
    This function will create a tools.py file in the interview_ai directory.
    """
    for path in paths:
        with open(path, "w") as file:
            data = """# Create custom tools here using langchain standards.\n# The Agent will load all tools from this file and use them.\n# Make sure to add descriptions to each tool,\n# so that the Agent's LLM could understand when and how to use them.\n\nfrom langchain_core.tools import StructuredTool\n\n# Do not remove this line. This will be used to import your tools.\nuser_tools = [] # Add your tools names here\n"""
            file.write(data)
        print(f"{path}/ created!")

def main() -> None:
    """
    This function will create a interview_ai directory in the current directory[
    should be the root directory of the project, where your server resides].
    
    It will create the following files:
    - config.json # Configuration file for Interview AI
    - interview_rules.json # Interview rules file
    - .example-env # Environment variables file
    - tools.py # Tools file to add custom tools

    Returns:
        None
    """
    print("Interview AI Setup")
    root_dir = os.getcwd()
    setup_path = os.path.join(root_dir, "interview_ai")
    config_path = os.path.join(setup_path, "config.json")
    rules_path = os.path.join(setup_path, "interview_rules.json")
    env_path = os.path.join(setup_path, ".example-env")
    tools_path = os.path.join(setup_path, "tools.py")

    _setup_directories([setup_path])

    print("Preparing files...")
    _setup_config([config_path])
    _setup_rules([rules_path])
    _setup_env([env_path])
    _setup_tools([tools_path])

    print("Interview AI Setup Completed Successfully!")
