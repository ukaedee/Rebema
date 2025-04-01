from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..models.database import get_db
from ..models.user import User
from ..models.knowledge import Knowledge
from ..models.file import File
from ..models.comment import Comment
from ..models.knowledge_collaborator import KnowledgeCollaborator
from ..core.security import get_current_user

router = APIRouter()

@router.post("/")
async def create_knowledge(
    title: str,
    method: str,
    target: str,
    description: str,
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ナレッジの作成
    knowledge = Knowledge(
        title=title,
        method=method,
        target=target,
        description=description,
        author_id=current_user.id
    )
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    
    # ファイルのアップロード処理
    if files:
        for file in files:
            # ここではファイルの保存処理を実装する必要があります
            # 例: Azure Blob Storageへのアップロード
            file_url = "dummy_url"  # 実際のファイルURLに置き換える
            db_file = File(
                knowledge_id=knowledge.id,
                file_name=file.filename,
                file_url=file_url
            )
            db.add(db_file)
    
    db.commit()
    return knowledge

@router.get("/")
async def list_knowledge(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    knowledges = db.query(Knowledge).offset(skip).limit(limit).all()
    return knowledges

@router.get("/{knowledge_id}")
async def get_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db)
):
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge not found"
        )
    
    # 閲覧数のインクリメント
    knowledge.views += 1
    db.commit()
    
    return knowledge

@router.post("/{knowledge_id}/comments")
async def create_comment(
    knowledge_id: int,
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge not found"
        )
    
    comment = Comment(
        knowledge_id=knowledge_id,
        content=content,
        author_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment

@router.post("/{knowledge_id}/collaborators")
async def add_collaborator(
    knowledge_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge not found"
        )
    
    if knowledge.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add collaborators"
        )
    
    collaborator = KnowledgeCollaborator(
        knowledge_id=knowledge_id,
        user_id=user_id
    )
    db.add(collaborator)
    db.commit()
    
    return {"message": "Collaborator added successfully"} 