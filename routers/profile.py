from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.user import User
from dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/profile")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 自分のプロフィール表示
@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "level": current_user.level
    }

# 自分のプロフィール編集
class ProfileUpdate(BaseModel):
    username: str

@router.put("/me")
def update_my_profile(update: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.username = update.username
    db.commit()
    db.refresh(current_user)
    return {
        "message": "プロフィール更新完了！",
        "username": current_user.username
    }

# 他人 or 自分のプロフィール表示（ID指定）
@router.get("/{user_id}")
def get_profile_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "level": user.level
    }
