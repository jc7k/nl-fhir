"""
Configuration management for NL-FHIR
HIPAA Compliant: No secrets or PHI in configuration
Production Ready: Environment-based configuration
"""

import os
from typing import List, Optional
from pydantic import Field, BaseModel
try:
    from pydantic_settings import BaseSettings
except Exception:
    # Lightweight shim: fall back to BaseModel when pydantic-settings is unavailable
    class BaseSettings(BaseModel):  # type: ignore
        class Config:
            arbitrary_types_allowed = True


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    app_name: str = Field(default="nl-fhir-converter", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Security Settings
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "*.railway.app", "testserver"],
        env="ALLOWED_HOSTS"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    trusted_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "*.railway.app", "testserver"],
        env="TRUSTED_HOSTS"
    )
    
    # Performance Settings
    max_request_size_mb: int = Field(default=1, env="MAX_REQUEST_SIZE_MB")
    request_timeout_seconds: float = Field(default=30.0, env="REQUEST_TIMEOUT_SECONDS")
    rate_limit_requests_per_minute: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    workers: int = Field(default=4, env="WORKERS")
    
    # Logging Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Monitoring Settings
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_health_check: bool = Field(default=True, env="ENABLE_HEALTH_CHECK")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Future Epic 2 - NLP Pipeline
    spacy_model: str = Field(default="en_core_web_sm", env="SPACY_MODEL")
    medspacy_enabled: bool = Field(default=False, env="MEDSPACY_ENABLED")
    nlp_cache_enabled: bool = Field(default=False, env="NLP_CACHE_ENABLED")
    nlp_cache_ttl_seconds: int = Field(default=3600, env="NLP_CACHE_TTL_SECONDS")
    
    # Future Epic 3 - FHIR Integration
    hapi_fhir_url: Optional[str] = Field(default=None, env="HAPI_FHIR_URL")
    hapi_fhir_timeout_seconds: int = Field(default=10, env="HAPI_FHIR_TIMEOUT_SECONDS")
    fhir_validation_enabled: bool = Field(default=False, env="FHIR_VALIDATION_ENABLED")
    fhir_version: str = Field(default="R4", env="FHIR_VERSION")
    
    # Future Epic 4 - Reverse Validation
    # Summarization and safety (Epic 4)
    summarization_enabled: bool = Field(default=True, env="SUMMARIZATION_ENABLED")
    safety_validation_enabled: bool = Field(default=True, env="SAFETY_VALIDATION_ENABLED")
    llm_provider: Optional[str] = Field(default=None, env="LLM_PROVIDER")
    llm_model: Optional[str] = Field(default=None, env="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, env="LLM_TEMPERATURE")
    
    # Future Epic 5 - Deployment
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() in ["production", "prod"]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() in ["development", "dev"]
    
    @property
    def max_request_size_bytes(self) -> int:
        """Get max request size in bytes"""
        return self.max_request_size_mb * 1024 * 1024
    
    def get_log_config(self) -> dict:
        """Get logging configuration"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": self.log_format
                },
                "json": {
                    "format": "%(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json" if self.is_production else "default",
                    "stream": "ext://sys.stdout"
                }
            },
            "root": {
                "level": self.log_level,
                "handlers": ["console"]
            }
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings (for dependency injection)"""
    return settings
