from pydantic import BaseModel


class FileDbInfo(BaseModel):
    file_hash: str
    filename: str
    company_id: int
    contract_title: str | None
    customer_name: str | None
    contract_value: int | None
    currency_type: str
    s3_relative_path: str
