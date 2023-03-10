import pytest
from fastapi.testclient import TestClient

from app import schema
from app.oauth2 import create_access_token


TEST_DATA = schema.UserInfo(user_id=12, company_id=55, is_admin=True)


@pytest.mark.skip
def test_search_prompt(client: TestClient):
    token = create_access_token(TEST_DATA)

    test_prompt = schema.SearchPrompt(prompt="My test searching prompt")

    res = client.post(
        "/search/prompt/",
        json=test_prompt.dict(),
        headers={"Authorization": f"JWT {token}"},
    )

    assert res and res.status_code == 200
