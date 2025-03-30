from models.database import engine, Base
from models import user, project, comment  # 全モデルをimport

# テーブル作成（なければ作成される）
Base.metadata.create_all(bind=engine)
