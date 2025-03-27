from fastapi import APIRouter

router = APIRouter()

@router.get("/ranking")
def get_ranking():
    return [
        {"id": 1, "username": "topuser", "level": 10},
        {"id": 2, "username": "runnerup", "level": 9},
    ]
