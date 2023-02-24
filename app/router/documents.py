import os
import asyncio
import boto3
import aioboto3
from multiprocessing.pool import ThreadPool

from fastapi import APIRouter, UploadFile, Depends, File, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_201_CREATED

from app import schema
from app.logger import log
from app.oauth2 import get_user_info
from app.config import ABSOLUTE_DOCUMENTS_DIR_PATH, settings
from app.utils import create_s3_client, S3_CONNECT_PARAMS, fast_s3_upload
from app.service import check_dir_exist, save_files_localy

router = APIRouter(tags=["Documents"], prefix="/documents")


@router.post("/upload-localy/")
async def upload_documents(
    files: list[UploadFile] = File(...),
    user_info: schema.UserInfo = Depends(get_user_info),
):
    dir_path = check_dir_exist(ABSOLUTE_DOCUMENTS_DIR_PATH, user_info.company_id)

    save_files_localy(dir_path, files)

    return JSONResponse(
        status_code=HTTP_201_CREATED,
        content={"message": "Files were successfully uploaded localy"},
    )


@router.post("/upload-s3/")
async def upload_docs_s3(
    files: list[UploadFile] = File(...),
    user_info: schema.UserInfo = Depends(get_user_info),
):
    session = aioboto3.Session()

    async with session.client(**S3_CONNECT_PARAMS) as s3:
        for file in files:
            try:
                upload_name = os.path.join(str(user_info.company_id), file.filename)
                await s3.upload_fileobj(
                    file.file, Bucket=settings.S3_BUCKET_NAME, Key=upload_name
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"File uploading failed {file.filename}"
                )
            finally:
                file.file.close()

    log(
        log.INFO,
        "Files were uploaded to S3 bucket [%s] for company [%d]",
        settings.S3_BUCKET_NAME,
        user_info.company_id,
    )
