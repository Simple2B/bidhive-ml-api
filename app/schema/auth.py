from datetime import datetime
from pydantic import BaseModel


class AccessToken(BaseModel):
    access_token: str


class RefreshToken(BaseModel):
    refresh_token: str


class TokenSet(AccessToken):
    refresh_token: str


class UserInfo(BaseModel):
    user_id: int
    company_id: int


class TokenData(UserInfo):
    exp: datetime


class AuthInfo(BaseModel):
    user_info: UserInfo
    secret_key: str
