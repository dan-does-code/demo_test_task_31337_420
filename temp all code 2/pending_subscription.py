from sqlalchemy.orm import Session
from app.models.models import PendingSubscription, PendingSubscriptionStatus
from app.schemas.schemas import PendingSubscriptionCreate, PendingSubscriptionUpdate
from typing import List, Optional


class PendingSubscriptionRepository:
    """Repository for pending subscription operations"""

    @staticmethod
    def create(db: Session, pending_subscription: PendingSubscriptionCreate) -> PendingSubscription:
        """Create a new pending subscription"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_pending_subscription = PendingSubscription(
                end_user_id=pending_subscription.end_user_id,
                managed_bot_id=pending_subscription.managed_bot_id,
                plan_id=pending_subscription.plan_id,
                status=PendingSubscriptionStatus.pending_approval
            )
            
            db.add(db_pending_subscription)
            db.commit()
            db.refresh(db_pending_subscription)
            logger.info(f"Created pending subscription: id={db_pending_subscription.id}, end_user_id={pending_subscription.end_user_id}")
            return db_pending_subscription
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating pending subscription: {str(e)}")
            raise

    @staticmethod
    def get_by_id(db: Session, pending_subscription_id: int) -> Optional[PendingSubscription]:
        """Get pending subscription by ID"""
        return db.query(PendingSubscription).filter(PendingSubscription.id == pending_subscription_id).first()

    @staticmethod
    def get_by_end_user(db: Session, end_user_id: int) -> List[PendingSubscription]:
        """Get all pending subscriptions for an end user"""
        return db.query(PendingSubscription).filter(PendingSubscription.end_user_id == end_user_id).all()

    @staticmethod
    def get_by_managed_bot(db: Session, managed_bot_id: int) -> List[PendingSubscription]:
        """Get all pending subscriptions for a managed bot"""
        return db.query(PendingSubscription).filter(PendingSubscription.managed_bot_id == managed_bot_id).all()

    @staticmethod
    def get_pending_by_end_user_and_bot(db: Session, end_user_id: int, managed_bot_id: int) -> Optional[PendingSubscription]:
        """Get pending subscription for an end user and managed bot"""
        return db.query(PendingSubscription).filter(
            PendingSubscription.end_user_id == end_user_id,
            PendingSubscription.managed_bot_id == managed_bot_id,
            PendingSubscription.status == PendingSubscriptionStatus.pending_approval
        ).first()

    @staticmethod
    def get_pending_by_managed_bot(db: Session, managed_bot_id: int) -> List[PendingSubscription]:
        """Get all pending subscriptions for a managed bot"""
        return db.query(PendingSubscription).filter(
            PendingSubscription.managed_bot_id == managed_bot_id,
            PendingSubscription.status == PendingSubscriptionStatus.pending_approval
        ).all()

    @staticmethod
    def update(db: Session, pending_subscription_id: int, pending_subscription: PendingSubscriptionUpdate) -> Optional[PendingSubscription]:
        """Update pending subscription"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_pending_subscription = PendingSubscriptionRepository.get_by_id(db, pending_subscription_id)
            if db_pending_subscription:
                update_data = pending_subscription.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_pending_subscription, key, value)
                db.commit()
                db.refresh(db_pending_subscription)
                logger.info(f"Updated pending subscription: id={pending_subscription_id}")
            return db_pending_subscription
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating pending subscription {pending_subscription_id}: {str(e)}")
            raise

    @staticmethod
    def update_status(db: Session, pending_subscription_id: int, status: PendingSubscriptionStatus) -> Optional[PendingSubscription]:
        """Update pending subscription status"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_pending_subscription = PendingSubscriptionRepository.get_by_id(db, pending_subscription_id)
            if db_pending_subscription:
                db_pending_subscription.status = status
                db.commit()
                db.refresh(db_pending_subscription)
                logger.info(f"Updated pending subscription status: id={pending_subscription_id}, status={status}")
            return db_pending_subscription
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating pending subscription status {pending_subscription_id}: {str(e)}")
            raise

    @staticmethod
    def delete(db: Session, pending_subscription_id: int) -> bool:
        """Delete pending subscription"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_pending_subscription = PendingSubscriptionRepository.get_by_id(db, pending_subscription_id)
            if db_pending_subscription:
                db.delete(db_pending_subscription)
                db.commit()
                logger.info(f"Deleted pending subscription: id={pending_subscription_id}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting pending subscription {pending_subscription_id}: {str(e)}")
            raise