from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    # Database configuration
    database_url: str = Field(
        default='postgresql+asyncpg://postgres:postgres@localhost:5432/theoforge_dev',
        description="Database connection URL"
    )
    
    # JWT configuration
    jwt_secret_key: str = Field(
        default="your-secret-key",
        description="Secret key for JWT tokens"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT tokens"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )

    # Login configuration
    max_login_attempts: int = Field(
        default=5,
        description="Maximum number of failed login attempts before account lockout"
    )

    # CORS configuration
    backend_cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="List of origins that can access the API"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create settings instance
settings = Settings()