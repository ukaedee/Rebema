from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.user import User
from dependencies import get_current_user  # 認証用 Depends

router = APIRouter()

# DBセッションを使うDepends関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 自分のプロフィール取得（ログイン必須）
@router.get("/profile/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "level": current_user.level
    }

# 任意ユーザーのプロフィール取得（ログイン不要 or 任意で制限）
@router.get("/profile/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "level": user.level
        # emailなどは公開しない想定なら除外OK
    }
