"""
Configuration centralisée pour le framework IBN Agentic AI
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # LLM Configuration - DeepSeek-R1 8B via Ollama
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "deepseek-r1:8b"  # DeepSeek-R1 8B (reasoning model)
    llm_temperature: float = 0.0
    
    # OpenSlice Configuration
    openslice_base_url: str = "http://localhost:13082"
    openslice_username: str = "admin"
    openslice_password: str = "admin"
    
    # ChromaDB Configuration
    chroma_persist_dir: str = "./data/chroma_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Application Configuration
    log_level: str = "INFO"
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instance globale
settings = Settings()
