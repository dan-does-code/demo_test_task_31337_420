import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.models.models import SubscriptionPlan
from app.repositories.subscription_plan import SubscriptionPlanRepository
from app.schemas.schemas import SubscriptionPlanCreate, SubscriptionPlanUpdate


class TestSubscriptionPlanRepository(unittest.TestCase):
    """Test cases for SubscriptionPlanRepository"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = MagicMock(spec=Session)
        self.subscription_plan_create = SubscriptionPlanCreate(
            managed_bot_id=123,
            name="Test Plan",
            duration_days=30,
            linked_resource_ids=[1, 2, 3],
            is_visible=True,
            description="Test subscription plan"
        )

    def test_create_subscription_plan_success(self):
        """Test creating a subscription plan successfully"""
        # Arrange
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()
        
        # Act
        result = SubscriptionPlanRepository.create(self.db, self.subscription_plan_create)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.managed_bot_id, self.subscription_plan_create.managed_bot_id)
        self.assertEqual(result.name, self.subscription_plan_create.name)
        self.assertEqual(result.duration_days, self.subscription_plan_create.duration_days)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    @patch('app.repositories.subscription_plan.get_logger')
    def test_create_subscription_plan_exception(self, mock_logger):
        """Test exception handling when creating a subscription plan"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        self.db.add = MagicMock()
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        
        # Act & Assert
        with self.assertRaises(Exception):
            SubscriptionPlanRepository.create(self.db, self.subscription_plan_create)
        
        self.db.rollback.assert_called_once()
        mock_logger_instance.error.assert_called_once()

    def test_get_by_id_found(self):
        """Test getting a subscription plan by ID when it exists"""
        # Arrange
        expected_plan = SubscriptionPlan(id=1, managed_bot_id=123)
        self.db.query.return_value.filter.return_value.first.return_value = expected_plan
        
        # Act
        result = SubscriptionPlanRepository.get_by_id(self.db, 1)
        
        # Assert
        self.assertEqual(result, expected_plan)

    def test_get_by_id_not_found(self):
        """Test getting a subscription plan by ID when it doesn't exist"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = SubscriptionPlanRepository.get_by_id(self.db, 999)
        
        # Assert
        self.assertIsNone(result)

    def test_update_success(self):
        """Test updating a subscription plan successfully"""
        # Arrange
        db_plan = SubscriptionPlan(id=1, managed_bot_id=123, name="Old Name")
        self.db.query.return_value.filter.return_value.first.return_value = db_plan
        update_data = SubscriptionPlanUpdate(name="New Name")
        
        # Act
        result = SubscriptionPlanRepository.update(self.db, 1, update_data)
        
        # Assert
        self.assertEqual(result, db_plan)
        self.assertEqual(result.name, "New Name")
        self.db.commit.assert_called_once()

    @patch('app.repositories.subscription_plan.get_logger')
    def test_update_exception(self, mock_logger):
        """Test exception handling when updating a subscription plan"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        db_plan = SubscriptionPlan(id=1, managed_bot_id=123)
        self.db.query.return_value.filter.return_value.first.return_value = db_plan
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        update_data = SubscriptionPlanUpdate(name="New Name")
        
        # Act & Assert
        with self.assertRaises(Exception):
            SubscriptionPlanRepository.update(self.db, 1, update_data)
        
        self.db.rollback.assert_called_once()
        mock_logger_instance.error.assert_called_once()

    def test_delete_success(self):
        """Test deleting a subscription plan successfully"""
        # Arrange
        db_plan = SubscriptionPlan(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = db_plan
        
        # Act
        result = SubscriptionPlanRepository.delete(self.db, 1)
        
        # Assert
        self.assertTrue(result)
        self.db.delete.assert_called_once_with(db_plan)
        self.db.commit.assert_called_once()

    @patch('app.repositories.subscription_plan.get_logger')
    def test_delete_exception(self, mock_logger):
        """Test exception handling when deleting a subscription plan"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        db_plan = SubscriptionPlan(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = db_plan
        self.db.delete = MagicMock()
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        
        # Act & Assert
        with self.assertRaises(Exception):
            SubscriptionPlanRepository.delete(self.db, 1)
        
        self.db.rollback.assert_called_once()
        mock_logger_instance.error.assert_called_once()