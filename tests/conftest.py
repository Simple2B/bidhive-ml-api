import os
import requests
import pytest
import time
from pathlib import Path
from s3fs import S3FileSystem
from typing import Iterator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import BASE_DIR, settings


ENDPOINT_URI = "http://127.0.0.1:3445"


@pytest.fixture
def client() -> Iterator[TestClient]:

    with TestClient(app) as c:
        yield c


@pytest.fixture
def db() -> Generator:
    # SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:

        def override_get_db() -> Generator:
            yield db

        app.dependency_overrides[get_db] = override_get_db

        yield db
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def s3_base():
    # writable local S3 system
    import shlex
    import subprocess

    try:
        # should fail since we didn't start server yet
        r = requests.get(ENDPOINT_URI)
    except Exception:
        pass
    else:
        if r.ok:
            raise RuntimeError("moto server already up")
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = "foo"
    my_env = os.environ.copy()
    my_venv = str((Path(BASE_DIR) / ".." / ".venv" / "bin").resolve())
    my_env["PATH"] = f":{my_venv}:{os.environ['PATH']}"
    proc = subprocess.Popen(
        shlex.split("moto_server -p 3445 -H 127.0.0.1"),
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        env=my_env,
    )

    timeout = 5
    while timeout > 0:
        try:
            print("polling for moto server")
            r = requests.get(ENDPOINT_URI)
            if r.ok:
                break
        except Exception:
            pass
        timeout -= 0.1
        time.sleep(0.1)
    print("server up")
    yield
    print("moto done")
    proc.terminate()
    proc.wait()


def get_boto3_client():
    from botocore.session import Session

    # NB: we use the sync botocore client for setup
    session = Session()
    return session.create_client("s3", endpoint_url=ENDPOINT_URI)


@pytest.fixture()
def s3(s3_base):
    client = get_boto3_client()
    client.create_bucket(
        Bucket=settings.S3_BUCKET_NAME,
        ACL="public-read",
        CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
    )

    S3FileSystem.clear_instance_cache()
    s3 = S3FileSystem(anon=False, client_kwargs={"endpoint_url": ENDPOINT_URI})
    s3.invalidate_cache()
    yield s3
