from celery import shared_task

from app import model as m
from app.logger import log
from app.database import get_db
from app.service import parse_document, parse_local_document


@shared_task(name="test_task")
def test_task():
    parse_local_document()


@shared_task(name="parse_file")
def parse_file(file_id: int):
    db_iter = get_db()
    db = next(db_iter)
    file_data = db.query(m.UploadedFile).get(file_id)

    parse_document(file_data)

    file_data.processed = True
    db.commit()
