import os
import aioboto3
import uuid
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError

from fastapi import APIRouter, UploadFile, Depends, File, HTTPException, Form, status
from fastapi.responses import JSONResponse

from app import schema
from app.logger import log
from app.oauth2 import get_admin_info
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
    user_info: schema.UserInfo = Depends(get_admin_info),
):
    dir_path = check_dir_exist(ABSOLUTE_DOCUMENTS_DIR_PATH, user_info.company_id)

    save_files_localy(dir_path, files)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Files were successfully uploaded localy"},
    )


@router.post("/upload-s3/")
async def upload_docs_s3(
    contract_title: str | None = Form(default=None),
    customer_name: str | None = Form(default=None),
    contract_value: int | None = Form(default=None),
    currency_type: str = Form(default="USD"),
    files: list[UploadFile] = File(...),
    user_info: schema.UserInfo = Depends(get_admin_info),
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

    async with session.client(**S3_CONNECT_PARAMS.dict()) as s3:
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
                # Use uuid as filename on s3 to be sure, that it is unique
                file_uuid = uuid.uuid4().hex
                s3_relative_path = os.path.join(str(user_info.company_id), file_uuid)
                await s3.upload_fileobj(
                    file.file, Bucket=settings.S3_BUCKET_NAME, Key=s3_relative_path
                )

                log(
                    log.DEBUG,
                    "File [%s] with uuid [%s] successfully uploaded to S3",
                    file.filename,
                    file_uuid,
                )

                # Save meta information about file to db
                file_info = schema.FileDbInfo(
                    file_hash=file_hash,
                    filename=file.filename,
                    company_id=user_info.company_id,
                    contract_title=contract_title,
                    customer_name=customer_name,
                    contract_value=contract_value,
                    currency_type=currency_type,
                    s3_relative_path=s3_relative_path,
                )
                file_id = save_file_info(db, file_info)

                # Start parsing process in Celery
                parse_file.delay(file_id)
            except (ValueError, ClientError) as e:
                log(
                    log.ERROR,
                    "File uploading failed [%s] error: [%s]",
                    file.filename,
                    e,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
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
