from pydantic import  Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    max_login_attempts: int = Field(default=3)

    # Security and authentication configuration
    jwt_secret_key: str = "a_very_secret_key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # 15 minutes for access token
    refresh_token_expire_minutes: int = 1440  # 24 hours for refresh token
    
    # Email verification configuration
    require_email_verification: bool = Field(default=False)  # Set to False by default

    # Qdrant configuration
    qdrant_url: str = Field(default="http://qdrant:6333", description="URL for the Qdrant service")
    qdrant_collection: str = Field(default="theoforge_vectors", description="Name of the Qdrant collection")
    vector_dimension: int = Field(default=1536, description="Dimension of the vectors used for embeddings")

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
