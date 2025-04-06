from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
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
from utils.experience import add_experience

router = APIRouter()

# Azure Blob Storage設定
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "knowledge-files")

# Blob Service Clientの初期化
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)

class KnowledgeCreate(BaseModel):
    title: str
    method: str
    target: str
    description: str
    category: Optional[str] = None

class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    method: Optional[str] = None
    target: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

@router.post("/")
async def create_knowledge(
    knowledge_data: KnowledgeCreate,
    files: Optional[List[UploadFile]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ナレッジの作成
    knowledge = Knowledge(
        title=knowledge_data.title,
        method=knowledge_data.method,
        target=knowledge_data.target,
        description=knowledge_data.description,
        category=knowledge_data.category,
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
    
    # 経験値を追加
    add_experience(current_user, 10, db)
    
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
    categories: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # 基本クエリの作成
    query = db.query(Knowledge)

    # 検索フィルターの適用
    if search:
        search_filter = (
            Knowledge.title.ilike(f"%{search}%") |
            Knowledge.description.ilike(f"%{search}%") |
            Knowledge.method.ilike(f"%{search}%") |
            Knowledge.target.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # カテゴリーフィルターの適用
    if categories:
        category_list = [cat.strip() for cat in categories.split(",")]
        query = query.filter(Knowledge.category.in_(category_list))

    # 総件数の取得
    total = query.count()

    # ソート順の適用
    if sort_by == "title":
        order_column = Knowledge.title
    elif sort_by == "views":
        order_column = Knowledge.views
    else:  # デフォルトは created_at
        order_column = Knowledge.created_at

    if sort_order == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    # ページネーションの適用
    query = query.offset(skip).limit(limit)
    
    # 結果の取得
    knowledge_list = query.all()
    
    # レスポンスの作成
    results = []
    for knowledge in knowledge_list:
        # コメント数の取得
        comment_count = db.query(Comment).filter(
            Comment.knowledge_id == knowledge.id
        ).count()
        
        # ファイル数の取得
        file_count = db.query(FileModel).filter(
            FileModel.knowledge_id == knowledge.id
        ).count()
        
        # 著者情報の取得
        author = db.query(User).filter(User.id == knowledge.author_id).first()
        
        # コラボレーター情報の取得
        collaborators = db.query(KnowledgeCollaborator).filter(
            KnowledgeCollaborator.knowledge_id == knowledge.id
        ).all()
        collaborator_ids = [c.user_id for c in collaborators]
        collaborator_users = db.query(User).filter(User.id.in_(collaborator_ids)).all()
        
        knowledge_dict = {
            "id": knowledge.id,
            "title": knowledge.title,
            "description": knowledge.description,
            "method": knowledge.method,
            "target": knowledge.target,
            "category": knowledge.category,
            "views": knowledge.views,
            "created_at": knowledge.created_at,
            "updated_at": knowledge.updated_at,
            "comment_count": comment_count,
            "file_count": file_count,
            "author": {
                "id": author.id,
                "username": author.username,
                "avatar_url": author.avatar_url,
                "department": author.department
            },
            "collaborators": [
                {
                    "id": user.id,
                    "username": user.username,
                    "avatar_url": user.avatar_url,
                    "department": user.department
                }
                for user in collaborator_users
            ]
        }
        results.append(knowledge_dict)

    return {
        "total": total,
        "items": results,
        "skip": skip,
        "limit": limit,
        "search": search,
        "categories": categories,
        "sort_by": sort_by,
        "sort_order": sort_order
    }

@router.put("/{knowledge_id}")
async def update_knowledge(
    knowledge_id: int,
    knowledge_data: KnowledgeUpdate,
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
    
    # 更新対象のフィールドを設定
    if knowledge_data.title is not None:
        knowledge.title = knowledge_data.title
    if knowledge_data.method is not None:
        knowledge.method = knowledge_data.method
    if knowledge_data.target is not None:
        knowledge.target = knowledge_data.target
    if knowledge_data.description is not None:
        knowledge.description = knowledge_data.description
    if knowledge_data.category is not None:
        knowledge.category = knowledge_data.category
    
    knowledge.updated_at = datetime.utcnow()
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
    
    # 閲覧数をインクリメント
    knowledge.views += 1
    db.commit()
    
    # 関連データのカウント
    comment_count = db.query(Comment).filter(Comment.knowledge_id == knowledge_id).count()
    file_count = db.query(FileModel).filter(FileModel.knowledge_id == knowledge_id).count()
    
    return {
        "id": knowledge.id,
        "title": knowledge.title,
        "description": knowledge.description,
        "method": knowledge.method,
        "target": knowledge.target,
        "category": knowledge.category,
        "views": knowledge.views,
        "created_at": knowledge.created_at,
        "updated_at": knowledge.updated_at,
        "author": {
            "id": knowledge.author.id,
            "username": knowledge.author.username,
            "avatar_url": knowledge.author.avatar_url,
            "department": knowledge.author.department
        },
        "stats": {
            "comment_count": comment_count,
            "file_count": file_count
        }
    }

@router.post("/{knowledge_id}/comments")
async def create_comment(
    knowledge_id: int,
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ナレッジの存在確認
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge not found"
        )
    
    # コメントの作成
    comment = Comment(
        content=content,
        knowledge_id=knowledge_id,
        author_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # 経験値を追加
    add_experience(current_user, 10, db)
    
    return comment

@router.get("/{knowledge_id}/comments")
async def list_comments(
    knowledge_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # ナレッジの存在確認
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge not found"
        )
    
    # コメント一覧を取得
    comments = db.query(Comment)\
        .filter(Comment.knowledge_id == knowledge_id)\
        .order_by(Comment.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    total = db.query(Comment)\
        .filter(Comment.knowledge_id == knowledge_id)\
        .count()
    
    return {
        "total": total,
        "items": comments
    }

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # コメントの存在確認
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # 権限チェック
    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    # コメントの削除
    db.delete(comment)
    db.commit()
    
    return {"message": "Comment deleted successfully"}

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