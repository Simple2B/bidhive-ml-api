import os
from pathlib import Path
from shutil import copyfileobj

from fastapi import APIRouter, UploadFile, Depends, File
from fastapi.responses import JSONResponse
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from app import schema
from app.oauth2 import get_user_info
from app.config import ABSOLUTE_DOCUMENTS_DIR_PATH

router = APIRouter(tags=["Documents"], prefix="/documents")


def check_dir_exist(base_docs_dir: str, company_id: int) -> str:
    dir_path: str = os.path.join(base_docs_dir, str(company_id))
    if not Path(dir_path).exists():
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        except (FileNotFoundError, OSError):
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content="There was a problem with creating directory for your company",
            )
    return dir_path


def save_files_localy(dir_path: str, files: list[UploadFile]):
    for file in files:
        try:
            with open(
                os.path.join(dir_path, file.filename),
                "wb",
            ) as f:
                copyfileobj(file.file, f)
        except Exception:
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content=f"There was a problem with file {file.filename}",
            )
        finally:
            file.file.close()


@router.post("/upload/")
async def upload_documents(
    files: list[UploadFile] = File(...),
    user_info: schema.UserInfo = Depends(get_user_info),
):
    dir_path = check_dir_exist(ABSOLUTE_DOCUMENTS_DIR_PATH, user_info.company_id)

    save_files_localy(dir_path, files)

    return JSONResponse(
        status_code=HTTP_201_CREATED,
        content={"message": "Files were successfully uploaded"},
    )
