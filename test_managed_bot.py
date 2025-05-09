import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.models.models import ManagedBot
from app.repositories.managed_bot import ManagedBotRepository
from app.schemas.schemas import ManagedBotCreate, ManagedBotUpdate


class TestManagedBotRepository(unittest.TestCase):
    """Test cases for ManagedBotRepository"""

    def setUp(self):
        """Set up test fixtures"""
        self.db = MagicMock(spec=Session)
        self.managed_bot_create = ManagedBotCreate(
            platform_user_id=123,
            tg_token="test_token_123:ABC",
            username="test_bot",
            config_data={"welcome_message": "Hello"},
            intended_payment_methods=["crypto"]
        )

    @patch('app.repositories.managed_bot.encrypt_text')
    def test_create_managed_bot_success(self, mock_encrypt):
        """Test creating a managed bot successfully"""
        # Arrange
        mock_encrypt.return_value = "encrypted_token"
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()
        
        # Act
        result = ManagedBotRepository.create(self.db, self.managed_bot_create)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.platform_user_id, self.managed_bot_create.platform_user_id)
        self.assertEqual(result.username, self.managed_bot_create.username)
        self.assertEqual(result.tg_token_encrypted, "encrypted_token")
        mock_encrypt.assert_called_once_with(self.managed_bot_create.tg_token)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    @patch('app.repositories.managed_bot.get_logger')
    @patch('app.repositories.managed_bot.encrypt_text')
    def test_create_managed_bot_exception(self, mock_encrypt, mock_logger):
        """Test exception handling when creating a managed bot"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        mock_encrypt.return_value = "encrypted_token"
        self.db.add = MagicMock()
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        
        # Act & Assert
        with self.assertRaises(Exception):
            ManagedBotRepository.create(self.db, self.managed_bot_create)
        
        self.db.rollback.assert_called_once()
        mock_logger_instance.error.assert_called_once()

    def test_get_by_id_found(self):
        """Test getting a managed bot by ID when it exists"""
        # Arrange
        expected_bot = ManagedBot(id=1, platform_user_id=123)
        self.db.query.return_value.filter.return_value.first.return_value = expected_bot
        
        # Act
        result = ManagedBotRepository.get_by_id(self.db, 1)
        
        # Assert
        self.assertEqual(result, expected_bot)

    def test_get_by_id_not_found(self):
        """Test getting a managed bot by ID when it doesn't exist"""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = ManagedBotRepository.get_by_id(self.db, 999)
        
        # Assert
        self.assertIsNone(result)

    @patch('app.repositories.managed_bot.encrypt_text')
    def test_update_success(self, mock_encrypt):
        """Test updating a managed bot successfully"""
        # Arrange
        mock_encrypt.return_value = "new_encrypted_token"
        db_bot = ManagedBot(id=1, platform_user_id=123, tg_token_encrypted="old_encrypted_token")
        self.db.query.return_value.filter.return_value.first.return_value = db_bot
        update_data = ManagedBotUpdate(tg_token="new_token")
        
        # Act
        result = ManagedBotRepository.update(self.db, 1, update_data)
        
        # Assert
        self.assertEqual(result, db_bot)
        self.assertEqual(result.tg_token_encrypted, "new_encrypted_token")
        mock_encrypt.assert_called_once_with("new_token")
        self.db.commit.assert_called_once()

    @patch('app.repositories.managed_bot.get_logger')
    def test_update_exception(self, mock_logger):
        """Test exception handling when updating a managed bot"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        db_bot = ManagedBot(id=1, platform_user_id=123)
        self.db.query.return_value.filter.return_value.first.return_value = db_bot
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        update_data = ManagedBotUpdate(username="new_username")
        
        # Act & Assert
        with self.assertRaises(Exception):
            ManagedBotRepository.update(self.db, 1, update_data)
        
        self.db.rollback.assert_called_once()
        mock_logger_instance.error.assert_called_once()

    def test_delete_success(self):
        """Test deleting a managed bot successfully"""
        # Arrange
        db_bot = ManagedBot(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = db_bot
        
        # Act
        result = ManagedBotRepository.delete(self.db, 1)
        
        # Assert
        self.assertTrue(result)
        self.db.delete.assert_called_once_with(db_bot)
        self.db.commit.assert_called_once()

    @patch('app.repositories.managed_bot.get_logger')
    def test_delete_exception(self, mock_logger):
        """Test exception handling when deleting a managed bot"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        db_bot = ManagedBot(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = db_bot
        self.db.delete = MagicMock()
        self.db.commit = MagicMock(side_effect=Exception("Database error"))
        self.db.rollback = MagicMock()
        
        # Act & Assert
        with self.assertRaises(Exception):
            ManagedBotRepository.delete(self.db, 1)
        
        self.db.rollback.assert_called_once()
        mock_logger_instance.error.assert_called_once()

    @patch('app.repositories.managed_bot.decrypt_text')
    @patch('app.repositories.managed_bot.get_logger')
    def test_get_decrypted_token_success(self, mock_logger, mock_decrypt):
        """Test getting a decrypted token successfully"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        mock_decrypt.return_value = "decrypted_token"
        db_bot = ManagedBot(id=1, tg_token_encrypted="encrypted_token")
        self.db.query.return_value.filter.return_value.first.return_value = db_bot
        
        # Act
        result = ManagedBotRepository.get_decrypted_token(self.db, 1)
        
        # Assert
        self.assertEqual(result, "decrypted_token")
        mock_decrypt.assert_called_once_with("encrypted_token")
        mock_logger_instance.debug.assert_called_once()

    @patch('app.repositories.managed_bot.get_logger')
    def test_get_decrypted_token_not_found(self, mock_logger):
        """Test getting a decrypted token when bot is not found"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = ManagedBotRepository.get_decrypted_token(self.db, 999)
        
        # Assert
        self.assertIsNone(result)
        mock_logger_instance.warning.assert_called_once()

    @patch('app.repositories.managed_bot.decrypt_text')
    @patch('app.repositories.managed_bot.get_logger')
    def test_get_decrypted_token_exception(self, mock_logger, mock_decrypt):
        """Test exception handling when getting a decrypted token"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        mock_decrypt.side_effect = Exception("Decryption error")
        db_bot = ManagedBot(id=1, tg_token_encrypted="encrypted_token")
        self.db.query.return_value.filter.return_value.first.return_value = db_bot
        
        # Act
        result = ManagedBotRepository.get_decrypted_token(self.db, 1)
        
        # Assert
        self.assertIsNone(result)
        mock_logger_instance.error.assert_called_once()