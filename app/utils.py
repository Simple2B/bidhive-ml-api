import boto3

from app.config import settings
from app.logger import log


def create_s3_client():

    try:
        client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        return client
    except Exception as err:
        log(log.ERROR, "S3 bucket client creation failed [%s]", err)
        raise


def create_s3_resource():
    try:
        resource = boto3.resource(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        return resource
    except Exception as err:
        log(log.ERROR, "S3 bucket resource creation failed [%s]", err)
        raise
