from sqlalchemy.orm import Session
from app.models.models import TargetResource
from app.schemas.schemas import TargetResourceCreate, TargetResourceUpdate
from typing import List, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TargetResourceRepository:
    """Repository for target resource operations"""

    @staticmethod
    def create(db: Session, target_resource: TargetResourceCreate) -> TargetResource:
        """Create a new target resource"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_target_resource = TargetResource(
                managed_bot_id=target_resource.managed_bot_id,
                tg_chat_id=target_resource.tg_chat_id,
                type=target_resource.type,
                invite_link_type=target_resource.invite_link_type,
                custom_link=target_resource.custom_link,
                is_mandatory=target_resource.is_mandatory
            )
            
            db.add(db_target_resource)
            db.commit()
            db.refresh(db_target_resource)
            logger.info(f"Created target resource: id={db_target_resource.id}, managed_bot_id={target_resource.managed_bot_id}")
            return db_target_resource
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating target resource: {str(e)}")
            raise

    @staticmethod
    def get_by_id(db: Session, target_resource_id: int) -> Optional[TargetResource]:
        """Get target resource by ID"""
        return db.query(TargetResource).filter(TargetResource.id == target_resource_id).first()

    @staticmethod
    def get_by_managed_bot(db: Session, managed_bot_id: int) -> List[TargetResource]:
        """Get all target resources for a managed bot"""
        return db.query(TargetResource).filter(TargetResource.managed_bot_id == managed_bot_id).all()

    @staticmethod
    def get_by_chat_id(db: Session, tg_chat_id: int) -> Optional[TargetResource]:
        """Get target resource by Telegram chat ID"""
        return db.query(TargetResource).filter(TargetResource.tg_chat_id == tg_chat_id).first()
        
    @staticmethod
    def get_by_id_and_bot(db: Session, resource_id: int, managed_bot_id: int) -> Optional[TargetResource]:
        """Get target resource by ID and managed bot ID"""
        return db.query(TargetResource).filter(
            TargetResource.id == resource_id,
            TargetResource.managed_bot_id == managed_bot_id
        ).first()

    @staticmethod
    def get_mandatory_by_managed_bot(db: Session, managed_bot_id: int) -> List[TargetResource]:
        """Get all mandatory target resources for a managed bot"""
        return db.query(TargetResource).filter(
            TargetResource.managed_bot_id == managed_bot_id,
            TargetResource.is_mandatory == True
        ).all()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[TargetResource]:
        """Get all target resources"""
        return db.query(TargetResource).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, target_resource_id: int, target_resource: TargetResourceUpdate) -> Optional[TargetResource]:
        """Update target resource"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_target_resource = TargetResourceRepository.get_by_id(db, target_resource_id)
            if db_target_resource:
                update_data = target_resource.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_target_resource, key, value)
                db.commit()
                db.refresh(db_target_resource)
                logger.info(f"Updated target resource: id={target_resource_id}")
                return db_target_resource
            else:
                logger.warning(f"Target resource not found for update: id={target_resource_id}")
                return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating target resource {target_resource_id}: {str(e)}")
            raise

    @staticmethod
    def delete(db: Session, target_resource_id: int) -> bool:
        """Delete target resource"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_target_resource = TargetResourceRepository.get_by_id(db, target_resource_id)
            if db_target_resource:
                db.delete(db_target_resource)
                db.commit()
                logger.info(f"Deleted target resource: id={target_resource_id}")
                return True
            else:
                logger.warning(f"Target resource not found for deletion: id={target_resource_id}")
                return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting target resource {target_resource_id}: {str(e)}")
            raise