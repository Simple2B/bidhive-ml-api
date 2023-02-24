from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True)
    filename = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime(), nullable=False)
    last_modified = Column(String(128), nullable=False)
    company_id = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(), default=datetime.now)
    file_size = Column(Integer, nullable=False)
    checksum = Column(Text, nullable=False)

    def __repr__(self):
        return f"<{self.id}: {self.filename}>"
