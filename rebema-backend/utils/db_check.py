from sqlalchemy import text
from models.database import engine

def check_database_connection():
    try:
        # データベース接続をテスト
        with engine.connect() as connection:
            # 簡単なクエリを実行
            result = connection.execute(text("SELECT 1"))
            print("✅ データベース接続テスト成功")
            
            # ユーザーテーブルの存在確認
            result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"✅ 確認されたテーブル: {', '.join(tables)}")
            
            # ユーザー数の確認
            result = connection.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"✅ ユーザー数: {user_count}")
            
            return True
    except Exception as e:
        print(f"❌ データベース接続エラー: {str(e)}")
        return False

if __name__ == "__main__":
    check_database_connection() 