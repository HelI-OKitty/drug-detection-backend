from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str = "drug_db"

    model_config = {"env_file": ".env"}


settings = Settings()
