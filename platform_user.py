from sqlalchemy.orm import Session
from app.models.models import PlatformUser
from app.schemas.schemas import PlatformUserCreate, PlatformUserUpdate
from typing import Optional, List
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PlatformUserRepository:
    """Repository for platform user operations"""

    @staticmethod
    def create(db: Session, platform_user: PlatformUserCreate) -> PlatformUser:
        """Create a new platform user"""
        
        try:
            db_platform_user = PlatformUser(tg_user_id=platform_user.tg_user_id)
            db.add(db_platform_user)
            db.commit()
            db.refresh(db_platform_user)
            logger.info(f"Created platform user: id={db_platform_user.id}, tg_user_id={platform_user.tg_user_id}")
            return db_platform_user
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating platform user: {str(e)}")
            raise

    @staticmethod
    def get_by_id(db: Session, platform_user_id: int) -> Optional[PlatformUser]:
        """Get platform user by ID"""
        return db.query(PlatformUser).filter(PlatformUser.id == platform_user_id).first()

    @staticmethod
    def get_by_tg_user_id(db: Session, tg_user_id: int) -> Optional[PlatformUser]:
        """Get platform user by Telegram user ID"""
        return db.query(PlatformUser).filter(PlatformUser.tg_user_id == tg_user_id).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[PlatformUser]:
        """Get all platform users"""
        return db.query(PlatformUser).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, platform_user_id: int, platform_user: PlatformUserUpdate) -> Optional[PlatformUser]:
        """Update platform user"""
        
        try:
            db_platform_user = PlatformUserRepository.get_by_id(db, platform_user_id)
            if db_platform_user:
                update_data = platform_user.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_platform_user, key, value)
                db.commit()
                db.refresh(db_platform_user)
                logger.info(f"Updated platform user: id={platform_user_id}")
            return db_platform_user
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating platform user {platform_user_id}: {str(e)}")
            raise

    @staticmethod
    def delete(db: Session, platform_user_id: int) -> bool:
        """Delete platform user"""
        
        try:
            db_platform_user = PlatformUserRepository.get_by_id(db, platform_user_id)
            if db_platform_user:
                db.delete(db_platform_user)
                db.commit()
                logger.info(f"Deleted platform user: id={platform_user_id}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting platform user {platform_user_id}: {str(e)}")
            raise