import os
import hashlib
from pathlib import Path
from shutil import copyfileobj
from typing import Tuple
from sqlalchemy.orm import Session

from fastapi import HTTPException, UploadFile
from starlette.status import HTTP_400_BAD_REQUEST

from app import model as m
from app.logger import log


def check_dir_exist(base_docs_dir: str, company_id: int) -> str:
    dir_path: str = os.path.join(base_docs_dir, str(company_id))
    if not Path(dir_path).exists():
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        except (FileNotFoundError, OSError) as err:
            log(log.ERROR, "An error accured in dir creation process: [%s]", err)
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="There was a problem with creating directory for your company",
            )
    log(log.INFO, "Directory for company was successfully created: [%s]", dir_path)
    return dir_path


def save_files_localy(dir_path: str, files: list[UploadFile]):
    for file in files:
        try:
            with open(
                os.path.join(dir_path, file.filename),
                "wb",
            ) as f:
                copyfileobj(file.file, f)
        except Exception as err:
            log(
                log.ERROR,
                "An error accured in [%s] creation process: [%s]",
                file.filename,
                err,
            )
            raise HTTPException(
                status_code=400, detail=f"There was a problem with file {file.filename}"
            )
        finally:
            file.file.close()
    log(log.INFO, "Files were successfully saved in path: [%s]", dir_path)


def check_file_hash(
    db: Session, fileobj: UploadFile, company_id: int
) -> Tuple[str, bool]:
    file_hash = hashlib.file_digest(fileobj.file, hashlib.sha256).hexdigest()

    # Return cursor to the start of the file
    fileobj.file.seek(0)

    file_in_db = (
        db.query(m.UploadedFile)
        .filter(
            m.UploadedFile.company_id == company_id,
            m.UploadedFile.filename == fileobj.filename,
            m.UploadedFile.hash == file_hash,
        )
        .first()
    )
    already_exist = True if file_in_db else False
    return (file_hash, already_exist)


def save_file_info(
    db: Session, file_hash: str, file: UploadFile, company_id: int
) -> int:
    uploaded_file = m.UploadedFile(
        filename=file.filename,
        company_id=company_id,
        hash=file_hash,
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    return uploaded_file.id
