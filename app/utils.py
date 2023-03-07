import os
import boto3
import s3fs
import pandas as pd
from pathlib import Path

from app.config import settings
from app.logger import log
from app import schema as s


S3_CONNECT_PARAMS = s.S3ConnParams(
    service_name="s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def create_s3_client():
    """
    Function that creates boto3 S3 client

    Returns:
        boto3.session.Session.client: boto3 client
    """

    try:
        client = boto3.client(**S3_CONNECT_PARAMS.dict())
        return client
    except Exception as err:
        log(log.ERROR, "S3 bucket client creation failed [%s]", err)
        raise


def create_s3_resource():
    """
    Function that creates boto3 S3 resource

    Returns:
        boto3.session.Session.resource: boto3 resource
    """
    try:
        resource = boto3.resource(**S3_CONNECT_PARAMS.dict())
        return resource
    except Exception as err:
        log(log.ERROR, "S3 bucket resource creation failed [%s]", err)


def create_s3fs():
    """
    Function that creates S3FileSystem

    Returns:
        s3fs.S3FileSystem: file-system instance
    """
    try:
        s3_fs = s3fs.S3FileSystem(
            key=settings.AWS_ACCESS_KEY_ID, secret=settings.AWS_SECRET_ACCESS_KEY
        )
        return s3_fs
    except Exception as err:
        log(log.ERROR, "S3 bucket filesystem creation failed [%s]", err)


def check_file_format(filename: str, format: str) -> bool:
    file_format = Path(filename).suffix

    return bool(file_format == format)


def to_csv_on_s3(s3_fs: s3fs.S3FileSystem, df: pd.DataFrame, company_id: int):
    """
    Function for saving DataFrame on S3 bucket

    Args:
        s3_fs (s3fs.S3FileSystem): S3FileSystem session
        df (pd.DataFrame): dataframe that should be saved
        company_id (int): id of user's company in Bidhive main app

    Raises:
        err: _description_
    """
    try:
        # Path of dataset.csv on S3 bucket
        path_to_dataset = os.path.join(
            settings.S3_BUCKET_NAME, str(company_id), "dataset.csv"
        )

        # Save dataset
        df.to_csv(
            s3_fs.open(path_to_dataset, mode="wb"),
            index=True,
        )
    except Exception as err:
        log(
            log.ERROR,
            "Loading of dataset.csv on S3 bucket failed for company [%d]: [%s]",
            company_id,
            err,
        )
        raise err


def get_csv_dataset(
    s3_fs: s3fs.S3FileSystem, company_id: int, columns: list[str]
) -> pd.DataFrame:
    """
    Function that retrieve (or create if it is not exist) and then return company dataset

    Args:
        s3_fs (s3fs.S3FileSystem): S3FileSystem session
        company_id (int): id of user's company in Bidhive main app
        columns (list[str]): list of columns which should be present in dataset

    Returns:
        pd.DataFrame: company dataset in pandas DataFrame
    """

    # Path of dataset.csv on S3 bucket
    path_to_dataset = os.path.join(
        settings.S3_BUCKET_NAME, str(company_id), "dataset.csv"
    )
    # Check if it exists
    csv_exist = s3_fs.exists(path_to_dataset)

    if not csv_exist:
        # Create new company dataset.csv file on s3
        df = pd.DataFrame(columns=columns)
        df.to_csv(s3_fs.open(path_to_dataset, mode="wb"))

    # Retrieve dataset.csv
    df = pd.read_csv(
        s3_fs.open(path_to_dataset, mode="rb"),
        index_col=0,
    )

    return df
