import boto3
import s3fs
import pandas as pd
from pathlib import Path

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


def check_file_format(filename: str, format: str) -> bool:
    file_format = Path(filename).suffix

    return bool(file_format == format)


def to_csv_on_s3(df: pd.DataFrame, company_id):
    s3_fs = s3fs.S3FileSystem(
        key=settings.AWS_ACCESS_KEY_ID, secret=settings.AWS_SECRET_ACCESS_KEY
    )

    df.to_csv(
        s3_fs.open(f"{settings.S3_BUCKET_NAME}/{company_id}/dataset.csv", mode="wb"),
        index=True,
    )


def create_or_retriev_csv(company_id: int):
    s3_fs = s3fs.S3FileSystem(
        key=settings.AWS_ACCESS_KEY_ID, secret=settings.AWS_SECRET_ACCESS_KEY
    )
    csv_exist = s3_fs.exists(f"{settings.S3_BUCKET_NAME}/{company_id}/dataset.csv")

    if not csv_exist:
        # Create new company dataset.csv file on s3
        # Maybe it is better to use s3_f3.open_async()
        df = pd.DataFrame(columns=["question", "answer"])
        df.to_csv(
            s3_fs.open(f"{settings.S3_BUCKET_NAME}/{company_id}/dataset.csv", mode="wb")
        )

    df = pd.read_csv(
        s3_fs.open(f"{settings.S3_BUCKET_NAME}/{company_id}/dataset.csv", mode="rb"),
        index_col=0,
    )

    return df
