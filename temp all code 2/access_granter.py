import logging
from sqlalchemy.orm import Session
from app.models.models import Subscription, InviteLinkType
from app.repositories.subscription import SubscriptionRepository
from app.repositories.subscription_plan import SubscriptionPlanRepository
from app.repositories.target_resource import TargetResourceRepository
from app.repositories.managed_bot import ManagedBotRepository
from app.services.telegram_api import TelegramAPIWrapper
from app.models.base import SessionLocal
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class AccessGranter:
    """Service for granting and revoking access to Telegram resources"""

    @staticmethod
    async def grant_access(db: Session, subscription: Subscription) -> Dict[str, Union[bool, Dict[int, str]]]:
        """Grant access to resources based on subscription
        
        Args:
            db: Database session
            subscription: Subscription object
            
        Returns:
            Dict with success status and invite links (if applicable)
        """
        # Get the subscription plan to determine which resources to grant access to
        plan = SubscriptionPlanRepository.get_by_id(db, subscription.plan_id)
        if not plan:
            logger.error(f"Plan not found for subscription {subscription.id}")
            return {"success": False, "links": {}}
        
        # Get the bot token
        bot_token = ManagedBotRepository.get_decrypted_token(db, subscription.managed_bot_id)
        if not bot_token:
            logger.error(f"Bot token not found for managed bot {subscription.managed_bot_id}")
            return {"success": False, "links": {}}
        
        # Initialize Telegram API wrapper
        telegram_api = TelegramAPIWrapper(bot_token)
        
        # Get resources linked to the subscription plan
        resource_ids = plan.linked_resource_ids or []
        resources = []
        for resource_id in resource_ids:
            resource = TargetResourceRepository.get_by_id(db, resource_id)
            if resource:
                resources.append(resource)
        
        if not resources:
            logger.warning(f"No resources found for plan {plan.id}")
            return {"success": True, "links": {}}
        
        # Process each resource and generate invite links or approve requests
        result = {"success": True, "links": {}}
        for resource in resources:
            # Handle different invite link types
            if resource.invite_link_type == InviteLinkType.custom and resource.custom_link:
                # Use custom link if available
                result["links"][resource.id] = resource.custom_link
            elif resource.invite_link_type == InviteLinkType.request:
                # For request type, approve the join request
                success = await telegram_api.approve_chat_join_request(
                    chat_id=resource.tg_chat_id,
                    user_id=subscription.end_user_id
                )
                if not success:
                    result["success"] = False
            else:
                # For unique or static links, create a new invite link
                invite_link = await telegram_api.create_chat_invite_link(
                    chat_id=resource.tg_chat_id,
                    invite_link_type=resource.invite_link_type,
                    name=f"Subscription for user {subscription.end_user_id}"
                )
                if invite_link:
                    result["links"][resource.id] = invite_link
                else:
                    result["success"] = False
        
        return result

    @staticmethod
    async def grant_access_task(subscription_id: int) -> Dict[str, Union[bool, Dict[int, str]]]:
        """Background task wrapper for grant_access that creates its own database session
        
        Args:
            subscription_id: ID of the subscription to grant access for
            
        Returns:
            Dict with success status and invite links (if applicable)
        """
        logger.info(f"Starting background task to grant access for subscription {subscription_id}")
        db = SessionLocal()
        try:
            from app.models.models import Subscription
            subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
            if not subscription:
                logger.error(f"Subscription not found for ID {subscription_id}")
                return {"success": False, "links": {}}
            
            return await AccessGranter.grant_access(db, subscription)
        except Exception as e:
            logger.exception(f"Error in grant_access_task: {str(e)}")
            return {"success": False, "links": {}}
        finally:
            db.close()
    
    @staticmethod
    async def revoke_access_task(subscription_id: int) -> bool:
        """Background task wrapper for revoke_access that creates its own database session
        
        Args:
            subscription_id: ID of the subscription to revoke access for
            
        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Starting background task to revoke access for subscription {subscription_id}")
        db = SessionLocal()
        try:
            from app.models.models import Subscription
            subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
            if not subscription:
                logger.error(f"Subscription not found for ID {subscription_id}")
                return False
            
            return await AccessGranter.revoke_access(db, subscription)
        except Exception as e:
            logger.exception(f"Error in revoke_access_task: {str(e)}")
            return False
        finally:
            db.close()
    
    @staticmethod
    async def revoke_access(db: Session, subscription: Subscription) -> bool:
        """Revoke access to resources for an expired subscription
        
        Args:
            db: Database session
            subscription: Subscription object
            
        Returns:
            Boolean indicating success or failure
        """
        # Get the subscription plan to determine which resources to revoke access from
        plan = SubscriptionPlanRepository.get_by_id(db, subscription.plan_id)
        if not plan:
            logger.error(f"Plan not found for subscription {subscription.id}")
            return False
        
        # Get the bot token
        bot_token = ManagedBotRepository.get_decrypted_token(db, subscription.managed_bot_id)
        if not bot_token:
            logger.error(f"Bot token not found for managed bot {subscription.managed_bot_id}")
            return False
        
        # Initialize Telegram API wrapper
        telegram_api = TelegramAPIWrapper(bot_token)
        
        # Get resources linked to the subscription plan
        resource_ids = plan.linked_resource_ids or []
        resources = []
        for resource_id in resource_ids:
            resource = TargetResourceRepository.get_by_id(db, resource_id)
            if resource:
                resources.append(resource)
        
        if not resources:
            logger.warning(f"No resources found for plan {plan.id}")
            return True  # No resources to revoke access from
        
        # Kick the user from each resource
        all_success = True
        for resource in resources:
            success = await telegram_api.kick_chat_member(
                chat_id=resource.tg_chat_id,
                user_id=subscription.end_user_id
            )
            if not success:
                all_success = False
                logger.error(
                    f"Failed to kick user {subscription.end_user_id} from resource {resource.id}"
                )
        
        return all_success