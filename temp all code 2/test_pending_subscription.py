import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.models.models import PendingSubscription, PendingSubscriptionStatus
from app.repositories.pending_subscription import PendingSubscriptionRepository
from app.schemas.schemas import PendingSubscriptionCreate, PendingSubscriptionUpdate


class TestPendingSubscriptionRepository(unittest.TestCase):
    """Test cases for PendingSubscriptionRepository"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = MagicMock(spec=Session)
        self.pending_subscription_create = PendingSubscriptionCreate(
            end_user_id=123,
            managed_bot_id=456,
            plan_id=789
        )

    def test_create_pending_subscription_success(self):
        """Test creating a pending subscription successfully"""
        # Arrange
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()
        
        # Act
        result = PendingSubscriptionRepository.create(self.db, self.pending_subscription_create)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.end_user_id, self.pending_subscription_create.end_user_id)
        self.assertEqual(result.managed_bot_id, self.pending_subscription_create.managed_bot_id)
        self.assertEqual(result.plan_id, self.pending_subscription_create.plan_id)
        self.assertEqual(result.status, PendingSubscriptionStatus.pending_approval)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_create_pending_subscription_exception(self):
        """Test creating a pending subscription with an exception"""
        # Arrange
        self.db.add = MagicMock()
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        
        # Act & Assert
        with self.assertRaises(Exception):
            PendingSubscriptionRepository.create(self.db, self.pending_subscription_create)
        self.db.rollback.assert_called_once()

    def test_get_by_id_found(self):
        """Test getting a pending subscription by ID when it exists"""
        # Arrange
        expected_subscription = PendingSubscription(id=1, end_user_id=123)
        self.db.query.return_value.filter.return_value.first.return_value = expected_subscription
        
        # Act
        result = PendingSubscriptionRepository.get_by_id(self.db, 1)
        
        # Assert
        self.assertEqual(result, expected_subscription)

    def test_get_by_id_not_found(self):
        """Test getting a pending subscription by ID when it doesn't exist"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = PendingSubscriptionRepository.get_by_id(self.db, 999)
        
        # Assert
        self.assertIsNone(result)

    def test_get_pending_by_managed_bot(self):
        """Test getting pending subscriptions by managed bot"""
        # Arrange
        expected_subscriptions = [PendingSubscription(id=1), PendingSubscription(id=2)]
        self.db.query.return_value.filter.return_value.all.return_value = expected_subscriptions
        
        # Act
        result = PendingSubscriptionRepository.get_pending_by_managed_bot(self.db, 456)
        
        # Assert
        self.assertEqual(result, expected_subscriptions)

    def test_update_status_success(self):
        """Test updating pending subscription status successfully"""
        # Arrange
        subscription = PendingSubscription(id=1, status=PendingSubscriptionStatus.pending_approval)
        self.db.query.return_value.filter.return_value.first.return_value = subscription
        
        # Act
        result = PendingSubscriptionRepository.update_status(self.db, 1, PendingSubscriptionStatus.approved)
        
        # Assert
        self.assertEqual(result.status, PendingSubscriptionStatus.approved)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_update_status_not_found(self):
        """Test updating pending subscription status when subscription doesn't exist"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = PendingSubscriptionRepository.update_status(self.db, 999, PendingSubscriptionStatus.approved)
        
        # Assert
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()