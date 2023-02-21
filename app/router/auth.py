# from shutil import unregister_archive_format
from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_403_FORBIDDEN

from app import schema
from app.oauth2 import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    verify_api_key,
)

router = APIRouter(tags=["Authentication"], prefix="/auth")


@router.post("/tokens/", response_model=schema.TokenSet)
async def get_tokens(auth_info: schema.AuthInfo):
    """
    Route that returns tokens by user info
    Args:
        user_info (UserInfo): user information from Bidhive app
    Raises:
        HTTPException: 403 - Invalid Credentials
    Returns:
        Set of tokens
    """

    if not verify_api_key(auth_info.secret_key):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Secret key is incorrect"
        )

    access_token = create_access_token(auth_info.user_info)
    refresh_token = create_refresh_token(auth_info.user_info)

    return schema.TokenSet(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh-token/", response_model=schema.AccessToken)
async def refresh_token(refresh_token: schema.RefreshToken) -> schema.AccessToken:
    """
    The route that generate new access token on the base of valid refresh_token

    Args:
        refresh_token (RefreshToken): refresh_token value from body of request

    Returns:
        AccessToken: pydantic model with new access token
    """
    new_access_token = verify_refresh_token(refresh_token.refresh_token)

    return schema.AccessToken(access_token=new_access_token)
