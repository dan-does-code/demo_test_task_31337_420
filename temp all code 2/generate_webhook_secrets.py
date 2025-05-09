\"""Script to generate webhook secrets for existing bots

This script should be run after the migration to add the webhook_secret column.
It will generate a unique webhook secret for each managed bot that doesn't have one.
"""

import sys
import os

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.base import get_db
from app.repositories.managed_bot import ManagedBotRepository


def generate_webhook_secrets():
    """Generate webhook secrets for all managed bots that don't have one"""
    db = next(get_db())
    try:
        # Get all managed bots
        managed_bots = ManagedBotRepository.get_all(db)
        
        # Count of bots that need webhook secrets
        bots_without_secret = [bot for bot in managed_bots if not bot.webhook_secret]
        print(f"Found {len(bots_without_secret)} bots without webhook secrets")
        
        # Generate webhook secrets for bots that don't have one
        for bot in bots_without_secret:
            webhook_secret = ManagedBotRepository.generate_webhook_secret()
            bot.webhook_secret = webhook_secret
            print(f"Generated webhook secret for bot {bot.id} ({bot.username})")
        
        # Commit the changes
        db.commit()
        print(f"Successfully generated webhook secrets for {len(bots_without_secret)} bots")
        
        # Print webhook URLs for all bots
        print("\nWebhook URLs for all bots:")
        for bot in managed_bots:
            print(f"Bot {bot.id} ({bot.username}): /webhook/{bot.webhook_secret}")
            
    except Exception as e:
        db.rollback()
        print(f"Error generating webhook secrets: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    generate_webhook_secrets()