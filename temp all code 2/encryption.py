from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Load environment variables
load_dotenv()

# Get secret key from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")


def get_encryption_key():
    """Generate a Fernet key from the SECRET_KEY environment variable"""
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is not set")
    
    # Use PBKDF2HMAC to derive a key from the SECRET_KEY
    salt = b'komandamaker_salt'  # A fixed salt for key derivation
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return key


def encrypt_text(text):
    """Encrypt a text string"""
    if not text:
        return None
    
    key = get_encryption_key()
    f = Fernet(key)
    encrypted_data = f.encrypt(text.encode())
    return encrypted_data.decode()


def decrypt_text(encrypted_text):
    """Decrypt an encrypted text string"""
    if not encrypted_text:
        return None
    
    key = get_encryption_key()
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_text.encode())
    return decrypted_data.decode()