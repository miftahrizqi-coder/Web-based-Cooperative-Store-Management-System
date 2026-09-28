from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str

    class Config:
        env_file = ".env"


settings = Settings()