from fastapi import APIRouter

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

@router.delete("/{project_id}")
def delete_project(project_id: int):
    return {"message": "deleted"}
