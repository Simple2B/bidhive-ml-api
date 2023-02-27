import os
import aioboto3
from sqlalchemy.orm import Session

from fastapi import APIRouter, UploadFile, Depends, File, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_201_CREATED

from app import schema
from app.logger import log
from app.oauth2 import get_user_info
from app.config import ABSOLUTE_DOCUMENTS_DIR_PATH, settings
from app.utils import S3_CONNECT_PARAMS, check_file_format
from app.service import (
    check_dir_exist,
    save_files_localy,
    check_file_hash,
    save_file_info,
)
from app.database import get_db
from app.tasks import parse_file

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
    db: Session = Depends(get_db),
):
    """
    Route for uploading .docx files to S3 bucket.

    Args:
        files (list[UploadFile]): list of files to upload
        user_info (schema.UserInfo): user information from access token
        db (Session): session of db connection

    Raises:
        HTTPException: if some file was not successfully uploaded
    """
    session = aioboto3.Session()

    async with session.client(**S3_CONNECT_PARAMS) as s3:
        for file in files:
            try:
                # Check that file has .docx format
                if not check_file_format(filename=file.filename, format=".docx"):
                    raise ValueError("The file should be only in .docx format")

                # Check if the file has been already uploaded
                file_hash, should_skip = check_file_hash(db, file, user_info.company_id)
                if should_skip:
                    continue

                # Upload file to S3 bucket
                upload_name = os.path.join(str(user_info.company_id), file.filename)
                await s3.upload_fileobj(
                    file.file, Bucket=settings.S3_BUCKET_NAME, Key=upload_name
                )

                # Save meta information about file to db
                file_id = save_file_info(db, file_hash, file, user_info.company_id)

                # Start parsing process in Celery
                parse_file.delay(file_id)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"File uploading failed {file.filename} error: {e}",
                )
            finally:
                file.file.close()

    log(
        log.INFO,
        "Files were uploaded to S3 bucket [%s] for company [%d]",
        settings.S3_BUCKET_NAME,
        user_info.company_id,
    )
