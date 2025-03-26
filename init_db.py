# init_db.py
from models.database import Base, engine
from models.user import User  # ← モデル増やしたらここに追加

Base.metadata.create_all(bind=engine)