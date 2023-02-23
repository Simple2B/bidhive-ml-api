from fastapi import APIRouter, HTTPException, Depends
from starlette.status import HTTP_403_FORBIDDEN

from app import schema
from app.oauth2 import get_user_info

router = APIRouter(tags=["Search"], prefix="/search")


@router.post("/prompt/", response_model=schema.SearchPrompt)
async def search_by_prompt(
    prompt: schema.SearchPrompt, user_info: schema.UserInfo = Depends(get_user_info)
):
    # Currently just returns the prompt back to user
    return prompt
