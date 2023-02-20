from pydantic import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET: str = "<None>"
    REFRESH_SECRET: str = "<Longer-None>"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 3
    BIDHIVE_API_SECRET_KEY: str = "<key_example_12345>"

    class Config:
        env_file = ".env"


settings = Settings()
