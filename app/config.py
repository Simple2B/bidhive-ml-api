import os
from pydantic import BaseSettings


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ABSOLUTE_DOCUMENTS_DIR_PATH = os.path.join(BASE_DIR, "uploaded_docs")

TEST_DOCS_DIR = os.path.dirname("tests/test_files/")


class Settings(BaseSettings):
    JWT_SECRET: str = "<None>"
    REFRESH_SECRET: str = "<Longer-None>"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 3
    BIDHIVE_API_SECRET_KEY: str = "<key_example_12345>"

    class Config:
        env_file = ".env"


settings = Settings()
