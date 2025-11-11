"""Configuration management for Democratic Republican SpokesBot."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Ollama Configuration
    ollama_base_url: str = "http://ollama:11434"
    ollama_llm_model: str = "qwen3:0.6b"
    ollama_embedding_model: str = "qwen3-embedding:0.6b"
    # Temperature for LLM (0.0-1.0). Higher values allow more creative reasoning.
    # 0.3-0.5 is good for factual answers with some reasoning, 0.7+ for more creative reasoning
    ollama_temperature: float = 0.4
    
    # Party Configuration
    party_name: str = "Democratic Republicans"
    bot_name: str = "Democratic Republican SpokesBot"
    
    # ChromaDB Configuration (use relative path for local dev, absolute for Docker)
    chroma_persist_directory: str = "data/chroma_db"
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # Rate Limiting (requests per minute per IP)
    rate_limit_per_minute: int = 10
    
    # Data directory (use relative path for local dev, absolute for Docker)
    # Now points to DRP Platform v3.0 directory
    data_directory: str = "drp_platform/platform"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

