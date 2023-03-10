from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app import schema, model as m
from app.database import get_db
from app.oauth2 import get_user_info
from app.service import search_answers
from app.utils import create_s3fs, get_csv_dataset  # async_get_csv_dataset,
from app.logger import log


router = APIRouter(tags=["Search"], prefix="/search")


@router.post("/prompt/", response_model=list[schema.SearchResponse])
def search_by_prompt(
    prompt: schema.SearchPrompt,
    user_info: schema.UserInfo = Depends(get_user_info),
    db: Session = Depends(get_db),
):
    """
    Searching by recieved prompt on the user's company dataset

    Args:
        prompt (schema.SearchPrompt): user's searching prompt
        user_info (schema.UserInfo, optional): user's info from access token
        db (Session, optional): db connection session

    Returns:
        response (list[schema.SearchResponse]): list with closest answers
    """

    log(
        log.DEBUG,
        "Searching process start for user [%d]. Prompt: [%s]",
        user_info.user_id,
        prompt.prompt,
    )
    # s3_fs = create_s3fs(asynchronous=True)
    # df = await async_get_csv_dataset(s3_fs, user_info.company_id)
    s3_fs = create_s3fs()
    df = get_csv_dataset(s3_fs, user_info.company_id)

    # Get dataframe with answers
    answer_as_df = search_answers(df, prompt.prompt)

    response = list()
    # Form list with suitable answers on the base of dataframe
    for index, row in answer_as_df.iterrows():
        file_info_id = int(row["file_info_id"])
        question = row["question"]
        answer = row["answer"]
        file_info = db.query(m.UploadedFile).get(file_info_id)
        data = schema.SearchResponse(
            contract_title=file_info.contract_title,
            customer_name=file_info.customer_name,
            contract_value=file_info.contract_value,
            currancy_type=file_info.currency_type,
            question=question,
            answer=answer,
        )
        response.append(data)

    log(
        log.DEBUG,
        "Searching process succeed for user [%d]. Prompt: [%s]",
        user_info.user_id,
        prompt.prompt,
    )
    return response
