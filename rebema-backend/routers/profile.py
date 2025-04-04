from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from models.database import get_db
from models.user import User
from models.knowledge import Knowledge
from core.security import get_current_user

router = APIRouter()

@router.get("/mypage")
async def get_mypage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 投稿ナレッジ数を取得
    knowledge_count = db.query(Knowledge)\
        .filter(Knowledge.author_id == current_user.id)\
        .count()
    
    # 総PV数を取得
    total_views = db.query(func.sum(Knowledge.views))\
        .filter(Knowledge.author_id == current_user.id)\
        .scalar() or 0
    
    # ナレッジ一覧を取得（title, views, created_at）
    knowledges = db.query(
        Knowledge.title,
        Knowledge.views,
        Knowledge.created_at
    )\
        .filter(Knowledge.author_id == current_user.id)\
        .order_by(Knowledge.created_at.desc())\
        .all()
    
    # レスポンスの整形
    knowledge_list = [
        {
            "title": k.title,
            "views": k.views,
            "created_at": k.created_at.isoformat()
        }
        for k in knowledges
    ]
    
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "level": current_user.level,
            "points": current_user.points,
            "current_xp": current_user.current_xp
        },
        "stats": {
            "knowledge_count": knowledge_count,
            "total_views": total_views
        },
        "knowledges": knowledge_list
    } 