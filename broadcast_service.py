from sqlalchemy.orm import Session
from app.repositories.subscription import SubscriptionRepository
from app.repositories.managed_bot import ManagedBotRepository
from app.services.telegram_api import TelegramAPIWrapper
from app.models.base import SessionLocal
from typing import List, Dict, Any, Optional
import asyncio
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class BroadcastService:
    """Service for broadcasting messages to subscribers"""

    @staticmethod
    async def broadcast_task(managed_bot_id: int, message_text: str, target_user_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Background task wrapper for broadcast_to_subscribers that creates its own database session
        
        Args:
            managed_bot_id: ID of the managed bot
            message_text: Text of the message to broadcast
            target_user_ids: Optional list of specific user IDs to target
            
        Returns:
            Dict with success status and broadcast results
        """
        logger.info(f"Starting background task to broadcast message for bot {managed_bot_id}")
        db = SessionLocal()
        try:
            return await BroadcastService.broadcast_to_subscribers(db, managed_bot_id, message_text, target_user_ids)
        except Exception as e:
            logger.exception(f"Error in broadcast_task: {str(e)}")
            return {"success": False, "message": f"Error in broadcast task: {str(e)}"}
        finally:
            db.close()
    
    @staticmethod
    async def broadcast_to_subscribers(db: Session, managed_bot_id: int, message_text: str, target_user_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Broadcast a message to all subscribers of a managed bot"""
        # Get bot token
        bot_token = ManagedBotRepository.get_decrypted_token(db, managed_bot_id)
        if not bot_token:
            return {"success": False, "message": "Bot token not found or could not be decrypted"}
        
        # Initialize Telegram API wrapper
        telegram_api = TelegramAPIWrapper(bot_token)
        
        # Get subscribers
        if target_user_ids:
            # If specific user IDs are provided, use those
            subscribers = []
            for user_id in target_user_ids:
                # Check if user has an active subscription
                user_subs = SubscriptionRepository.get_active_by_end_user_and_bot(db, user_id, managed_bot_id)
                if user_subs:
                    subscribers.append({"end_user_id": user_id})
        else:
            # Otherwise, get all active subscribers
            subscriptions = SubscriptionRepository.get_active_by_managed_bot(db, managed_bot_id)
            subscribers = []
            # Deduplicate subscribers (a user might have multiple active subscriptions)
            user_ids = set()
            for sub in subscriptions:
                if sub.end_user_id not in user_ids:
                    subscribers.append({"end_user_id": sub.end_user_id})
                    user_ids.add(sub.end_user_id)
        
        if not subscribers:
            return {"success": False, "message": "No active subscribers found"}
        
        # Send messages
        success_count = 0
        failed_count = 0
        failed_users = []
        
        for subscriber in subscribers:
            try:
                result = await telegram_api.send_message(
                    chat_id=subscriber["end_user_id"],
                    text=message_text
                )
                
                if result:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_users.append(subscriber["end_user_id"])
                
                # Add a small delay to avoid hitting rate limits
                await asyncio.sleep(0.05)
                
            except Exception as e:
                logger.exception(f"Error sending broadcast to user {subscriber['end_user_id']}: {str(e)}")
                failed_count += 1
                failed_users.append(subscriber["end_user_id"])
        
        return {
            "success": True,
            "total": len(subscribers),
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_users": failed_users
        }