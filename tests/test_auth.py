from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.datastructures import Headers

from app.oauth2 import (
    create_access_token,
    verify_access_token,
    get_user_info,
    create_refresh_token,
)
from app import schema
from app.config import settings


TEST_DATA = schema.UserInfo(user_id=56, company_id=78)


def test_access_token():
    token = create_access_token(TEST_DATA)
    assert token
    user_info = verify_access_token(token=token)
    assert user_info
    assert user_info.company_id == TEST_DATA.company_id
    assert user_info.user_id == TEST_DATA.user_id


def test_create_token(client: TestClient):
    request_data = schema.AuthInfo(
        user_info=TEST_DATA, secret_key=settings.BIDHIVE_API_SECRET_KEY
    )

    res = client.post("/auth/tokens/", json=request_data.dict())
    assert res and res.status_code == 200

    tokens = schema.TokenSet.parse_obj(res.json())
    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.refresh_token != tokens.access_token


def test_get_user_info():
    token = create_access_token(TEST_DATA)
    headers = Headers(
        {
            "Authorization": f"JWT {token}",
        }
    )
    request = Request(scope={"method": "GET", "type": "http", "headers": headers.raw})
    user_info = get_user_info(request)
    assert user_info.company_id == TEST_DATA.company_id
    assert user_info.user_id == TEST_DATA.user_id


def test_refresh_token(client: TestClient):
    user_info = schema.UserInfo(
        user_id=TEST_DATA.user_id, company_id=TEST_DATA.company_id
    )
    refresh_token = create_refresh_token(user_info)

    result = client.post(
        "/auth/refresh-token/", json={"refresh_token": f"{refresh_token}"}
    )
    assert result and result.status_code == 200

    new_access_token = schema.AccessToken.parse_obj(result.json())
    decoded_user_info = verify_access_token(new_access_token.access_token)

    assert decoded_user_info.user_id == user_info.user_id
    assert decoded_user_info.company_id == user_info.company_id
