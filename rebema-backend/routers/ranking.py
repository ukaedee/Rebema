from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from models.database import get_db
from models.user import User
from models.user_activity import UserActivity
from core.security import get_current_user

router = APIRouter()

@router.get("/points")
async def get_points_ranking(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # ポイントに基づくランキング
    ranking = db.query(User).order_by(User.points.desc()).limit(limit).all()
    return ranking

@router.get("/level")
async def get_level_ranking(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # レベルに基づくランキング
    ranking = db.query(User).order_by(User.level.desc(), User.current_xp.desc()).limit(limit).all()
    return ranking

@router.get("/activity")
async def get_activity_ranking(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # アクティビティ数に基づくランキング
    ranking = (
        db.query(
            User,
            func.count(UserActivity.id).label('activity_count')
        )
        .join(UserActivity)
        .group_by(User.id)
        .order_by(func.count(UserActivity.id).desc())
        .limit(limit)
        .all()
    )
    return ranking

@router.get("/my-rank")
async def get_my_rank(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ポイントランキングでの自分の順位
    points_rank = (
        db.query(func.count(User.id))
        .filter(User.points > current_user.points)
        .scalar() + 1
    )
    
    # レベルランキングでの自分の順位
    level_rank = (
        db.query(func.count(User.id))
        .filter(
            (User.level > current_user.level) |
            ((User.level == current_user.level) & (User.current_xp > current_user.current_xp))
        )
        .scalar() + 1
    )
    
    return {
        "points_rank": points_rank,
        "level_rank": level_rank
    } 