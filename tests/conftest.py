import pytest
from typing import Iterator
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:

    with TestClient(app) as c:
        yield c
