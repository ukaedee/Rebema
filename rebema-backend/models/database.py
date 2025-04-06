from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

# データベース接続情報を個別に取得
DB_HOST = os.getenv("MYSQL_HOST")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DB")
DB_PORT = os.getenv("MYSQL_PORT", "3306")

# SSL証明書のパス
SSL_CA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "DigiCertGlobalRootCA.crt.pem")

# データベースURLを構築
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# エンジンの作成
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "ssl": {
            "ca": SSL_CA_PATH,
            "ssl_mode": "VERIFY_IDENTITY"
        }
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
