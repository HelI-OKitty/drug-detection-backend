from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str = "drug_db"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    TEXT_AI_URL: str = ""
    TEXT_AI_API_KEY: str = ""
    IMAGE_AI_URL: str = ""
    IMAGE_AI_API_KEY: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
