import asyncio
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ChatInviteLink
from telegram.error import TelegramError, RetryAfter
from app.models.models import InviteLinkType, ResourceType
from typing import Optional, List, Dict, Any, Union

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramAPIWrapper:
    """Wrapper for Telegram Bot API"""

    def __init__(self, token: str):
        """Initialize with bot token"""
        self.bot = Bot(token=token)

    async def send_message(
        self, chat_id: int, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> bool:
        """Send a message to a chat"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
            return True
        except RetryAfter as e:
            logger.warning(f"Rate limited. Retrying after {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            return await self.send_message(chat_id, text, reply_markup)
        except TelegramError as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def kick_chat_member(self, chat_id: int, user_id: int) -> bool:
        """Kick a user from a chat"""
        try:
            await self.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            # Immediately unban to allow the user to rejoin if they get a new subscription
            await self.bot.unban_chat_member(chat_id=chat_id, user_id=user_id, only_if_banned=True)
            return True
        except RetryAfter as e:
            logger.warning(f"Rate limited. Retrying after {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            return await self.kick_chat_member(chat_id, user_id)
        except TelegramError as e:
            logger.error(f"Error kicking chat member: {e}")
            return False

    async def create_chat_invite_link(
        self, chat_id: int, invite_link_type: InviteLinkType, name: Optional[str] = None
    ) -> Optional[str]:
        """Create an invite link for a chat"""
        try:
            # Set parameters based on invite link type
            creates_join_request = invite_link_type == InviteLinkType.request
            is_primary = invite_link_type == InviteLinkType.static
            
            # For unique links, we create a new link each time
            if invite_link_type == InviteLinkType.unique:
                invite_link = await self.bot.create_chat_invite_link(
                    chat_id=chat_id,
                    creates_join_request=creates_join_request,
                    name=name or f"Subscription link"
                )
                return invite_link.invite_link
            
            # For static links, we revoke all existing links and create a new primary link
            elif invite_link_type == InviteLinkType.static:
                # Get primary link
                chat_invite_link = await self.bot.export_chat_invite_link(chat_id=chat_id)
                return chat_invite_link
            
            # For request links, we create a link that requires admin approval
            elif invite_link_type == InviteLinkType.request:
                invite_link = await self.bot.create_chat_invite_link(
                    chat_id=chat_id,
                    creates_join_request=True,
                    name=name or f"Subscription request link"
                )
                return invite_link.invite_link
            
            return None
        except RetryAfter as e:
            logger.warning(f"Rate limited. Retrying after {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            return await self.create_chat_invite_link(chat_id, invite_link_type, name)
        except TelegramError as e:
            logger.error(f"Error creating chat invite link: {e}")
            return None

    async def approve_chat_join_request(self, chat_id: int, user_id: int) -> bool:
        """Approve a chat join request"""
        try:
            await self.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            return True
        except RetryAfter as e:
            logger.warning(f"Rate limited. Retrying after {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            return await self.approve_chat_join_request(chat_id, user_id)
        except TelegramError as e:
            logger.error(f"Error approving chat join request: {e}")
            return False

    async def decline_chat_join_request(self, chat_id: int, user_id: int) -> bool:
        """Decline a chat join request"""
        try:
            await self.bot.decline_chat_join_request(chat_id=chat_id, user_id=user_id)
            return True
        except RetryAfter as e:
            logger.warning(f"Rate limited. Retrying after {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            return await self.decline_chat_join_request(chat_id, user_id)
        except TelegramError as e:
            logger.error(f"Error declining chat join request: {e}")