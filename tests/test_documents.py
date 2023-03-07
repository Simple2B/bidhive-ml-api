import os
from pathlib import Path
from tempfile import NamedTemporaryFile

# from moto import mock_s3

from fastapi import UploadFile
from fastapi.testclient import TestClient
from starlette.status import HTTP_201_CREATED
from sqlalchemy.orm import Session

from app import schema, model
from app.oauth2 import create_access_token
from app.config import TEST_DOCS_DIR, ABSOLUTE_DOCUMENTS_DIR_PATH, settings
from app.utils import check_file_format
from app.service import check_file_hash, save_file_info


TEST_DATA = schema.UserInfo(user_id=56, company_id=78, is_admin=True)


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


# Moto doesn't work with aioboto3, so this test can be used only for uploadin through the boto3
# @mock_s3
# def test_docs_s3_upload(client: TestClient):
#     # Create fake bucket on mocked client
#     s3_resource = create_s3_resource()
#     bucket = s3_resource.create_bucket(
#         Bucket=settings.S3_BUCKET_NAME,
#         CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
#     )

#     token = create_access_token(TEST_DATA)

#     test_files = [file for file in Path(TEST_DOCS_DIR).iterdir()]

#     files = [("files", open(file, "rb")) for file in test_files]
#     response = client.post(
#         "/documents/upload-s3/", files=files, headers={"Authorization": f"JWT {token}"}
#     )

#     assert response and response.status_code == 200

#     # Check existance of files on fake bucket
#     uploaded_docs = [
#         file.key for file in bucket.objects.filter(Prefix=f"{TEST_DATA.company_id}/")
#     ]

#     for test_file in test_files:
#         assert f"{TEST_DATA.company_id}/{test_file.name}" in uploaded_docs


def test_check_file_format():
    valid_inputs = [("Test_1.docx", ".docx"), ("Test_2.txt", ".txt")]
    invalid_inputs = [("Test_1.docx", ".txt"), ("Test_2.txt", ".docs")]

    for filename, format in valid_inputs:
        result = check_file_format(filename, format)
        assert result

    for filename, format in invalid_inputs:
        result = check_file_format(filename, format)
        assert not result


def test_save_file_info(db: Session):
    test_hash = "hjkwhiu94y89o9he91uhd01u0"
    test_s3_path = os.path.join(
        settings.S3_BUCKET_NAME, str(TEST_DATA.company_id), "testname"
    )
    file_info = schema.FileDbInfo(
        file_hash=test_hash,
        filename="Testname",
        company_id=TEST_DATA.company_id,
        contract_title="Test title",
        customer_name="Test customer",
        contract_value=1000000,
        currency_type="USD",
        s3_relative_path=test_s3_path,
    )
    file_id = save_file_info(db, file_info)

    db_info = db.query(model.UploadedFile).get(file_id)

    assert db_info and db_info.hash == test_hash


def test_check_file_hash(db: Session):
    test_file_hash = None
    with NamedTemporaryFile() as tmp_file:
        tmp_file.write(b"Test my file")
        tmp_file.seek(0)
        test_file = UploadFile(tmp_file.name, tmp_file)

        test_file_hash, exist = check_file_hash(db, test_file, TEST_DATA.company_id)
        assert test_file_hash and not exist

        test_s3_path = os.path.join(
            settings.S3_BUCKET_NAME, str(TEST_DATA.company_id), "testname"
        )

        file_info = schema.FileDbInfo(
            file_hash=test_file_hash,
            filename=test_file.filename,
            company_id=TEST_DATA.company_id,
            contract_title="Test title",
            customer_name="Test customer",
            contract_value=1000000,
            currency_type="USD",
            s3_relative_path=test_s3_path,
        )
        save_file_info(db, file_info)

        # Try to get hash in second time
        new_hash, exist = check_file_hash(db, test_file, TEST_DATA.company_id)
        assert new_hash == test_file_hash and exist

        # Chagne file a little bit and try to recieve hash after that
        tmp_file.write(b"Second part")
        tmp_file.seek(0)
        updated_test_file = UploadFile(tmp_file.name, tmp_file)

        updated_test_file_hash, exist = check_file_hash(
            db, updated_test_file, TEST_DATA.company_id
        )
        assert updated_test_file_hash and not exist
        assert updated_test_file_hash != test_file_hash
