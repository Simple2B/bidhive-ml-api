from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean

from app.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True)
    filename = Column(String(length=256), nullable=False)
    company_id = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(), default=datetime.now)
    hash = Column(Text, nullable=False)
    processed = Column(Boolean, default=False)
    contract_title = Column(String(length=256), nullable=True)
    customer_name = Column(String(length=256), nullable=True)
    contract_value = Column(Integer, nullable=True)
    currency_type = Column(String(length=32), default="USD", nullable=False)
    s3_relative_path = Column(String(length=256), nullable=False)

    def __repr__(self):
        return f"<{self.id}: {self.filename}>"
