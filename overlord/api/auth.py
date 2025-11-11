"""Authentication and authorization for Fleet API"""

from fastapi import HTTPException, Header, status
from config import settings
import hashlib


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify API key from request header"""

    # For now, use a simple comparison with the configured API key
    # In production, this should check against hashed keys in the database
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Simple validation - in production, hash and compare with database
    expected_key = settings.API_SECRET_KEY
    if x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    return x_api_key


def generate_api_key(device_id: str) -> tuple[str, str]:
    """Generate API key for device

    Returns:
        tuple: (plain_key, hashed_key) - plain_key to give to device, hashed_key to store in DB
    """
    import secrets

    # Generate random key
    plain_key = f"fleet_{device_id}_{secrets.token_urlsafe(32)}"

    # Hash for storage
    hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()

    return plain_key, hashed_key
