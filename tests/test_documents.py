from pathlib import Path

from fastapi.testclient import TestClient
from starlette.status import HTTP_201_CREATED

from app.oauth2 import create_access_token
from app import schema
from app.config import TEST_DOCS_DIR, ABSOLUTE_DOCUMENTS_DIR_PATH


TEST_DATA = schema.UserInfo(user_id=56, company_id=78)


def test_documents_upload(client: TestClient):
    token = create_access_token(TEST_DATA)

    test_upload_file = Path(TEST_DOCS_DIR, "empty.docx")

    files = {"files": open(test_upload_file, "rb")}
    response = client.post(
        "/documents/upload/", files=files, headers={"Authorization": f"JWT {token}"}
    )

    assert response and response.status_code == HTTP_201_CREATED

    # remove the test file from the uploaded_docs directory
    uploaded_file = Path(
        ABSOLUTE_DOCUMENTS_DIR_PATH, str(TEST_DATA.company_id), "empty.docx"
    )

    assert uploaded_file.exists()

    uploaded_file.unlink()
