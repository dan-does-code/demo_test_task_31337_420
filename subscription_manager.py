from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import traceback
from app.repositories.subscription import SubscriptionRepository
from app.repositories.pending_subscription import PendingSubscriptionRepository
from app.repositories.subscription_plan import SubscriptionPlanRepository
from app.repositories.target_resource import TargetResourceRepository
from app.repositories.managed_bot import ManagedBotRepository
from app.repositories.end_user import EndUserRepository
from app.schemas.schemas import SubscriptionCreate, PendingSubscriptionCreate, EndUserCreate
from app.models.models import SubscriptionStatus, PendingSubscriptionStatus
from app.utils.logger import get_logger
from typing import List, Optional, Dict, Any, Union

# Get logger for this module
logger = get_logger(__name__)


class SubscriptionManager:
    """Service for managing subscriptions"""

    @staticmethod
    async def create_subscription(db: Session, end_user_id: int, managed_bot_id: int, plan_id: int) -> dict:
        """Create a new subscription"""
        try:
            logger.info(f"Creating subscription for end_user_id={end_user_id}, managed_bot_id={managed_bot_id}, plan_id={plan_id}")
            
            # Get the subscription plan to determine duration
            plan = SubscriptionPlanRepository.get_by_id(db, plan_id)
            if not plan:
                logger.warning(f"Subscription plan not found: plan_id={plan_id}")
                return {"success": False, "message": "Subscription plan not found"}

            # Create subscription
            subscription_data = SubscriptionCreate(
                end_user_id=end_user_id,
                managed_bot_id=managed_bot_id,
                plan_id=plan_id
            )
            
            subscription = SubscriptionRepository.create(db, subscription_data, plan.duration_days)
            logger.info(f"Subscription created successfully: id={subscription.id}, end_date={subscription.end_date}")
            
            return {
                "success": True, 
                "subscription": subscription,
                "end_date": subscription.end_date
            }
        except Exception as e:
            error_msg = f"Error creating subscription: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return {"success": False, "message": error_msg}

    @staticmethod
    async def create_pending_subscription(db: Session, end_user_id: int, managed_bot_id: int, plan_id: int) -> dict:
        """Create a new pending subscription"""
        try:
            logger.info(f"Creating pending subscription for end_user_id={end_user_id}, managed_bot_id={managed_bot_id}, plan_id={plan_id}")
            
            # Check if plan exists
            plan = SubscriptionPlanRepository.get_by_id(db, plan_id)
            if not plan:
                logger.warning(f"Subscription plan not found: plan_id={plan_id}")
                return {"success": False, "message": "Subscription plan not found"}

            # Check if there's already a pending subscription
            existing_pending = PendingSubscriptionRepository.get_pending_by_end_user_and_bot(db, end_user_id, managed_bot_id)
            if existing_pending:
                logger.info(f"User already has pending subscription: end_user_id={end_user_id}, managed_bot_id={managed_bot_id}")
                return {"success": False, "message": "You already have a pending subscription request"}

            # Create pending subscription
            pending_data = PendingSubscriptionCreate(
                end_user_id=end_user_id,
                managed_bot_id=managed_bot_id,
                plan_id=plan_id
            )
            
            pending_subscription = PendingSubscriptionRepository.create(db, pending_data)
            logger.info(f"Pending subscription created successfully: id={pending_subscription.id}")
            
            return {
                "success": True, 
                "pending_subscription": pending_subscription
            }
        except Exception as e:
            error_msg = f"Error creating pending subscription: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return {"success": False, "message": error_msg}

    @staticmethod
    async def approve_pending_subscription(db: Session, pending_subscription_id: int) -> dict:
        """Approve a pending subscription and create an active subscription"""
        try:
            logger.info(f"Approving pending subscription: id={pending_subscription_id}")
            
            # Get pending subscription
            pending_subscription = PendingSubscriptionRepository.get_by_id(db, pending_subscription_id)
            if not pending_subscription:
                logger.warning(f"Pending subscription not found: id={pending_subscription_id}")
                return {"success": False, "message": "Pending subscription not found"}
            
            # Check if already processed
            if pending_subscription.status != PendingSubscriptionStatus.pending_approval:
                logger.warning(f"Pending subscription already processed: id={pending_subscription_id}, status={pending_subscription.status.value}")
                return {"success": False, "message": f"Subscription already {pending_subscription.status.value}"}
            
            # Create active subscription
            result = await SubscriptionManager.create_subscription(
                db, 
                pending_subscription.end_user_id, 
                pending_subscription.managed_bot_id, 
                pending_subscription.plan_id
            )
            
            if not result["success"]:
                logger.error(f"Failed to create subscription from pending: id={pending_subscription_id}, error={result.get('message')}")
                return result
            
            # Update pending subscription status
            updated_pending = PendingSubscriptionRepository.update_status(
                db, 
                pending_subscription_id, 
                PendingSubscriptionStatus.approved
            )
            
            logger.info(f"Pending subscription approved successfully: id={pending_subscription_id}, new subscription id={result['subscription'].id}")
            
            return {
                "success": True,
                "subscription": result["subscription"],
                "pending_subscription": updated_pending
            }
        except Exception as e:
            error_msg = f"Error approving pending subscription: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return {"success": False, "message": error_msg}

    @staticmethod
    async def reject_pending_subscription(db: Session, pending_subscription_id: int) -> dict:
        """Reject a pending subscription"""
        try:
            logger.info(f"Rejecting pending subscription: id={pending_subscription_id}")
            
            # Get pending subscription
            pending_subscription = PendingSubscriptionRepository.get_by_id(db, pending_subscription_id)
            if not pending_subscription:
                logger.warning(f"Pending subscription not found: id={pending_subscription_id}")
                return {"success": False, "message": "Pending subscription not found"}
            
            # Check if already processed
            if pending_subscription.status != PendingSubscriptionStatus.pending_approval:
                logger.warning(f"Pending subscription already processed: id={pending_subscription_id}, status={pending_subscription.status.value}")
                return {"success": False, "message": f"Subscription already {pending_subscription.status.value}"}
            
            # Update pending subscription status
            updated_pending = PendingSubscriptionRepository.update_status(
                db, 
                pending_subscription_id, 
                PendingSubscriptionStatus.rejected
            )
            
            logger.info(f"Pending subscription rejected successfully: id={pending_subscription_id}")
            
            return {
                "success": True,
                "pending_subscription": updated_pending
            }
        except Exception as e:
            error_msg = f"Error rejecting pending subscription: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return {"success": False, "message": error_msg}

    @staticmethod
    async def get_active_subscriptions_by_end_user(db: Session, end_user_id: int) -> List:
        """Get all active subscriptions for an end user"""
        return SubscriptionRepository.get_active_by_end_user(db, end_user_id)

    @staticmethod
    async def get_active_subscriptions_by_managed_bot(db: Session, managed_bot_id: int) -> List:
        """Get all active subscriptions for a managed bot"""
        return SubscriptionRepository.get_active_by_managed_bot(db, managed_bot_id)

    @staticmethod
    async def get_expired_subscriptions() -> List:
        """Get all expired subscriptions"""
        return SubscriptionRepository.get_expired()

    @staticmethod
    async def expire_subscription(db: Session, subscription_id: int) -> dict:
        """Mark a subscription as expired"""
        subscription = SubscriptionRepository.get_by_id(db, subscription_id)
        if not subscription:
            return {"success": False, "message": "Subscription not found"}
        
        updated_subscription = SubscriptionRepository.update_status(
            db, 
            subscription_id, 
            SubscriptionStatus.expired
        )
        
        return {
            "success": True,
            "subscription": updated_subscription
        }

    @staticmethod
    async def check_access(db: Session, end_user_id: int, managed_bot_id: int, resource_id: Optional[int] = None) -> bool:
        """Check if an end user has access to a resource"""
        # Get active subscriptions for this user and bot
        subscriptions = await SubscriptionManager.get_active_subscriptions_by_end_user_and_bot(
            db, end_user_id, managed_bot_id
        )
        
        if not subscriptions:
            return False
        
        # If no specific resource is requested, user has access if they have any active subscription
        if resource_id is None:
            return True
        
        # Check if any of the user's subscription plans include this resource
        for subscription in subscriptions:
            plan = SubscriptionPlanRepository.get_by_id(db, subscription.plan_id)
            if plan and resource_id in plan.linked_resource_ids:
                return True
        
        return False

    @staticmethod
    async def get_active_subscriptions_by_end_user_and_bot(db: Session, end_user_id: int, managed_bot_id: int) -> List:
        """Get all active subscriptions for an end user and managed bot"""
        return SubscriptionRepository.get_active_by_end_user_and_bot(db, end_user_id, managed_bot_id)

    @staticmethod
    async def get_pending_subscriptions_by_managed_bot(db: Session, managed_bot_id: int) -> List:
        """Get all pending subscriptions for a managed bot"""
        return PendingSubscriptionRepository.get_pending_by_managed_bot(db, managed_bot_id)