from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, profile, project, ranking, comments 

app = FastAPI()

# フロントと接続できるようCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では限定しよう
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(project.router)
app.include_router(ranking.router)
app.include_router(comments.router)



@app.get("/")
def hello():
    return {"message": "FastAPI ちゃんと動いてるよ〜✨"}
