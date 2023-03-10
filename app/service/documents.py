import os
import hashlib
from pathlib import Path
from shutil import copyfileobj
from typing import Tuple
from sqlalchemy.orm import Session

from fastapi import HTTPException, UploadFile
from starlette.status import HTTP_400_BAD_REQUEST

from app import model as m, schema as s
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
    """
    Function that create hash on the base of file object and
    Check if such file has already been downloaded.

    Args:
        db (Session): sqlalchemy Session connection to db
        fileobj (UploadFile): file-like object
        company_id (int): id of user's company in main Bidhive app

    Returns:
        Tuple[str, bool]: file hash and True/False (if such file hash already exist in db or not)
    """

    # Calculate file hash
    file_hash = hashlib.file_digest(fileobj.file, hashlib.sha256).hexdigest()
    log(log.DEBUG, "check_file_hash created hash for file [%s]", fileobj.filename)

    # Return cursor to the start of the file
    fileobj.file.seek(0)

    # Check existance in db
    file_in_db = (
        db.query(m.UploadedFile)
        .filter_by(
            company_id=company_id,
            filename=fileobj.filename,
            hash=file_hash,
        )
        .first()
    )
    already_exist = file_in_db is not None
    return (file_hash, already_exist)


def save_file_info(db: Session, file_info: s.FileDbInfo) -> int:
    """
    Fucntion that saves information abot uploaded file to db

    Args:
        db (Session): sqlalchemy Session connection to db
        file_info (s.FileDbInfo): file information in Pydantic model

    Returns:
        int: primary key of created record in db
    """

    # Create a record and save it
    uploaded_file = m.UploadedFile(
        filename=file_info.filename,
        company_id=file_info.company_id,
        hash=file_info.file_hash,
        contract_title=file_info.contract_title,
        customer_name=file_info.customer_name,
        contract_value=file_info.contract_value,
        currency_type=file_info.currency_type,
        s3_relative_path=file_info.s3_relative_path,
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    log(
        log.DEBUG, "Save_file_info succesfully worked for file [%s]", file_info.filename
    )

    return uploaded_file.id
