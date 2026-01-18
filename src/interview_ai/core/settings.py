import os, json
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class StorageMode(Enum):
    MEMORY = "memory"
    DATABASE = "database"

class DatabaseName(Enum):
    POSTGRES = "postgres"
    MONGODB = "mongo"
    SQLITE = "sqlite"

class Settings(BaseSettings):
    """
    Settings class to load the system configurations and environment variables. 
    
    Attributes:
        model_config (SettingsConfigDict): Settings configuration.
        llm_api_key (Optional[str]): LLM API key.
        llm_model_name (str): LLM model name.
        storage_mode (StorageMode): Storage mode.
        database_uri (Optional[str]): Database URI.
        max_intro_questions (int): Maximum number of introduction questions.
        internet_search (str): Internet search tool name.
        database_name (DatabaseName): Database name.
        use_toon_formatting (bool): Use TOON formatting for LLM inputs.
    """
    model_config = SettingsConfigDict()

    # LLM MODELS
    llm_api_key: Optional[str] = Field(
        default=os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )
    llm_model_name: str = Field(default="")

    # STORAGE
    storage_mode: StorageMode = Field(default=StorageMode.MEMORY.value)
    database_name: DatabaseName = Field(default=DatabaseName.SQLITE.value)
    database_uri: Optional[str] = Field(
        default=os.getenv("POSTGRES_CONNECTION_URI") or os.getenv("MONGODB_CONNECTION_URI")
    )

    # GRAPH
    max_intro_questions: int = Field(default=3)
    use_toon_formatting: bool = Field(default=False)

    # TOOLS
    internet_search: str = Field(default="duckduckgo")

    def __init__(self) -> None:
        """
        Initialize the settings class instance.

        Returns:
            None
        """
        super().__init__()
        
        # LOAD SYSTEM CONFIGS
        root_dir = os.getcwd()
        config_path = os.path.join(root_dir, "interview_ai", "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, "r") as config_file:
                system_config = json.load(config_file)

                for config_key, config_value in system_config.items():
                    if config_key == "comments": continue
                    setattr(self, config_key, config_value)

            self._validate_settings()
        else:
            # Config file might not exist during initialization (init-agent)
            # Validation will happen when InterviewClient is instantiated.
            pass

    def _validate_settings(self) -> None:
        """
        Validate the settings values.

        Returns:
            None
        """
        # CONFIGURATIONS VALIDATION
        if self.storage_mode == StorageMode.DATABASE.value and self.database_uri is None:
            raise ValueError("Database URI not found")
        elif not self.llm_model_name:
            raise ValueError("LLM MODEL NAME not found")

settings = Settings()
