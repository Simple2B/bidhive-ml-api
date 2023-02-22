from pathlib import Path
from moto import mock_s3

from fastapi.testclient import TestClient
from starlette.status import HTTP_201_CREATED

from app import schema
from app.oauth2 import create_access_token
from app.config import TEST_DOCS_DIR, ABSOLUTE_DOCUMENTS_DIR_PATH, settings
from app.utils import create_s3_resource


TEST_DATA = schema.UserInfo(user_id=56, company_id=78)


def test_docs_local_upload(client: TestClient):
    token = create_access_token(TEST_DATA)

    test_files = [file for file in Path(TEST_DOCS_DIR).iterdir()]

    files = [("files", open(file, "rb")) for file in test_files]
    response = client.post(
        "/documents/upload-localy/",
        files=files,
        headers={"Authorization": f"JWT {token}"},
    )

    assert response and response.status_code == HTTP_201_CREATED

    # Check files existance in uploaded_docs directory
    expected_uploaded_files = [
        Path(ABSOLUTE_DOCUMENTS_DIR_PATH, str(TEST_DATA.company_id), file.name)
        for file in test_files
    ]

    for file in expected_uploaded_files:
        assert file.exists()

    # remove the test file and company dir from the uploaded_docs directory
    company_dir = Path(ABSOLUTE_DOCUMENTS_DIR_PATH, str(TEST_DATA.company_id))
    for file in company_dir.iterdir():
        file.unlink()
    company_dir.rmdir()


@mock_s3
def test_docs_s3_upload(client: TestClient):
    # Create fake bucket on mocked client
    s3_resource = create_s3_resource()
    bucket = s3_resource.create_bucket(Bucket=settings.S3_BUCKET_NAME)

    token = create_access_token(TEST_DATA)

    test_files = [file for file in Path(TEST_DOCS_DIR).iterdir()]

    files = [("files", open(file, "rb")) for file in test_files]
    response = client.post(
        "/documents/upload-s3/", files=files, headers={"Authorization": f"JWT {token}"}
    )

    assert response and response.status_code == 200

    # Check existance of files on fake bucket
    uploaded_docs = [
        file.key for file in bucket.objects.filter(Prefix=f"{TEST_DATA.company_id}/")
    ]

    for test_file in test_files:
        assert f"{TEST_DATA.company_id}/{test_file.name}" in uploaded_docs
