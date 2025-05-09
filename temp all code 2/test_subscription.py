import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import Subscription, SubscriptionStatus
from app.repositories.subscription import SubscriptionRepository
from app.schemas.schemas import SubscriptionCreate, SubscriptionUpdate


class TestSubscriptionRepository(unittest.TestCase):
    """Test cases for SubscriptionRepository"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = MagicMock(spec=Session)
        self.subscription_create = SubscriptionCreate(
            end_user_id=123,
            managed_bot_id=456,
            plan_id=789
        )
        self.duration_days = 30

    def test_create_subscription_success(self):
        """Test creating a subscription successfully"""
        # Arrange
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()
        
        # Act
        result = SubscriptionRepository.create(self.db, self.subscription_create, self.duration_days)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.end_user_id, self.subscription_create.end_user_id)
        self.assertEqual(result.managed_bot_id, self.subscription_create.managed_bot_id)
        self.assertEqual(result.plan_id, self.subscription_create.plan_id)
        self.assertEqual(result.status, SubscriptionStatus.active)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_get_by_id_found(self):
        """Test getting a subscription by ID when it exists"""
        # Arrange
        expected_subscription = Subscription(id=1, end_user_id=123)
        self.db.query.return_value.filter.return_value.first.return_value = expected_subscription
        
        # Act
        result = SubscriptionRepository.get_by_id(self.db, 1)
        
        # Assert
        self.assertEqual(result, expected_subscription)

    def test_get_by_id_not_found(self):
        """Test getting a subscription by ID when it doesn't exist"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = SubscriptionRepository.get_by_id(self.db, 999)
        
        # Assert
        self.assertIsNone(result)

    def test_get_expired(self):
        """Test getting expired subscriptions"""
        # Arrange
        expected_subscriptions = [Subscription(id=1), Subscription(id=2)]
        self.db.query.return_value.filter.return_value.all.return_value = expected_subscriptions
        
        # Act
        result = SubscriptionRepository.get_expired(self.db)
        
        # Assert
        self.assertEqual(result, expected_subscriptions)

    def test_update_status_success(self):
        """Test updating subscription status successfully"""
        # Arrange
        subscription = Subscription(id=1, status=SubscriptionStatus.active)
        self.db.query.return_value.filter.return_value.first.return_value = subscription
        
        # Act
        result = SubscriptionRepository.update_status(self.db, 1, SubscriptionStatus.expired)
        
        # Assert
        self.assertEqual(result.status, SubscriptionStatus.expired)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_update_status_not_found(self):
        """Test updating subscription status when subscription doesn't exist"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = SubscriptionRepository.update_status(self.db, 999, SubscriptionStatus.expired)
        
        # Assert
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()