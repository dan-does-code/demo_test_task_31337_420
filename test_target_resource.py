import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.models.models import TargetResource
from app.repositories.target_resource import TargetResourceRepository
from app.schemas.schemas import TargetResourceCreate, TargetResourceUpdate


class TestTargetResourceRepository(unittest.TestCase):
    """Test cases for TargetResourceRepository"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = MagicMock(spec=Session)
        self.target_resource_create = TargetResourceCreate(
            managed_bot_id=123,
            tg_chat_id=456,
            type="channel",
            invite_link_type="static",
            custom_link="https://t.me/example",
            is_mandatory=True
        )

    def test_create_target_resource_success(self):
        """Test creating a target resource successfully"""
        # Arrange
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()
        
        # Act
        result = TargetResourceRepository.create(self.db, self.target_resource_create)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.managed_bot_id, self.target_resource_create.managed_bot_id)
        self.assertEqual(result.tg_chat_id, self.target_resource_create.tg_chat_id)
        self.assertEqual(result.type, self.target_resource_create.type)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    @patch('app.utils.logger.get_logger')
    def test_create_target_resource_exception(self, mock_logger):
        """Test exception handling when creating a target resource"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        self.db.add = MagicMock()
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        
        # Act & Assert
        with self.assertRaises(Exception):
            TargetResourceRepository.create(self.db, self.target_resource_create)
        
        self.db.rollback.assert_called_once()
        mock_logger_instance.error.assert_called_once()

    def test_get_by_id_found(self):
        """Test getting a target resource by ID when it exists"""
        # Arrange
        expected_resource = TargetResource(id=1, managed_bot_id=123)
        self.db.query.return_value.filter.return_value.first.return_value = expected_resource
        
        # Act
        result = TargetResourceRepository.get_by_id(self.db, 1)
        
        # Assert
        self.assertEqual(result, expected_resource)

    def test_get_by_id_not_found(self):
        """Test getting a target resource by ID when it doesn't exist"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = TargetResourceRepository.get_by_id(self.db, 999)
        
        # Assert
        self.assertIsNone(result)

    def test_update_success(self):
        """Test updating a target resource successfully"""
        # Arrange
        db_resource = TargetResource(id=1, managed_bot_id=123, tg_chat_id=456)
        self.db.query.return_value.filter.return_value.first.return_value = db_resource
        update_data = TargetResourceUpdate(is_mandatory=False)
        
        # Act
        result = TargetResourceRepository.update(self.db, 1, update_data)
        
        # Assert
        self.assertEqual(result, db_resource)
        self.assertEqual(result.is_mandatory, False)
        self.db.commit.assert_called_once()

    @patch('app.utils.logger.get_logger')
    def test_update_exception(self, mock_logger):
        """Test exception handling when updating a target resource"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        db_resource = TargetResource(id=1, managed_bot_id=123)
        self.db.query.return_value.filter.return_value.first.return_value = db_resource
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        update_data = TargetResourceUpdate(is_mandatory=False)
        
        # Act & Assert
        with self.assertRaises(Exception):
            TargetResourceRepository.update(self.db, 1, update_data)
        
        self.db.rollback.assert_called_once()
        mock_logger_instance.error.assert_called_once()

    def test_delete_success(self):
        """Test deleting a target resource successfully"""
        # Arrange
        db_resource = TargetResource(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = db_resource
        
        # Act
        result = TargetResourceRepository.delete(self.db, 1)
        
        # Assert
        self.assertTrue(result)
        self.db.delete.assert_called_once_with(db_resource)
        self.db.commit.assert_called_once()

    @patch('app.utils.logger.get_logger')
    def test_delete_exception(self, mock_logger):
        """Test exception handling when deleting a target resource"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        db_resource = TargetResource(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = db_resource
        self.db.delete = MagicMock()
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        
        # Act & Assert
        with self.assertRaises(Exception):
            TargetResourceRepository.delete(self.db, 1)
        
        self.db.rollback.assert_called_once()
        mock_logger_instance.error.assert_called_once()