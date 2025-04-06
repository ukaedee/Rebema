from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel

from models.database import get_db
from models.user import User
from models.user_activity import UserActivity
from core.security import get_current_user

router = APIRouter(prefix="/ranking", tags=["ranking"])

class RankingResponse(BaseModel):
    id: int
    position: str
    name: str
    department: str
    level: int
    avatar_url: str | None

def get_position_suffix(position: int) -> str:
    if position % 10 == 1 and position != 11:
        return "st"
    elif position % 10 == 2 and position != 12:
        return "nd"
    elif position % 10 == 3 and position != 13:
        return "rd"
    return "th"

@router.get("/level", response_model=List[RankingResponse])
async def get_level_ranking(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    # レベルに基づくランキング
    users = (
        db.query(User)
        .order_by(User.level.desc(), User.experience_points.desc())
        .limit(limit)
        .all()
    )
    
    ranking_list = []
    for i, user in enumerate(users, 1):
        position = f"{i}{get_position_suffix(i)}"
        ranking_list.append({
            "id": user.id,
            "position": position,
            "name": user.username,
            "department": user.department or "所属なし",
            "level": user.level,
            "avatar_url": user.avatar_url
        })
    
    return ranking_list

@router.get("/points", response_model=List[RankingResponse])
async def get_points_ranking(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    # ポイントに基づくランキング
    users = (
        db.query(User)
        .order_by(User.points.desc())
        .limit(limit)
        .all()
    )
    
    ranking_list = []
    for i, user in enumerate(users, 1):
        position = f"{i}{get_position_suffix(i)}"
        ranking_list.append({
            "id": user.id,
            "position": position,
            "name": user.username,
            "department": user.department or "所属なし",
            "level": user.level,
            "avatar_url": user.avatar_url
        })
    
    return ranking_list

@router.get("/activity", response_model=List[RankingResponse])
async def get_activity_ranking(
    limit: int = 5,
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
    
    ranking_list = []
    for i, (user, _) in enumerate(ranking, 1):
        position = f"{i}{get_position_suffix(i)}"
        ranking_list.append({
            "id": user.id,
            "position": position,
            "name": user.username,
            "department": user.department or "所属なし",
            "level": user.level,
            "avatar_url": user.avatar_url
        })
    
    return ranking_list

@router.get("/me")
async def get_my_rank(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # レベルランキングでの自分の順位
    level_rank = (
        db.query(func.count(User.id))
        .filter(
            (User.level > current_user.level) |
            ((User.level == current_user.level) & (User.experience_points > current_user.experience_points))
        )
        .scalar() + 1
    )
    
    # ポイントランキングでの自分の順位
    points_rank = (
        db.query(func.count(User.id))
        .filter(User.points > current_user.points)
        .scalar() + 1
    )
    
    # アクティビティランキングでの自分の順位
    my_activity_count = (
        db.query(func.count(UserActivity.id))
        .filter(UserActivity.user_id == current_user.id)
        .scalar() or 0
    )
    
    activity_rank = (
        db.query(func.count())
        .from_self(
            db.query(User.id, func.count(UserActivity.id).label('count'))
            .join(UserActivity)
            .group_by(User.id)
            .having(func.count(UserActivity.id) > my_activity_count)
        )
        .scalar() or 0
    ) + 1
    
    return {
        "level_rank": {
            "position": f"{level_rank}{get_position_suffix(level_rank)}",
            "rank": level_rank
        },
        "points_rank": {
            "position": f"{points_rank}{get_position_suffix(points_rank)}",
            "rank": points_rank
        },
        "activity_rank": {
            "position": f"{activity_rank}{get_position_suffix(activity_rank)}",
            "rank": activity_rank
        }
    } 