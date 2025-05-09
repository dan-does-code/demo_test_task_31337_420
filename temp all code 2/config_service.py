# File: app/services/config_service.py

from sqlalchemy.orm import Session
from app.repositories.managed_bot import ManagedBotRepository
from app.schemas.schemas import BotConfigUpdate
from typing import Dict, Any, Optional
from app.utils.logger import get_logger # Added import

logger = get_logger(__name__) # Added logger instance


class ConfigService:
    """Service for managing bot configurations"""

    @staticmethod
    def get_config(db: Session, managed_bot_id: int) -> Dict[str, Any]:
        """Get the configuration data for a managed bot

        Args:
            db: Database session
            managed_bot_id: ID of the managed bot

        Returns:
            Dict containing the bot's configuration data or empty dict if not found
        """
        bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
        # Return default empty dict if bot or config_data is None/empty
        return bot.config_data if bot and bot.config_data else {}

    @staticmethod
    def update_config(db: Session, managed_bot_id: int, config_update: BotConfigUpdate) -> Optional[Dict[str, Any]]: # Return type changed to Optional
        """Update the configuration data for a managed bot

        Args:
            db: Database session
            managed_bot_id: ID of the managed bot
            config_update: BotConfigUpdate object containing fields to update

        Returns:
            Updated configuration data dict or None if bot not found
        """
        bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
        if not bot:
            logger.warning(f"Managed bot not found for config update: id={managed_bot_id}")
            return None # Return None if bot not found

        # Get current config or initialize empty dict
        current_config = bot.config_data or {}

        # Update with new values, excluding None values from the Pydantic model
        update_data = config_update.dict(exclude_unset=True, exclude_none=True)

        # Merge the updates into the current config
        current_config.update(update_data) # Use update() for cleaner merging

        # Update the bot's config_data
        try:
            bot.config_data = current_config
            db.commit()
            db.refresh(bot) # Refresh the bot instance
            logger.info(f"Updated config for managed bot: id={managed_bot_id}")
            return bot.config_data # Return the updated config from the refreshed bot object
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating config for bot {managed_bot_id}: {str(e)}")
            return None # Return None on error

    # --- START: ADD THIS FUNCTION ---
    @staticmethod
    def update_config_field(db: Session, managed_bot_id: int, field_key: str, field_value: Any) -> Optional[Dict[str, Any]]:
        """Update a specific field in the configuration data for a managed bot

        Args:
            db: Database session
            managed_bot_id: ID of the managed bot
            field_key: The key of the config field to update
            field_value: The new value for the config field

        Returns:
            Updated configuration data dict or None if bot not found or error occurs
        """
        bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
        if not bot:
            logger.warning(f"Managed bot not found for config field update: id={managed_bot_id}")
            return None

        # Get current config or initialize empty dict
        current_config = bot.config_data or {}

        # Update the specific field
        current_config[field_key] = field_value

        # Update the bot's config_data
        try:
            # Important: Mark the JSON field as modified for SQLAlchemy to detect the change
            from sqlalchemy.orm.attributes import flag_modified
            bot.config_data = current_config
            flag_modified(bot, "config_data") # Mark as modified

            db.commit()
            db.refresh(bot) # Refresh the bot instance
            logger.info(f"Updated config field '{field_key}' for managed bot: id={managed_bot_id}")
            return bot.config_data # Return the updated config
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating config field '{field_key}' for bot {managed_bot_id}: {str(e)}")
            return None
    # --- END: ADD THIS FUNCTION ---

    @staticmethod
    def get_message(db: Session, managed_bot_id: int, message_key: str, default_message: Optional[str] = None) -> str: # Added optional default
        """Get a specific message from the bot's configuration

        Args:
            db: Database session
            managed_bot_id: ID of the managed bot
            message_key: Key of the message to retrieve
            default_message: Optional default message if key not found

        Returns:
            Message string or default message if not found
        """
        # Default messages for different message types if no specific default is provided
        default_messages = {
            "welcome_message": "Welcome to the bot! Use /subscribe to see available plans.",
            "subscription_message": "Thank you for subscribing!",
            "expired_message": "Your subscription has expired. Use /subscribe to renew.",
            "pending_message": "Your subscription request is pending approval. You will be notified.",
            "approved_message": "Your subscription has been approved!",
            "rejected_message": "Your subscription request has been rejected."
        }

        # Get the bot's config
        config = ConfigService.get_config(db, managed_bot_id)

        # Return the message if it exists, otherwise return the provided default or the hardcoded default
        return config.get(message_key, default_message or default_messages.get(message_key, ""))