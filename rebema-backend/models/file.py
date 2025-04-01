from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_id = Column(Integer, ForeignKey("knowledges.id"))
    file_name = Column(String(255))
    file_url = Column(String(255))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # リレーションシップ
    knowledge = relationship("Knowledge", back_populates="files") 