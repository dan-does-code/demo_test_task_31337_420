from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.models import Subscription, SubscriptionStatus
from app.schemas.schemas import SubscriptionCreate, SubscriptionUpdate
from typing import List, Optional


class SubscriptionRepository:
    """Repository for subscription operations"""

    @staticmethod
    def create(db: Session, subscription: SubscriptionCreate, duration_days: int) -> Subscription:
        """Create a new subscription"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            # Calculate end date based on duration
            start_date = datetime.now()
            end_date = start_date + timedelta(days=duration_days)
            
            # Create subscription with calculated dates
            db_subscription = Subscription(
                end_user_id=subscription.end_user_id,
                managed_bot_id=subscription.managed_bot_id,
                plan_id=subscription.plan_id,
                start_date=start_date,
                end_date=end_date,
                status=SubscriptionStatus.active
            )
            
            db.add(db_subscription)
            db.commit()
            db.refresh(db_subscription)
            logger.info(f"Created subscription: id={db_subscription.id}, end_user_id={subscription.end_user_id}, end_date={end_date}")
            return db_subscription
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating subscription: {str(e)}")
            raise

    @staticmethod
    def get_by_id(db: Session, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID"""
        return db.query(Subscription).filter(Subscription.id == subscription_id).first()

    @staticmethod
    def get_by_end_user(db: Session, end_user_id: int) -> List[Subscription]:
        """Get all subscriptions for an end user"""
        return db.query(Subscription).filter(Subscription.end_user_id == end_user_id).all()

    @staticmethod
    def get_by_managed_bot(db: Session, managed_bot_id: int) -> List[Subscription]:
        """Get all subscriptions for a managed bot"""
        return db.query(Subscription).filter(Subscription.managed_bot_id == managed_bot_id).all()

    @staticmethod
    def get_active_by_end_user(db: Session, end_user_id: int) -> List[Subscription]:
        """Get all active subscriptions for an end user"""
        return db.query(Subscription).filter(
            Subscription.end_user_id == end_user_id,
            Subscription.status == SubscriptionStatus.active,
            Subscription.end_date > datetime.now()
        ).all()

    @staticmethod
    def get_active_by_managed_bot(db: Session, managed_bot_id: int) -> List[Subscription]:
        """Get all active subscriptions for a managed bot"""
        return db.query(Subscription).filter(
            Subscription.managed_bot_id == managed_bot_id,
            Subscription.status == SubscriptionStatus.active,
            Subscription.end_date > datetime.now()
        ).all()

    @staticmethod
    def get_active_by_end_user_and_bot(db: Session, end_user_id: int, managed_bot_id: int) -> List[Subscription]:
        """Get all active subscriptions for an end user and managed bot"""
        return db.query(Subscription).filter(
            Subscription.end_user_id == end_user_id,
            Subscription.managed_bot_id == managed_bot_id,
            Subscription.status == SubscriptionStatus.active,
            Subscription.end_date > datetime.now()
        ).all()

    @staticmethod
    def get_expired(db: Session) -> List[Subscription]:
        """Get all expired subscriptions that are still marked as active"""
        return db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.active,
            Subscription.end_date <= datetime.now()
        ).all()

    @staticmethod
    def update(db: Session, subscription_id: int, subscription: SubscriptionUpdate) -> Optional[Subscription]:
        """Update subscription"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_subscription = SubscriptionRepository.get_by_id(db, subscription_id)
            if db_subscription:
                update_data = subscription.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_subscription, key, value)
                db.commit()
                db.refresh(db_subscription)
                logger.info(f"Updated subscription: id={subscription_id}")
            return db_subscription
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating subscription {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def update_status(db: Session, subscription_id: int, status: SubscriptionStatus) -> Optional[Subscription]:
        """Update subscription status"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_subscription = SubscriptionRepository.get_by_id(db, subscription_id)
            if db_subscription:
                db_subscription.status = status
                db.commit()
                db.refresh(db_subscription)
                logger.info(f"Updated subscription status: id={subscription_id}, status={status}")
            return db_subscription
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating subscription status {subscription_id}: {str(e)}")
            raise

    @staticmethod
    def delete(db: Session, subscription_id: int) -> bool:
        """Delete subscription"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_subscription = SubscriptionRepository.get_by_id(db, subscription_id)
            if db_subscription:
                db.delete(db_subscription)
                db.commit()
                logger.info(f"Deleted subscription: id={subscription_id}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting subscription {subscription_id}: {str(e)}")
            raise