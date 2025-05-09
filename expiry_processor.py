from sqlalchemy.orm import Session
from app.repositories.subscription import SubscriptionRepository
from app.services.access_granter import AccessGranter
from app.services.telegram_api import TelegramAPIWrapper
from app.repositories.managed_bot import ManagedBotRepository
from app.services.config_service import ConfigService
from typing import List, Dict, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class ExpiryProcessor:
    """Service for processing expired subscriptions"""

    @staticmethod
    async def process_expired_subscriptions(db: Session) -> Dict[str, Any]:
        """Process all expired subscriptions"""
        # Get all expired subscriptions that are still marked as active
        expired_subscriptions = SubscriptionRepository.get_expired(db)
        
        if not expired_subscriptions:
            return {"success": True, "message": "No expired subscriptions found", "processed": 0}
        
        processed_count = 0
        failed_count = 0
        results = []
        
        for subscription in expired_subscriptions:
            try:
                # Revoke access to resources
                revoke_result = await AccessGranter.revoke_access(db, subscription.id)
                
                # Update subscription status to expired
                updated_subscription = SubscriptionRepository.update_status(
                    db, subscription.id, "expired"
                )
                
                # Notify user about expiration
                if updated_subscription:
                    # Get bot token
                    bot_token = ManagedBotRepository.get_decrypted_token(db, subscription.managed_bot_id)
                    if bot_token:
                        # Initialize Telegram API wrapper
                        telegram_api = TelegramAPIWrapper(bot_token)
                        
                        # Get expiration message from config
                        expired_message = ConfigService.get_message(db, subscription.managed_bot_id, "expired")
                        
                        # Send message to user
                        await telegram_api.send_message(
                            chat_id=subscription.end_user_id,
                            text=expired_message
                        )
                
                processed_count += 1
                results.append({
                    "subscription_id": subscription.id,
                    "end_user_id": subscription.end_user_id,
                    "managed_bot_id": subscription.managed_bot_id,
                    "success": True,
                    "revoke_result": revoke_result
                })
                
            except Exception as e:
                logger.exception(f"Error processing expired subscription {subscription.id}: {str(e)}")
                failed_count += 1
                results.append({
                    "subscription_id": subscription.id,
                    "end_user_id": subscription.end_user_id,
                    "managed_bot_id": subscription.managed_bot_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "processed": processed_count,
            "failed": failed_count,
            "total": len(expired_subscriptions)
        }