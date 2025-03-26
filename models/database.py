import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path

# .envファイルのパスを正しく解決
env_path = Path(__file__).resolve().parent.parent / 'rebema-backend' / '.env'
print(f"Looking for .env at: {env_path}")  # デバッグ用
load_dotenv(dotenv_path=env_path)

# 環境変数からDB_URLを取得
DB_URL = os.getenv('DB_URL')
if DB_URL is None:
    raise ValueError("DB_URL is not set in .env file")

# エンジンの作成
engine = create_engine(DB_URL, echo=True)

# セッションの設定
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Baseクラスの作成
Base = declarative_base()
