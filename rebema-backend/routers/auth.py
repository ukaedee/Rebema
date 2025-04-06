from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import os
from azure.storage.blob import BlobServiceClient, ContentSettings

from models.database import get_db
from models.user import User
from models.knowledge import Knowledge
from models.comment import Comment
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user
)

router = APIRouter()

# Azure Blob Storage設定
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "user-avatars")

# Blob Service Clientの初期化
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    department: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    level: int
    points: int
    current_xp: int
    avatar_url: Optional[str]
    department: Optional[str]

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    username: Optional[str] = None
    department: Optional[str] = None
    password: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # メールアドレスの重複チェック
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # ユーザー名の重複チェック
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # 新規ユーザー作成
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        username=user_data.username,
        department=user_data.department
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "User created successfully"}

@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    # メールアドレスでユーザーを検索
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "accessToken": access_token,
        "tokenType": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.username,
            "department": user.department,
            "level": user.level,
            "hasAvatar": user.avatar_data is not None,
            "avatarContentType": user.avatar_content_type
        }
    }

@router.get("/me")
async def read_users_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ナレッジ数を取得
    knowledge_count = db.query(Knowledge).filter(
        Knowledge.author_id == current_user.id
    ).count()
    
    # コメント数を取得
    comment_count = db.query(Comment).filter(
        Comment.author_id == current_user.id
    ).count()
    
    # 最近の活動を取得（最新5件のナレッジとコメント）
    recent_knowledge = db.query(Knowledge).filter(
        Knowledge.author_id == current_user.id
    ).order_by(Knowledge.created_at.desc()).limit(5).all()
    
    recent_comments = db.query(Comment).filter(
        Comment.author_id == current_user.id
    ).order_by(Comment.created_at.desc()).limit(5).all()
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "department": current_user.department,
        "avatar_url": current_user.avatar_url,
        "experience_points": current_user.experience_points,
        "level": current_user.level,
        "stats": {
            "knowledge_count": knowledge_count,
            "comment_count": comment_count
        },
        "recent_activity": {
            "knowledge": [
                {
                    "id": k.id,
                    "title": k.title,
                    "created_at": k.created_at
                } for k in recent_knowledge
            ],
            "comments": [
                {
                    "id": c.id,
                    "content": c.content,
                    "knowledge_id": c.knowledge_id,
                    "created_at": c.created_at
                } for c in recent_comments
            ]
        }
    }

@router.put("/me")
async def update_profile(
    profile: UserProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if profile.username is not None:
        # ユーザー名の重複チェック
        existing_user = db.query(User).filter(
            User.username == profile.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        current_user.username = profile.username
    
    if profile.department is not None:
        current_user.department = profile.department
    
    if profile.password is not None:
        current_user.hashed_password = get_password_hash(profile.password)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "department": current_user.department,
        "avatar_url": current_user.avatar_url,
        "experience_points": current_user.experience_points,
        "level": current_user.level
    }

@router.post("/me/avatar")
async def update_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ファイルタイプの検証
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    try:
        # Azure Blob Storageにアップロード
        blob_name = f"avatars/{current_user.id}/{file.filename}"
        blob_client = container_client.get_blob_client(blob_name)
        
        file_content = await file.read()
        blob_client.upload_blob(
            file_content,
            content_settings=ContentSettings(content_type=file.content_type),
            overwrite=True
        )
        
        # ユーザーのavatar_urlを更新
        current_user.avatar_url = blob_client.url
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        
        return {
            "avatar_url": current_user.avatar_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 