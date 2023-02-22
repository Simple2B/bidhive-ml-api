import os
from pathlib import Path
from shutil import copyfileobj

from fastapi import HTTPException, UploadFile
from starlette.status import HTTP_400_BAD_REQUEST

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
