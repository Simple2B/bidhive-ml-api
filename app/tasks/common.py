from celery import shared_task

from app import model as m
from app.logger import log
from app.database import get_db
from app.service import parse_document, parse_local_document
from app.utils import create_s3fs


@shared_task(name="test_task")
def test_task():
    parse_local_document()


@shared_task(name="parse_file")
def parse_file(file_id: int):
    """
    Celery task for parsing process of the uploaded file

    Args:
        file_id (int): id of record with file info in db
    """

    # Retrieve record with file information from db
    db_iter = get_db()
    db = next(db_iter)
    file_data = db.query(m.UploadedFile).get(file_id)

    log(log.DEBUG, "Celery started parsing file [%s]", file_data.filename)

    s3_fs = create_s3fs()

    # Parse file if it wasn't processed previously
    if not file_data.processed:
        parse_document(file_data, s3_fs)

    # Mark file as processed
    file_data.processed = True
    db.commit()
    log(log.DEBUG, "Celery succesfully processed file [%s]", file_data.filename)
