from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Knowledge(Base):
    __tablename__ = "knowledges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    method = Column(String(255))
    target = Column(String(255))
    description = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)

    # リレーションシップ
    author = relationship("User", back_populates="knowledges")
    files = relationship("File", back_populates="knowledge")
    comments = relationship("Comment", back_populates="knowledge")
    collaborators = relationship("KnowledgeCollaborator", back_populates="knowledge") 