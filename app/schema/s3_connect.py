from pydantic import BaseModel


class S3ConnParams(BaseModel):
    service_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
