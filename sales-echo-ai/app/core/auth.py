"""
Authentication and Authorization Middleware
Production-ready JWT-based authentication for SalesEcho AI.

TODO: Implement JWT validation with Supabase public key.
Currently a placeholder for future Auth middleware implementation.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import prisma

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


class UserContext:
    """
    User context extracted from JWT token.
    
    This will be populated by Auth middleware in production.
    """
    def __init__(
        self,
        user_id: str,
        org_id: str,
        email: str,
        role: str = "sales_rep"
    ):
        self.user_id = user_id
        self.org_id = org_id
        self.email = email
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserContext:
    """
    Extract and validate user context from JWT token.
    
    PRODUCTION IMPLEMENTATION:
    1. Extract JWT from Authorization header
    2. Validate token signature with Supabase public key
    3. Extract user_id and org_id from token claims
    4. Verify user exists in database
    5. Return UserContext object
    
    CURRENT STATUS: Placeholder - returns None for development.
    This MUST be implemented before production deployment.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        UserContext: Validated user context with org_id and user_id
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # TODO: Implement JWT validation
    # 1. Decode JWT token
    # 2. Validate signature with Supabase public key
    # 3. Extract claims (user_id, org_id, email, role)
    # 4. Verify user exists in database
    # 5. Return UserContext
    
    token = credentials.credentials
    
    # PLACEHOLDER: This is a development bypass
    # In production, this will validate the JWT and extract user context
    logger.warning(
        "DEV_ONLY: Auth middleware not yet implemented. "
        "Using placeholder. Token validation required before production."
    )
    
    # For now, raise an error to force explicit handling
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication middleware not yet implemented. "
               "Use form parameters (org_id, user_id) for development testing."
    )


async def get_user_org_id(user_id: str) -> Optional[str]:
    """
    Get user's org_id from database.
    
    Helper function for development/testing when JWT is not available.
    In production, org_id will come from JWT token claims.
    
    Args:
        user_id: User UUID
        
    Returns:
        org_id if user exists, None otherwise
    """
    try:
        user = await prisma.user.find_unique(where={"id": user_id})
        if user:
            return user.org_id
        return None
    except Exception as e:
        logger.error(f"Failed to get user org_id: {str(e)}")
        return None
