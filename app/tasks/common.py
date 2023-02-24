from celery import shared_task
from app.logger import log


@shared_task(name="test_task")
def test_task(a: int, b: int):
    result = a + b
    log(log.INFO, "Result:[%d]", result)
    return result
