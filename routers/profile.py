from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.user import User
from dependencies import get_current_user
from pydantic import BaseModel
from datetime import date
from models.profile import Profile

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

# プロフィール作成用のモデル
class ProfileCreate(BaseModel):
    department: str | None = None
    hire_date: date | None = None
    phone_number: str | None = None
    email_address: str
    location: str | None = None
    level_number: int
    experience_points: int | None = None
    assigned_quest: str | None = None
    profile_image: str | None = None
    description: str | None = None
    interests: str | None = None
    updated_at: date | None = None

# プロフィール更新用のモデル
class ProfileUpdate(ProfileCreate):
    pass

# ユーザー名更新用のモデル
class UsernameUpdate(BaseModel):
    username: str

@router.put("/me")
def update_my_profile(update: UsernameUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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

# 自分の詳細プロフィールを登録（1回限り）
@router.post("/me/details")
def create_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="プロフィールは既に存在します")

    profile = Profile(user_id=current_user.id, **profile_data.dict())
    db.add(profile)
    db.commit()
    return {"message": "プロフィール登録完了！"}

# 自分の詳細プロフィール取得
@router.get("/me/details")
def get_profile_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="プロフィールが未登録です")
    return profile

@router.put("/me/details")
def update_profile_details(
    update_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="プロフィールが存在しません")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return {"message": "プロフィールを更新しました！"}
