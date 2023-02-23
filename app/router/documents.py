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
    # s3_client = create_s3_client()

    # def upload_s3(file: UploadFile):
    #     try:
    #         upload_name = os.path.join(str(user_info.company_id), file.filename)
    #         s3_client.upload_fileobj(
    #             file.file, Bucket=settings.S3_BUCKET_NAME, Key=upload_name
    #         )
    #     except Exception:
    #         raise HTTPException(
    #             status_code=400, detail=f"File uploading failed {file.filename}"
    #         )
    #     finally:
    #         file.file.close()

    # pool = ThreadPool(processes=len(files) * 2)

    # Just classic uploading through the pools - block execution until files will be uploaded
    # pool.map(upload_s3, files)

    # Async uploading through the pools: doesn't block server but returns response before all files will be uploaded
    # pool.async_map(upload_s3, files)

    # Uploading through the aioboto client: doesn't block server waits for the end of uploading
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

    # Using s3.TransferManager - doesn't upload at all
    # s3_dir = f"{user_info.company_id}/"

    # fast_s3_upload(boto3.Session(), settings.S3_BUCKET_NAME, s3_dir, files)

    log(
        log.INFO,
        "Files were uploaded to S3 bucket [%s] for company [%d]",
        settings.S3_BUCKET_NAME,
        user_info.company_id,
    )
