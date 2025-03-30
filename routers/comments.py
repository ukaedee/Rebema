# routers/comments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.comment import Comment
from models.database import SessionLocal
from dependencies import get_current_user
from models.user import User
from pydantic import BaseModel

router = APIRouter()

# DBセッション依存性
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydanticスキーマ
class CommentCreate(BaseModel):
    content: str


@router.get("/projects/{project_id}/comments", tags=["Comments"])
def get_comments(project_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.project_id == project_id).order_by(Comment.created_at).all()

    return [
        {
            "comment_id": comment.id,
            "content": comment.content,
            "username": comment.user.username,
            "created_at": comment.created_at
        }
        for comment in comments
    ]

# コメントを追加するルート
@router.post("/projects/{project_id}/comments", tags=["Comments"])
def create_comment(
    project_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = Comment(
        content=comment_data.content,
        user_id=current_user.id,
        project_id=project_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {
        "message": "コメント追加完了！",
        "comment_id": comment.id,
        "created_at": comment.created_at
    }
