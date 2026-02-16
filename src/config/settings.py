"""
QA-GPT Configuration Module

Manages all application settings using Pydantic Settings v2.
Reads from .env file and provides type-safe configuration access.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    
    All settings have sensible defaults except for provider-specific credentials.
    """
    
    # LLM Provider Configuration
    llm_provider: str
    
    # AWS Bedrock Configuration
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_default_region: str = "eu-west-1"
    bedrock_model_id: str = "eu.anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    # Google Gemini Configuration
    gemini_api_key: str = ""
    gemini_model_id: str = "gemini-1.5-pro"
    
    # Team Configuration
    team_id: str = "local_team"
    
    # QA Pipeline Configuration
    qa_confidence_threshold: float = 0.85
    max_judge_iterations: int = 3
    
    # Context File Paths
    tech_context_path: str = "context_files/tech_context.md"
    codebase_map_path: str = "context_files/codebase_map.md"
    
    # Logging Configuration
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate that llm_provider is either 'bedrock' or 'gemini'."""
        if v not in ("bedrock", "gemini"):
            raise ValueError(
                f"llm_provider must be 'bedrock' or 'gemini', got '{v}'"
            )
        return v


# Module-level singleton instance
settings = Settings()