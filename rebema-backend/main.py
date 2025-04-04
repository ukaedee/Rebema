from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, knowledge, ranking, profile
from models.database import engine, Base
import os

# データベースのテーブルを作成
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rebema API")

# CORS設定
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 環境変数から取得
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
app.include_router(ranking.router, prefix="/ranking", tags=["ranking"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])

@app.get("/")
async def root():
    return {"message": "Welcome to Rebema API"} 