from sqlalchemy.orm import Session
from app.models.models import SubscriptionPlan
from app.schemas.schemas import SubscriptionPlanCreate, SubscriptionPlanUpdate
from typing import List, Optional


class SubscriptionPlanRepository:
    """Repository for subscription plan operations"""

    @staticmethod
    def create(db: Session, subscription_plan: SubscriptionPlanCreate) -> SubscriptionPlan:
        """Create a new subscription plan"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_subscription_plan = SubscriptionPlan(
                managed_bot_id=subscription_plan.managed_bot_id,
                name=subscription_plan.name,
                duration_days=subscription_plan.duration_days,
                linked_resource_ids=subscription_plan.linked_resource_ids,
                is_visible=subscription_plan.is_visible,
                description=subscription_plan.description
            )
            
            db.add(db_subscription_plan)
            db.commit()
            db.refresh(db_subscription_plan)
            logger.info(f"Created subscription plan: id={db_subscription_plan.id}, name={subscription_plan.name}")
            return db_subscription_plan
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating subscription plan: {str(e)}")
            raise

    @staticmethod
    def get_by_id(db: Session, subscription_plan_id: int) -> Optional[SubscriptionPlan]:
        """Get subscription plan by ID"""
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription_plan_id).first()

    @staticmethod
    def get_by_managed_bot(db: Session, managed_bot_id: int) -> List[SubscriptionPlan]:
        """Get all subscription plans for a managed bot"""
        return db.query(SubscriptionPlan).filter(SubscriptionPlan.managed_bot_id == managed_bot_id).all()

    @staticmethod
    def get_visible_by_managed_bot(db: Session, managed_bot_id: int) -> List[SubscriptionPlan]:
        """Get all visible subscription plans for a managed bot"""
        return db.query(SubscriptionPlan).filter(
            SubscriptionPlan.managed_bot_id == managed_bot_id,
            SubscriptionPlan.is_visible == True
        ).all()
        
    @staticmethod
    def get_by_id_and_bot(db: Session, plan_id: int, managed_bot_id: int) -> Optional[SubscriptionPlan]:
        """Get subscription plan by ID and managed bot ID"""
        return db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.managed_bot_id == managed_bot_id
        ).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[SubscriptionPlan]:
        """Get all subscription plans"""
        return db.query(SubscriptionPlan).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, subscription_plan_id: int, subscription_plan: SubscriptionPlanUpdate) -> Optional[SubscriptionPlan]:
        """Update subscription plan"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_subscription_plan = SubscriptionPlanRepository.get_by_id(db, subscription_plan_id)
            if db_subscription_plan:
                update_data = subscription_plan.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_subscription_plan, key, value)
                db.commit()
                db.refresh(db_subscription_plan)
                logger.info(f"Updated subscription plan: id={subscription_plan_id}")
                return db_subscription_plan
            else:
                logger.warning(f"Subscription plan not found for update: id={subscription_plan_id}")
                return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating subscription plan {subscription_plan_id}: {str(e)}")
            raise

    @staticmethod
    def delete(db: Session, subscription_plan_id: int) -> bool:
        """Delete subscription plan"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_subscription_plan = SubscriptionPlanRepository.get_by_id(db, subscription_plan_id)
            if db_subscription_plan:
                db.delete(db_subscription_plan)
                db.commit()
                logger.info(f"Deleted subscription plan: id={subscription_plan_id}")
                return True
            else:
                logger.warning(f"Subscription plan not found for deletion: id={subscription_plan_id}")
                return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting subscription plan {subscription_plan_id}: {str(e)}")
            raise