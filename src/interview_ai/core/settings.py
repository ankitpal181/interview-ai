import os, json
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class StorageMode(Enum):
    MEMORY = "memory"
    DATABASE = "database"

class Settings(BaseSettings):
    model_config = SettingsConfigDict()

    # LLM MODELS
    llm_api_key: Optional[str] = Field(
        default=os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )
    llm_model_name: str = Field(default="")

    # STORAGE
    storage_mode: StorageMode = Field(default=StorageMode.MEMORY.value)
    database_uri: Optional[str] = Field(
        default=os.getenv("POSTGRES_CONNECTION_URI") or os.getenv("MONGODB_CONNECTION_URI")
    )

    # GRAPH
    max_intro_questions: int = Field(default=3)

    # TOOLS
    internet_search: str = Field(default="duckduckgo")

    def __init__(self) -> None:
        super().__init__()
        
        # LOAD SYSTEM CONFIGS
        root_dir = os.getcwd()
        config_path = os.path.join(root_dir, "interview_ai", "config.json")
        
        with open(config_path, "r") as config_file:
            system_config = json.load(config_file)

            for config_key, config_value in system_config.items():
                if config_key == "comments": continue
                setattr(self, config_key, config_value)
        
        self._validate_settings()
    
    def _validate_settings(self) -> None:
        # CONFIGURATIONS VALIDATION
        if self.storage_mode == StorageMode.DATABASE.value and self.database_uri is None:
            raise ValueError("Database URI not found")
        elif not self.llm_model_name:
            raise ValueError("LLM MODEL NAME not found")

settings = Settings()
