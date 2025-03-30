# models/project.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .database import Base
import enum

# ステータスの列挙型
class ProjectStatus(str, enum.Enum):
    draft = "立案中"
    in_progress = "施行中"
    completed = "施行済み"

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    description = Column(String(500))
    status = Column(Enum(ProjectStatus), default=ProjectStatus.draft)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="projects")

    comments = relationship("Comment", back_populates="project")
