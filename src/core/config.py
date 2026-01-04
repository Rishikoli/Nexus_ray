"""
Configuration management for Nexus Ray framework.

Centralizes all configuration with environment variable support.
"""

from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os


class KafkaSettings(BaseModel):
    """Kafka configuration"""
    bootstrap_servers: str = Field(default="localhost:9092")
    client_id: str = Field(default="nexus-ray")
    group_id: str = Field(default="nexus-ray-group")
    compression_type: str = Field(default="gzip")
    auto_offset_reset: str = Field(default="latest")
    enable_auto_commit: bool = Field(default=True)


class DatabaseSettings(BaseModel):
    """Database configuration"""
    url: str = Field(default="sqlite:///nexus_ray.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)


class LLMSettings(BaseModel):
    """LLM configuration"""
    default_model: str = Field(default="mistral-7b-ov")
    model_path: str = Field(default="models/")
    device: str = Field(default="CPU")
    quantization: str = Field(default="int8")
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.7)
    timeout_seconds: int = Field(default=60)


class VectorMemorySettings(BaseModel):
    """Vector memory configuration"""
    backend: str = Field(default="faiss")  # faiss or chromadb
    dimension: int = Field(default=768)
    index_type: str = Field(default="IndexFlatL2")
    persist_directory: str = Field(default="./data/vector_memory")
    collection_name: str = Field(default="nexus_ray_memory")


class ObservabilitySettings(BaseModel):
    """Observability configuration"""
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    prometheus_port: int = Field(default=9090)
    enable_tracing: bool = Field(default=True)
    enable_llm_insights: bool = Field(default=True)


class APISettings(BaseModel):
    """API configuration"""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)
    reload: bool = Field(default=False)
    enable_cors: bool = Field(default=True)
    cors_origins: list = Field(default=["http://localhost:3000"])


class WorkflowSettings(BaseModel):
    """Workflow execution configuration"""
    max_retries: int = Field(default=3)
    default_timeout_seconds: int = Field(default=300)
    enable_parallel_execution: bool = Field(default=True)
    max_concurrent_tasks: int = Field(default=10)
    retry_backoff_base: float = Field(default=2.0)
    state_persistence_enabled: bool = Field(default=True)


class NotionSettings(BaseModel):
    """Notion integration configuration"""
    enabled: bool = Field(default=False)
    api_key: str = Field(default="")
    workflow_database_id: str = Field(default="")  # Database for workflow documentation
    execution_database_id: str = Field(default="")  # Database for execution logs
    auto_sync: bool = Field(default=True)  # Auto-sync workflows on completion


class Settings(BaseSettings):
    """
    Main application settings.
    
    Loads from environment variables with NEXUS_RAY_ prefix.
    Example: NEXUS_RAY_KAFKA__BOOTSTRAP_SERVERS=localhost:9092
    """
    
    # Application
    app_name: str = Field(default="Nexus Ray")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")  # development, staging, production
    debug: bool = Field(default=True)
    
    # Component settings
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    vector_memory: VectorMemorySettings = Field(default_factory=VectorMemorySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    api: APISettings = Field(default_factory=APISettings)
    workflow: WorkflowSettings = Field(default_factory=WorkflowSettings)
    notion: NotionSettings = Field(default_factory=NotionSettings)
    
    class Config:
        env_prefix = "NEXUS_RAY_"
        env_nested_delimiter = "__"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance (singleton).
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.
    
    Returns:
        New settings instance
    """
    global _settings
    _settings = Settings()
    return _settings


# Example .env file content:
"""
# Nexus Ray Configuration

# Application
NEXUS_RAY_ENVIRONMENT=development
NEXUS_RAY_DEBUG=true

# Kafka
NEXUS_RAY_KAFKA__BOOTSTRAP_SERVERS=localhost:9092
NEXUS_RAY_KAFKA__CLIENT_ID=nexus-ray-dev
NEXUS_RAY_KAFKA__GROUP_ID=nexus-ray-group-dev

# Database
NEXUS_RAY_DATABASE__URL=postgresql://user:pass@localhost/nexus_ray

# LLM
NEXUS_RAY_LLM__DEFAULT_MODEL=mistral-7b-ov
NEXUS_RAY_LLM__DEVICE=CPU
NEXUS_RAY_LLM__QUANTIZATION=int8

# Vector Memory
NEXUS_RAY_VECTOR_MEMORY__BACKEND=chromadb
NEXUS_RAY_VECTOR_MEMORY__PERSIST_DIRECTORY=/data/vector_memory

# Observability
NEXUS_RAY_OBSERVABILITY__LOG_LEVEL=DEBUG
NEXUS_RAY_OBSERVABILITY__ENABLE_LLM_INSIGHTS=true

# API
NEXUS_RAY_API__PORT=8000
NEXUS_RAY_API__WORKERS=4

# Workflow
NEXUS_RAY_WORKFLOW__MAX_CONCURRENT_TASKS=20
NEXUS_RAY_WORKFLOW__STATE_PERSISTENCE_ENABLED=true
"""
