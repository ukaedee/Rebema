from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import relationship, Session
from models.database import get_db
from models.user import User
from models.project import Project
from auth import get_current_user

router = APIRouter(prefix="/projects")

@router.post("")
def create_project():
    return {"message": "created", "id": 99}

@router.get("")
def get_all_projects():
    return [
        {"id": 1, "title": "公開案件A"},
        {"id": 2, "title": "公開案件B"},
    ]

@router.get("/{project_id}")
def get_project(project_id: int):
    return {"id": project_id, "title": "案件詳細", "description": "詳細説明"}

@router.put("/{project_id}")
def update_project(project_id: int):
    return {"message": "updated"}

@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="自分のプロジェクトのみ削除できます")

    db.delete(project)
    db.commit()
    return {"message": "削除完了！"}

