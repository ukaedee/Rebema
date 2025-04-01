from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceExistsError

from models.database import get_db
from models.user import User
from models.knowledge import Knowledge
from models.file import File as FileModel
from models.comment import Comment
from models.knowledge_collaborator import KnowledgeCollaborator
from core.security import get_current_user

router = APIRouter()

# Azure Blob Storage設定
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "knowledge-files")

# Blob Service Clientの初期化
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)

@router.post("/")
async def create_knowledge(
    title: str,
    method: str,
    target: str,
    description: str,
    files: Optional[List[UploadFile]] = None,
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
            # Azure Blob Storageにファイルをアップロード
            blob_name = f"{knowledge.id}/{file.filename}"
            blob_client = container_client.get_blob_client(blob_name)
            
            # ファイルの内容をアップロード
            file_content = await file.read()
            blob_client.upload_blob(
                file_content,
                content_settings=ContentSettings(content_type=file.content_type),
                overwrite=True
            )
            
            # データベースにファイル情報を保存
            db_file = FileModel(
                knowledge_id=knowledge.id,
                file_name=file.filename,
                file_url=blob_client.url,
                content_type=file.content_type
            )
            db.add(db_file)
    
    db.commit()
    return knowledge

@router.post("/{knowledge_id}/files")
async def upload_files(
    knowledge_id: int,
    files: List[UploadFile] = File(...),
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
            detail="Not authorized to upload files"
        )
    
    uploaded_files = []
    for file in files:
        blob_name = f"{knowledge_id}/{file.filename}"
        blob_client = container_client.get_blob_client(blob_name)
        
        file_content = await file.read()
        blob_client.upload_blob(
            file_content,
            content_settings=ContentSettings(content_type=file.content_type),
            overwrite=True
        )
        
        db_file = FileModel(
            knowledge_id=knowledge_id,
            file_name=file.filename,
            file_url=blob_client.url,
            content_type=file.content_type
        )
        db.add(db_file)
        uploaded_files.append(db_file)
    
    db.commit()
    return uploaded_files

@router.get("/{knowledge_id}/files")
async def list_files(
    knowledge_id: int,
    db: Session = Depends(get_db)
):
    files = db.query(FileModel).filter(FileModel.knowledge_id == knowledge_id).all()
    return files

@router.get("/{knowledge_id}/files/{file_id}")
async def download_file(
    knowledge_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.knowledge_id == knowledge_id
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return {"file_url": file.file_url}

@router.get("/")
async def list_knowledge(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query(None, enum=["created_at", "views", "title"]),
    sort_order: Optional[str] = Query("desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db)
):
    query = db.query(Knowledge)
    
    if search:
        query = query.filter(
            (Knowledge.title.ilike(f"%{search}%")) |
            (Knowledge.description.ilike(f"%{search}%"))
        )
    
    if sort_by:
        sort_column = getattr(Knowledge, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    total = query.count()
    knowledges = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": knowledges
    }

@router.put("/{knowledge_id}")
async def update_knowledge(
    knowledge_id: int,
    title: Optional[str] = None,
    method: Optional[str] = None,
    target: Optional[str] = None,
    description: Optional[str] = None,
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
            detail="Not authorized to update this knowledge"
        )
    
    if title:
        knowledge.title = title
    if method:
        knowledge.method = method
    if target:
        knowledge.target = target
    if description:
        knowledge.description = description
    
    db.commit()
    db.refresh(knowledge)
    return knowledge

@router.delete("/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: int,
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
            detail="Not authorized to delete this knowledge"
        )
    
    # 関連するファイルをAzure Blob Storageから削除
    files = db.query(FileModel).filter(FileModel.knowledge_id == knowledge_id).all()
    for file in files:
        blob_name = f"{knowledge_id}/{file.file_name}"
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
    
    # データベースから削除
    db.delete(knowledge)
    db.commit()
    
    return {"message": "Knowledge deleted successfully"}

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