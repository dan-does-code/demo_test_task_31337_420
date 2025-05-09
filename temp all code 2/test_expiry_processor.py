import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session
from app.models.models import Subscription, SubscriptionStatus
from app.services.expiry_processor import ExpiryProcessor
from app.repositories.subscription import SubscriptionRepository
from app.services.access_granter import AccessGranter
from app.repositories.managed_bot import ManagedBotRepository
from app.services.telegram_api import TelegramAPIWrapper
from app.services.config_service import ConfigService


class TestExpiryProcessor(unittest.TestCase):
    """Test cases for ExpiryProcessor"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = MagicMock(spec=Session)

    @patch('app.repositories.subscription.SubscriptionRepository.get_expired')
    async def test_process_expired_subscriptions_none_found(self, mock_get_expired):
        """Test processing expired subscriptions when none are found"""
        # Arrange
        mock_get_expired.return_value = []
        
        # Act
        result = await ExpiryProcessor.process_expired_subscriptions(self.db)
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["processed"], 0)
        self.assertIn("No expired subscriptions found", result["message"])

    @patch('app.repositories.subscription.SubscriptionRepository.get_expired')
    @patch('app.services.access_granter.AccessGranter.revoke_access')
    @patch('app.repositories.subscription.SubscriptionRepository.update_status')
    @patch('app.repositories.managed_bot.ManagedBotRepository.get_decrypted_token')
    @patch('app.services.telegram_api.TelegramAPIWrapper.send_message')
    @patch('app.services.config_service.ConfigService.get_message')
    async def test_process_expired_subscriptions_success(self, mock_get_message, mock_send_message, 
                                                       mock_get_token, mock_update_status, 
                                                       mock_revoke_access, mock_get_expired):
        """Test processing expired subscriptions successfully"""
        # Arrange
        subscription1 = MagicMock()
        subscription1.id = 1
        subscription1.end_user_id = 123
        subscription1.managed_bot_id = 456
        
        subscription2 = MagicMock()
        subscription2.id = 2
        subscription2.end_user_id = 789
        subscription2.managed_bot_id = 456
        
        mock_get_expired.return_value = [subscription1, subscription2]
        mock_revoke_access.return_value = {"success": True}
        mock_update_status.return_value = MagicMock()
        mock_get_token.return_value = "test_token"
        mock_get_message.return_value = "Your subscription has expired"
        mock_send_message.return_value = True
        
        # Act
        result = await ExpiryProcessor.process_expired_subscriptions(self.db)
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["processed"], 2)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(len(result["results"]), 2)
        mock_revoke_access.assert_called()
        mock_update_status.assert_called()
        mock_get_token.assert_called()
        mock_send_message.assert_called()

    @patch('app.repositories.subscription.SubscriptionRepository.get_expired')
    @patch('app.services.access_granter.AccessGranter.revoke_access')
    async def test_process_expired_subscriptions_with_error(self, mock_revoke_access, mock_get_expired):
        """Test processing expired subscriptions with an error"""
        # Arrange
        subscription = MagicMock()
        subscription.id = 1
        subscription.end_user_id = 123
        subscription.managed_bot_id = 456
        
        mock_get_expired.return_value = [subscription]
        mock_revoke_access.side_effect = Exception("Test error")
        
        # Act
        result = await ExpiryProcessor.process_expired_subscriptions(self.db)
        
        # Assert
        self.assertTrue(result["success"])  # Overall process still succeeds
        self.assertEqual(result["processed"], 0)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(len(result["results"]), 1)
        self.assertFalse(result["results"][0]["success"])
        self.assertIn("Test error", result["results"][0]["error"])


if __name__ == "__main__":
    unittest.main()