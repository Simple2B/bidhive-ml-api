import os
import boto3
import botocore
import boto3.s3.transfer as s3_transfer
import aioboto3

from app.config import settings
from app.logger import log


S3_CONNECT_PARAMS = {
    "service_name": "s3",
    "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    "region_name": settings.AWS_REGION,
}


def create_s3_client():

    try:
        client = boto3.client(**S3_CONNECT_PARAMS)
        return client
    except Exception as err:
        log(log.ERROR, "S3 bucket client creation failed [%s]", err)
        raise


def create_s3_resource():
    try:
        resource = boto3.resource(**S3_CONNECT_PARAMS)
        return resource
    except Exception as err:
        log(log.ERROR, "S3 bucket resource creation failed [%s]", err)
        raise
