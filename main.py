from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "FastAPI ちゃんと動いてるよ〜✨"}
