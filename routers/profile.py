from fastapi import APIRouter

router = APIRouter(prefix="/profile")

@router.get("/me")
def get_profile():
    return {"name": "mockname", "department": "マーケティング"}

@router.put("/me")
def update_profile():
    return {"message": "updated"}

@router.get("/me/projects")
def my_projects():
    return [
        {"id": 1, "title": "案件A"},
        {"id": 2, "title": "案件B"},
    ]
