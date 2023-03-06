import docx2txt
import pandas as pd
from moto import mock_s3
from s3fs import S3FileSystem

from app.utils import create_s3fs, create_s3_resource, get_csv_dataset
from app.config import settings
from app import schema as s
from app.service.parsing import parse_text


TEST_DATA = s.UserInfo(user_id=12, company_id=14)


@mock_s3
def test_create_s3f3():
    s3_fs = create_s3fs()
    assert s3_fs
    assert isinstance(s3_fs, S3FileSystem)


# mock_s3 decorator doesn't work because of aioboto
# @mock_s3
# def test_get_csv_dataset():
#     s3_fs = create_s3fs()

#     # Create fake bucket on mocked client
#     s3_resource = create_s3_resource()
#     bucket = s3_resource.create_bucket(
#         Bucket=settings.S3_BUCKET_NAME,
#         CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
#     )

#     df = get_csv_dataset(s3_fs, TEST_DATA.company_id, ["question", "answer"])
#     assert df
#     assert isinstance(df, pd.DataFrame)
#     assert s3_fs.exists(f"{settings.S3_BUCKET_NAME}/{TEST_DATA.company_id}/dataset.csv")


def test_parse_text():
    filename = "tests/test_files/Expression of Interest Form - Tier 3 Weight Management Service.docx"
    doc = docx2txt.process(filename)

    result_df = parse_text(doc)
    assert not result_df.empty
    assert isinstance(result_df, pd.DataFrame)
