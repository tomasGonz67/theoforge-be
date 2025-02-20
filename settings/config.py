from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Database configuration
    database_url: str = Field(
        default='postgresql+asyncpg://user:password@localhost/authdb',
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

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create settings instance
settings = Settings()