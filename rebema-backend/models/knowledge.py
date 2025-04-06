from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Knowledge(Base):
    __tablename__ = "knowledges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    method = Column(Text)
    target = Column(Text)
    description = Column(Text)
    category = Column(String(100), nullable=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_id = Column(Integer, ForeignKey("users.id"))

    # リレーションシップ
    author = relationship("User", back_populates="knowledges")
    files = relationship("File", back_populates="knowledge", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="knowledge", cascade="all, delete-orphan")
    collaborators = relationship("KnowledgeCollaborator", back_populates="knowledge", cascade="all, delete-orphan")

    # インデックス
    __table_args__ = (
        Index('ix_knowledges_category', 'category'),
    ) 