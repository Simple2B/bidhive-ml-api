from celery import shared_task

from app import model as m
from app.logger import log
from app.utils import create_s3_resource
from app.database import get_db
from app.config import settings


@shared_task(name="test_task")
def test_task(a: int, b: int):
    result = a + b
    log(log.INFO, "Result:[%d]", result)
    return result


@shared_task(name="parse_file")
def parse_file(file_id: int):
    db_iter = get_db()
    db = next(db_iter)
    file_data = db.query(m.UploadedFile).get(file_id)

    s3_resource = create_s3_resource()
    file = s3_resource.Object(
        bucket_name=f"{settings.S3_BUCKET_NAME}",
        key=f"{file_data.company_id}/{file_data.filename}",
    )

    def parse_script(fileobj):
        print(len(fileobj))
        pass

    parse_script(file.get()["Body"].read())

    file.delete()

    file_data.processed = True
    db.commit()
