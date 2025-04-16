"""
Configuration Management for ThoughtCaptcha Backend.

This module loads application settings from environment variables using Pydantic.
It ensures that required settings like database URLs and API keys are present.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    # Load .env file if it exists (useful for local development)
    # In production (like Railway), env vars are usually set directly.
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    DATABASE_URL: str
    OPENROUTER_API_KEY: str = "" # Default to empty string if not set
    FRONTEND_ORIGIN_URL: str = "*" # Default to allow all origins for simplicity in demo

    # --- OpenRouter Specific Settings (Optional - Can be expanded later) ---
    # OPENROUTER_MODEL: str = "openai/gpt-3.5-turbo" # Example default model
    # OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

@lru_cache()
def get_settings() -> Settings:
    """
    Returns the application settings instance.
    Uses lru_cache to load settings only once.
    """
    return Settings()

# Example usage (typically imported in other modules):
# from .config import get_settings
# settings = get_settings()
# print(settings.DATABASE_URL) 