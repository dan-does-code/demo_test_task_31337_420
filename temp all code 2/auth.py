# File: app/dependencies/auth.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.models import PlatformUser
from app.repositories.platform_user import PlatformUserRepository # Added import

# In a real application, this would be replaced with proper authentication
# such as OAuth2 with JWT tokens or another authentication mechanism

async def get_current_user(db: Session = Depends(get_db)) -> PlatformUser:
    """
    Get the current authenticated user.

    In a real application, this would extract user information from
    authentication tokens or session data. For now, this is a placeholder
    that should be replaced with proper authentication logic.

    Returns:
        PlatformUser: The authenticated platform user

    Raises:
        HTTPException: If authentication fails
    """
    # --- START: TEMPORARY FIX - REMOVE FOR PRODUCTION ---
    # This is a placeholder for development/testing ONLY.
    # It assumes the first platform user in the database is the admin.
    # Replace this with real authentication before deploying.
    logger.warning("Using placeholder authentication in get_current_user. NOT FOR PRODUCTION.")
    first_user = PlatformUserRepository.get_all(db, limit=1)
    if not first_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Temporary Auth Failed: No platform users found in DB.",
        )
    return first_user[0]
    # --- END: TEMPORARY FIX ---

    # Original placeholder code (commented out):
    # raise HTTPException(
    #     status_code=status.HTTP_501_NOT_IMPLEMENTED,
    #     detail="Authentication not implemented. Replace this dependency with proper authentication."
    # )

# Add necessary imports at the top if not already present
from app.utils.logger import get_logger
logger = get_logger(__name__)