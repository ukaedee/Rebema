# dependencies.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.user import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db)) -> User:
    # 仮のユーザー取得処理（本来はトークンから取得）
    user = db.query(User).filter(User.id == 12345).first()  # 例: ID=12345のユーザーを返す
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
