from app import celery_app
from app.logger import log


@celery_app.task(name="test_task")
def test_task(a: int, b: int):
    result = a + b
    log(log.INFO, "Result:[%d]", result)
    return result
