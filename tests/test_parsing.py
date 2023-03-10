import os
import docx2txt
import pytest
import pandas as pd
from s3fs import S3FileSystem
from moto import mock_s3
from sqlalchemy.orm import Session

from app.utils import create_s3fs, get_csv_dataset, to_csv_on_s3
from app.config import settings, COLUMNS
from app import schema as s, model as m
from app.service.parsing import parse_text, parse_document
from app.service.documents import save_file_info


TEST_DATA = s.UserInfo(user_id=12, company_id=87, is_admin=True)
DATASET_PATH = os.path.join(
    settings.S3_BUCKET_NAME, str(TEST_DATA.company_id), "dataset.csv"
)


@mock_s3
def test_create_s3f3():
    s3_fs = create_s3fs()
    assert s3_fs
    assert isinstance(s3_fs, S3FileSystem)


def test_get_csv_dataset(s3: S3FileSystem):
    df = get_csv_dataset(s3, TEST_DATA.company_id, COLUMNS)
    assert isinstance(df, pd.DataFrame)
    assert s3.exists(DATASET_PATH)


def test_parse_text():
    filename = "tests/test_files/Expression of Interest Form - Tier 3 Weight Management Service.docx"
    doc = docx2txt.process(filename)

    result_df = parse_text(12, doc)
    assert not result_df.empty
    assert isinstance(result_df, pd.DataFrame)


def test_to_csv_on_s3(s3: S3FileSystem):
    # Create dataframe and load it on fake bucket
    df = pd.DataFrame(columns=COLUMNS)
    to_csv_on_s3(s3, df, TEST_DATA.company_id)

    # Check if csv exists on fake bucket
    assert s3.exists(DATASET_PATH)


# NOTE: skip this test because it run parse_document() function that use OpeanAI
@pytest.mark.skip
def test_parse_document(s3: S3FileSystem, db: Session):
    test_s3_path = os.path.join(
        settings.S3_BUCKET_NAME, str(TEST_DATA.company_id), "testname"
    )
    test_s3_relative_path = os.path.join(str(TEST_DATA.company_id), "testname")
    test_file = open(
        "tests/test_files/Expression of Interest Form - Tier 3 Weight Management Service.docx",
        "rb",
    )

    # Upload test file on fake bucket
    with s3.open(test_s3_path, mode="wb") as document:
        document.write(test_file.read())
    assert s3.exists(test_s3_path)

    # Save info about the file
    file_info = s.FileDbInfo(
        file_hash="jhckajhcsasoh28ue80",
        filename="testname",
        company_id=TEST_DATA.company_id,
        contract_title="Test title",
        customer_name="Test customer",
        contract_value=1000000,
        currency_type="USD",
        s3_relative_path=test_s3_relative_path,
    )
    file_id = save_file_info(db, file_info)

    file_data = db.query(m.UploadedFile).get(file_id)
    parse_document(file_data, s3)

    # Check if the dataset apperd in bucket after parsing
    assert s3.exists(DATASET_PATH)
