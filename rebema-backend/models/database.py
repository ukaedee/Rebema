from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
SSL_CA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "DigiCertGlobalRootCA.crt.pem")

# ✅ URLはそのままにして、connect_argsでSSLオプションを渡す！
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "ssl": {
            "ca": SSL_CA_PATH
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
