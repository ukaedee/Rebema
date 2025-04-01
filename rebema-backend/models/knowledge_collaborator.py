from sqlalchemy import Column, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base

class KnowledgeCollaborator(Base):
    __tablename__ = "knowledge_collaborators"

    knowledge_id = Column(Integer, ForeignKey("knowledges.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    # リレーションシップ
    knowledge = relationship("Knowledge", back_populates="collaborators")
    user = relationship("User", back_populates="collaborations") 