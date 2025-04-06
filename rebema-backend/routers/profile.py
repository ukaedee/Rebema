from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import os
from sqlalchemy.sql import func

from models.database import get_db
from models.user import User
from models.profile import Profile
from models.knowledge import Knowledge
from models.comment import Comment
from core.security import get_current_user, get_password_hash

router = APIRouter(prefix="/profile", tags=["profile"])

class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    department: Optional[str] = None
    password: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None

@router.get("/me")
async def read_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # プロフィール情報を取得
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        # プロフィールが存在しない場合は作成
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
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
        "email": current_user.email,
        "department": current_user.department,
        "avatar_url": current_user.avatar_url,
        "experience_points": current_user.experience_points,
        "level": current_user.level,
        "bio": profile.bio,
        "phone_number": profile.phone_number,
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
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if profile_data.username is not None:
        # ユーザー名の重複チェック
        existing_user = db.query(User).filter(
            User.username == profile_data.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        current_user.username = profile_data.username
    
    if profile_data.department is not None:
        current_user.department = profile_data.department
    
    if profile_data.password is not None:
        current_user.password_hash = get_password_hash(profile_data.password)
    
    # プロフィール情報の更新
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
    
    if profile_data.bio is not None:
        profile.bio = profile_data.bio
    
    if profile_data.phone_number is not None:
        profile.phone_number = profile_data.phone_number
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    db.refresh(profile)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "department": current_user.department,
        "avatar_url": current_user.avatar_url,
        "experience_points": current_user.experience_points,
        "level": current_user.level,
        "bio": profile.bio,
        "phone_number": profile.phone_number
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
        # ファイルの内容を読み込む
        file_content = await file.read()
        
        # ユーザーのアバター情報を更新
        current_user.avatar_data = file_content
        current_user.avatar_content_type = file.content_type
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        
        return {
            "message": "Avatar updated successfully",
            "contentType": current_user.avatar_content_type
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me/avatar")
async def get_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.avatar_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    
    return Response(
        content=current_user.avatar_data,
        media_type=current_user.avatar_content_type
    )

@router.get("/mypage")
async def get_mypage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # プロフィール情報を取得
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # 登録ナレッジ数を取得
    knowledge_count = db.query(Knowledge).filter(
        Knowledge.author_id == current_user.id
    ).count()

    # 累積PV数を取得
    total_views = db.query(func.sum(Knowledge.views)).filter(
        Knowledge.author_id == current_user.id
    ).scalar() or 0

    # 次のレベルまでに必要な経験値を計算
    next_level_exp = (current_user.level + 1) * 100 - current_user.experience_points

    # 最近のナレッジを取得（最新5件）
    recent_knowledge = (
        db.query(Knowledge)
        .filter(Knowledge.author_id == current_user.id)
        .order_by(Knowledge.created_at.desc())
        .limit(5)
        .all()
    )

    # ナレッジリストの作成
    knowledge_list = []
    for k in recent_knowledge:
        # カテゴリーに基づくアイコンとカラーの設定
        icon, bg_color = get_category_icon_and_color(k.category)
        
        knowledge_list.append({
            "id": k.id,
            "title": k.title,
            "category": k.category,
            "icon": icon,
            "iconBgColor": bg_color,
            "author": current_user.username,
            "views": k.views,
            "createdAt": k.created_at.strftime("%Y年%m月%d日"),
            "content": k.description  # または整形されたコンテンツ
        })

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.username,
            "department": current_user.department or "所属なし",
            "level": current_user.level,
            "nextLevelExp": next_level_exp,
            "avatar_url": current_user.avatar_url,
            "bio": profile.bio,
            "stats": {
                "knowledgeCount": knowledge_count,
                "totalPageViews": total_views
            }
        },
        "knowledgeList": knowledge_list
    }

def get_category_icon_and_color(category: str) -> tuple[str, str]:
    """カテゴリーに基づいてアイコンと背景色を返す"""
    category_mapping = {
        "メール": ("💌", "#FFFBD6"),
        "電話": ("📞", "#F1FFCA"),
        "訪問": ("🏠", "#E0D6FF"),
        "その他": ("📝", "#FFE0D6"),
        # 他のカテゴリーも必要に応じて追加
    }
    
    return category_mapping.get(category, ("📝", "#FFE0D6"))  # デフォルト値 