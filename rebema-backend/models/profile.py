from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    bio = Column(Text)
    phone_number = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    # リレーションシップ
    user = relationship("User", back_populates="profile") 