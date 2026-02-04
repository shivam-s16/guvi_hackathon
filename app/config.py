"""
Configuration module for the Honeypot API.
Loads settings from environment variables.
Supports FREE AI providers: Gemini, Cohere, Groq

IMPORTANT: All sensitive values must be set via environment variables.
Never hardcode API keys or secrets!
"""

import os
from functools import lru_cache
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration - MUST be set in production!
    api_key: str = os.getenv("API_KEY", "change-me-in-production")
    api_host: str = "0.0.0.0"
    # Support PORT env var for deployment platforms (Render, Heroku, Railway)
    api_port: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    
    # AI Provider Configuration (all FREE)
    ai_provider: str = "gemini"  # Options: gemini, groq, cohere
    
    # Google Gemini API Key (FREE - https://makersuite.google.com/app/apikey)
    gemini_api_key: Optional[str] = None
    
    # Groq API Key (FREE - https://console.groq.com)
    groq_api_key: Optional[str] = None
    
    # Cohere API Key (FREE - https://dashboard.cohere.com/api-keys)
    cohere_api_key: Optional[str] = None
    
    # GUVI Callback
    guvi_callback_url: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    # Session Configuration
    session_timeout_minutes: int = 30
    max_engagement_messages: int = 25
    
    # Scam Detection Thresholds
    scam_confidence_threshold: float = 0.7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
