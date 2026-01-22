"""Configuration settings for the multi-agent system"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Azure OpenAI settings
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_api_version: str = "2025-01-01-preview"
    azure_openai_deployment: str = "gpt-4.1"
    
    # Neo4j settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: Optional[str] = ""
    neo4j_password: Optional[str] = ""
    
    # Serper API settings (optional)
    serper_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
