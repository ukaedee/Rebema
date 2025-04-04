from sqlalchemy.orm import Session
from models.user import User

def add_experience(user: User, xp: int, db: Session) -> None:
    """
    ユーザーに経験値を追加し、レベルアップの処理を行う

    Args:
        user (User): 経験値を追加するユーザー
        xp (int): 追加する経験値
        db (Session): データベースセッション

    Note:
        - current_xpに経験値を加算
        - pointsに経験値を加算
        - レベルアップに必要な経験値に達した場合、レベルアップ処理を実行
        - レベルアップ後の必要経験値は level * 10
    """
    user.current_xp += xp
    user.points += xp
    required_xp = user.level * 10
    
    while user.current_xp >= required_xp:
        user.current_xp -= required_xp
        user.level += 1
        required_xp = user.level * 10
    
    db.commit() 