"""Configuration management for PartyBot."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Ollama Configuration
    ollama_base_url: str = "http://ollama:11434"
    ollama_llm_model: str = "qwen3:0.6b"
    ollama_embedding_model: str = "qwen3-embedding:0.6b"
    
    # Party Configuration
    party_name: str = "Democratic Republicans"
    
    # ChromaDB Configuration (use relative path for local dev, absolute for Docker)
    chroma_persist_directory: str = "data/chroma_db"
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # Data directory (use relative path for local dev, absolute for Docker)
    # Now points to DRP Platform v3.0 directory
    data_directory: str = "drp_platform/platform"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

