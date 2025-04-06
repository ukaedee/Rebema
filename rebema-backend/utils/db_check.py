from sqlalchemy import text
from models.database import engine
import time

def check_database_connection():
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            # データベース接続をテスト
            with engine.connect() as connection:
                # 基本的な接続テスト
                connection.execute(text("SELECT 1"))
                print(f"✅ データベース接続テスト成功 (試行回数: {attempt + 1})")
                
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
            print(f"❌ データベース接続エラー (試行回数: {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"⏳ {retry_delay}秒後に再試行します...")
                time.sleep(retry_delay)
            else:
                print("❌ 最大試行回数に達しました。データベース接続に失敗しました。")
                return False

if __name__ == "__main__":
    check_database_connection() 