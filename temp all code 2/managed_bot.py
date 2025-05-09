from sqlalchemy.orm import Session
from app.models.models import ManagedBot
from app.schemas.schemas import ManagedBotCreate, ManagedBotUpdate
from app.utils.encryption import encrypt_text, decrypt_text
from typing import List, Optional
import secrets
import string


class ManagedBotRepository:
    """Repository for managed bot operations"""

    @staticmethod
    def generate_webhook_secret(length=32) -> str:
        """Generate a secure random webhook secret"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def create(db: Session, managed_bot: ManagedBotCreate) -> ManagedBot:
        """Create a new managed bot"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            # Encrypt the bot token before storing
            encrypted_token = encrypt_text(managed_bot.tg_token)
            
            # Generate a webhook secret if not provided
            webhook_secret = managed_bot.webhook_secret or ManagedBotRepository.generate_webhook_secret()
            
            # Create the managed bot with encrypted token and webhook secret
            db_managed_bot = ManagedBot(
                platform_user_id=managed_bot.platform_user_id,
                tg_token_encrypted=encrypted_token,
                username=managed_bot.username,
                config_data=managed_bot.config_data,
                intended_payment_methods=managed_bot.intended_payment_methods,
                webhook_secret=webhook_secret
            )
            
            db.add(db_managed_bot)
            db.commit()
            db.refresh(db_managed_bot)
            logger.info(f"Created managed bot: id={db_managed_bot.id}, username={managed_bot.username}")
            return db_managed_bot
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating managed bot: {str(e)}")
            raise

    @staticmethod
    def get_by_id(db: Session, managed_bot_id: int) -> Optional[ManagedBot]:
        """Get managed bot by ID"""
        return db.query(ManagedBot).filter(ManagedBot.id == managed_bot_id).first()

    @staticmethod
    def get_by_platform_user_id(db: Session, platform_user_id: int) -> List[ManagedBot]:
        """Get all managed bots for a platform user"""
        return db.query(ManagedBot).filter(ManagedBot.platform_user_id == platform_user_id).all()
        
    @staticmethod
    def get_by_webhook_secret(db: Session, webhook_secret: str) -> Optional[ManagedBot]:
        """Get managed bot by webhook secret"""
        return db.query(ManagedBot).filter(ManagedBot.webhook_secret == webhook_secret).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[ManagedBot]:
        """Get all managed bots"""
        return db.query(ManagedBot).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, managed_bot_id: int, managed_bot: ManagedBotUpdate) -> Optional[ManagedBot]:
        """Update managed bot"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_managed_bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
            if db_managed_bot:
                update_data = managed_bot.dict(exclude_unset=True)
                
                # Handle token encryption if a new token is provided
                if "tg_token" in update_data:
                    update_data["tg_token_encrypted"] = encrypt_text(update_data.pop("tg_token"))
                
                for key, value in update_data.items():
                    setattr(db_managed_bot, key, value)
                
                db.commit()
                db.refresh(db_managed_bot)
                logger.info(f"Updated managed bot: id={managed_bot_id}")
                return db_managed_bot
            else:
                logger.warning(f"Managed bot not found for update: id={managed_bot_id}")
                return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating managed bot {managed_bot_id}: {str(e)}")
            raise

    @staticmethod
    def delete(db: Session, managed_bot_id: int) -> bool:
        """Delete managed bot"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_managed_bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
            if db_managed_bot:
                db.delete(db_managed_bot)
                db.commit()
                logger.info(f"Deleted managed bot: id={managed_bot_id}")
                return True
            else:
                logger.warning(f"Managed bot not found for deletion: id={managed_bot_id}")
                return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting managed bot {managed_bot_id}: {str(e)}")
            raise

    @staticmethod
    def get_decrypted_token(db: Session, managed_bot_id: int) -> Optional[str]:
        """Get the decrypted token for a managed bot"""
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        
        try:
            db_managed_bot = ManagedBotRepository.get_by_id(db, managed_bot_id)
            if db_managed_bot and db_managed_bot.tg_token_encrypted:
                token = decrypt_text(db_managed_bot.tg_token_encrypted)
                logger.debug(f"Retrieved decrypted token for managed bot: id={managed_bot_id}")
                return token
            else:
                logger.warning(f"No encrypted token found for managed bot: id={managed_bot_id}")
                return None
        except Exception as e:
            logger.error(f"Error decrypting token for managed bot {managed_bot_id}: {str(e)}")
            return None