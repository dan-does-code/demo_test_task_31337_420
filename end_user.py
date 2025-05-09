from sqlalchemy.orm import Session
from app.models.models import EndUser
from app.schemas.schemas import EndUserCreate, EndUserUpdate
from typing import List, Optional


class EndUserRepository:
    """Repository for end user operations"""

    @staticmethod
    def create(db: Session, end_user: EndUserCreate) -> EndUser:
        """Create a new end user"""
        db_end_user = EndUser(
            tg_user_id=end_user.tg_user_id,
            first_name=end_user.first_name,
            last_name=end_user.last_name,
            username=end_user.username
        )
        
        db.add(db_end_user)
        db.commit()
        db.refresh(db_end_user)
        return db_end_user

    @staticmethod
    def get_by_tg_user_id(db: Session, tg_user_id: int) -> Optional[EndUser]:
        """Get end user by Telegram user ID"""
        return db.query(EndUser).filter(EndUser.tg_user_id == tg_user_id).first()

    @staticmethod
    def get_or_create(db: Session, end_user: EndUserCreate) -> EndUser:
        """Get existing end user or create a new one if not exists"""
        db_end_user = EndUserRepository.get_by_tg_user_id(db, end_user.tg_user_id)
        if db_end_user:
            return db_end_user
        return EndUserRepository.create(db, end_user)

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[EndUser]:
        """Get all end users"""
        return db.query(EndUser).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, tg_user_id: int, end_user: EndUserUpdate) -> Optional[EndUser]:
        """Update end user"""
        db_end_user = EndUserRepository.get_by_tg_user_id(db, tg_user_id)
        if db_end_user:
            update_data = end_user.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_end_user, key, value)
            db.commit()
            db.refresh(db_end_user)
        return db_end_user

    @staticmethod
    def delete(db: Session, tg_user_id: int) -> bool:
        """Delete end user"""
        db_end_user = EndUserRepository.get_by_tg_user_id(db, tg_user_id)
        if db_end_user:
            db.delete(db_end_user)
            db.commit()
            return True
        return False