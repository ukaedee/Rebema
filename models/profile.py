from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)  # Userモデルと関連付け
    department = Column(String(100))
    hire_date = Column(Date)
    phone_number = Column(String(20))  # IntegerからStringに変更
    email_address = Column(String(100), nullable=False)
    location = Column(String(100))
    level_number = Column(Integer, nullable=False)
    experience_points = Column(Integer)
    assigned_quest = Column(String(100))
    profile_image = Column(String(255))
    description = Column(String(500))
    interests = Column(String(255))
    updated_at = Column(Date)

    # Userモデルとの関連付け
    user = relationship("User", back_populates="profile")
