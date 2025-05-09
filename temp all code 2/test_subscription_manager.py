import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session
from app.models.models import Subscription, PendingSubscription, SubscriptionStatus, PendingSubscriptionStatus
from app.services.subscription_manager import SubscriptionManager
from app.repositories.subscription import SubscriptionRepository
from app.repositories.pending_subscription import PendingSubscriptionRepository
from app.repositories.subscription_plan import SubscriptionPlanRepository
from app.schemas.schemas import SubscriptionCreate, PendingSubscriptionCreate


class TestSubscriptionManager(unittest.TestCase):
    """Test cases for SubscriptionManager"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = MagicMock(spec=Session)
        self.end_user_id = 123
        self.managed_bot_id = 456
        self.plan_id = 789
        self.duration_days = 30

    @patch('app.repositories.subscription_plan.SubscriptionPlanRepository.get_by_id')
    @patch('app.repositories.subscription.SubscriptionRepository.create')
    async def test_create_subscription_success(self, mock_create, mock_get_plan):
        """Test creating a subscription successfully"""
        # Arrange
        mock_plan = MagicMock()
        mock_plan.duration_days = self.duration_days
        mock_get_plan.return_value = mock_plan
        
        mock_subscription = MagicMock()
        mock_subscription.id = 1
        mock_subscription.end_date = "2023-12-31"
        mock_create.return_value = mock_subscription
        
        # Act
        result = await SubscriptionManager.create_subscription(
            self.db, self.end_user_id, self.managed_bot_id, self.plan_id
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["subscription"], mock_subscription)
        mock_get_plan.assert_called_once_with(self.db, self.plan_id)
        mock_create.assert_called_once()

    @patch('app.repositories.subscription_plan.SubscriptionPlanRepository.get_by_id')
    async def test_create_subscription_plan_not_found(self, mock_get_plan):
        """Test creating a subscription when plan is not found"""
        # Arrange
        mock_get_plan.return_value = None
        
        # Act
        result = await SubscriptionManager.create_subscription(
            self.db, self.end_user_id, self.managed_bot_id, self.plan_id
        )
        
        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Subscription plan not found")

    @patch('app.repositories.subscription_plan.SubscriptionPlanRepository.get_by_id')
    @patch('app.repositories.subscription.SubscriptionRepository.create')
    async def test_create_subscription_exception(self, mock_create, mock_get_plan):
        """Test creating a subscription with an exception"""
        # Arrange
        mock_plan = MagicMock()
        mock_plan.duration_days = self.duration_days
        mock_get_plan.return_value = mock_plan
        
        mock_create.side_effect = Exception("Database error")
        
        # Act
        result = await SubscriptionManager.create_subscription(
            self.db, self.end_user_id, self.managed_bot_id, self.plan_id
        )
        
        # Assert
        self.assertFalse(result["success"])
        self.assertIn("Error creating subscription", result["message"])

    @patch('app.repositories.subscription_plan.SubscriptionPlanRepository.get_by_id')
    @patch('app.repositories.pending_subscription.PendingSubscriptionRepository.get_pending_by_end_user_and_bot')
    @patch('app.repositories.pending_subscription.PendingSubscriptionRepository.create')
    async def test_create_pending_subscription_success(self, mock_create, mock_get_pending, mock_get_plan):
        """Test creating a pending subscription successfully"""
        # Arrange
        mock_plan = MagicMock()
        mock_get_plan.return_value = mock_plan
        mock_get_pending.return_value = None
        
        mock_pending = MagicMock()
        mock_pending.id = 1
        mock_create.return_value = mock_pending
        
        # Act
        result = await SubscriptionManager.create_pending_subscription(
            self.db, self.end_user_id, self.managed_bot_id, self.plan_id
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["pending_subscription"], mock_pending)
        mock_get_plan.assert_called_once_with(self.db, self.plan_id)
        mock_get_pending.assert_called_once_with(self.db, self.end_user_id, self.managed_bot_id)
        mock_create.assert_called_once()

    @patch('app.repositories.subscription_plan.SubscriptionPlanRepository.get_by_id')
    async def test_create_pending_subscription_plan_not_found(self, mock_get_plan):
        """Test creating a pending subscription when plan is not found"""
        # Arrange
        mock_get_plan.return_value = None
        
        # Act
        result = await SubscriptionManager.create_pending_subscription(
            self.db, self.end_user_id, self.managed_bot_id, self.plan_id
        )
        
        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Subscription plan not found")

    @patch('app.repositories.subscription_plan.SubscriptionPlanRepository.get_by_id')
    @patch('app.repositories.pending_subscription.PendingSubscriptionRepository.get_pending_by_end_user_and_bot')
    async def test_create_pending_subscription_already_exists(self, mock_get_pending, mock_get_plan):
        """Test creating a pending subscription when one already exists"""
        # Arrange
        mock_plan = MagicMock()
        mock_get_plan.return_value = mock_plan
        
        mock_existing = MagicMock()
        mock_get_pending.return_value = mock_existing
        
        # Act
        result = await SubscriptionManager.create_pending_subscription(
            self.db, self.end_user_id, self.managed_bot_id, self.plan_id
        )
        
        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "You already have a pending subscription request")

    @patch('app.repositories.pending_subscription.PendingSubscriptionRepository.get_by_id')
    @patch('app.services.subscription_manager.SubscriptionManager.create_subscription')
    @patch('app.repositories.pending_subscription.PendingSubscriptionRepository.update_status')
    async def test_approve_pending_subscription_success(self, mock_update_status, mock_create_sub, mock_get_pending):
        """Test approving a pending subscription successfully"""
        # Arrange
        mock_pending = MagicMock()
        mock_pending.id = 1
        mock_pending.end_user_id = self.end_user_id
        mock_pending.managed_bot_id = self.managed_bot_id
        mock_pending.plan_id = self.plan_id
        mock_pending.status = PendingSubscriptionStatus.pending_approval
        mock_get_pending.return_value = mock_pending
        
        mock_subscription = MagicMock()
        mock_subscription.id = 2
        mock_create_sub.return_value = {"success": True, "subscription": mock_subscription}
        
        mock_updated_pending = MagicMock()
        mock_update_status.return_value = mock_updated_pending
        
        # Act
        result = await SubscriptionManager.approve_pending_subscription(self.db, 1)
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["subscription"], mock_subscription)
        self.assertEqual(result["pending_subscription"], mock_updated_pending)
        mock_get_pending.assert_called_once_with(self.db, 1)
        mock_create_sub.assert_called_once_with(
            self.db, self.end_user_id, self.managed_bot_id, self.plan_id
        )
        mock_update_status.assert_called_once_with(
            self.db, 1, PendingSubscriptionStatus.approved
        )


if __name__ == "__main__":
    unittest.main()