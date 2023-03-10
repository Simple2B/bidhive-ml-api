from datetime import datetime, timedelta

from fastapi import HTTPException
from jose import JWTError, jwt
from pydantic import ValidationError
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from app import schema
from .config import settings
from app.logger import log


SECRET_KEY = settings.JWT_SECRET
REFRESH_SECRET = settings.REFRESH_SECRET
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(data: schema.UserInfo) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = schema.TokenData(**data.dict(), exp=expire)

    return jwt.encode(token_data.dict(), SECRET_KEY)


def create_refresh_token(data: schema.UserInfo) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_data = schema.TokenData(**data.dict(), exp=expire)

    return jwt.encode(token_data.dict(), REFRESH_SECRET)


def verify_access_token(token: str) -> schema.UserInfo:
    log(log.INFO, "verify_access_token(%s)", token)
    try:
        payload = schema.TokenData.parse_obj(jwt.decode(token, SECRET_KEY))
        return schema.UserInfo(
            user_id=payload.user_id,
            company_id=payload.company_id,
            is_admin=payload.is_admin,
        )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=401,
            detail="Incorrect access token",
        )


def verify_refresh_token(refresh_token: str) -> str:
    log(log.INFO, "verify_refresh_token(%s)", refresh_token)
    try:
        payload = schema.TokenData.parse_obj(jwt.decode(refresh_token, REFRESH_SECRET))
        user_info = schema.UserInfo(
            user_id=payload.user_id,
            company_id=payload.company_id,
            is_admin=payload.is_admin,
        )
        return create_access_token(user_info)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=400,
            detail="Incorrect refresh token",
        )


def verify_api_key(secret_key: str) -> bool:
    if settings.BIDHIVE_API_SECRET_KEY == secret_key:
        return True

    return False


def get_token_from_header(request: Request) -> str:
    """
    This function returns access token from authorization header

    Args:
        request (Request): user's request

    Raises:
        HTTPException: if request doesn't contain Authorization header
        HTTPException: if access token prefix is not JWT

    Returns:
        str: access token from authorization header
    """
    authorization: str = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "JWT"},
        )

    scheme, token = authorization.split(" ")
    if scheme.lower() != "jwt":
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect access token prefix",
            headers={"WWW-Authenticate": "JWT"},
        )

    return token


def get_user_info(request: Request) -> schema.UserInfo:
    """
    The function that allows to achieve user_info from valid access token
    Use this function for authorization in routes where any user has access
    Args:
        request (Request): user's request

    Returns:
        schema.UserInfo: user's data
    """

    token = get_token_from_header(request)
    user_data = verify_access_token(token)

    return user_data


def get_admin_info(request: Request) -> schema.UserInfo:
    """
    This function allows to achieve user information and ensure that user is admin of company.
    Use this function for authorization in routes where accesshave only admins.

    Args:
        request (Request): user's request

    Raises:
        HTTPException: if user is not a company admin

    Returns:
        schema.UserInfo: user's data
    """
    token = get_token_from_header(request)
    user_data = verify_access_token(token)

    if not user_data.is_admin:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="User must be company admin to use this route",
            headers={"WWW-Authenticate": "JWT"},
        )

    return user_data
