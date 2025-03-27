from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login():
    return {"access_token": "dummy_token", "token_type": "bearer"}

@router.get("/me")
def me():
    return {"id": 1, "username": "mockuser", "level": 5}
