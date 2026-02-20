"""
Utility functions for SalesEcho AI
"""

import re
import random
from typing import Optional
from unidecode import unidecode
from app.core.database import prisma
import logging

logger = logging.getLogger(__name__)


async def generate_slug(organization_name: str) -> str:
    """
    Generate a URL-friendly slug from an organization name.
    
    Handles Hebrew/Unicode characters by transliterating to ASCII.
    Ensures uniqueness by checking the database and appending a random
    4-digit suffix if the slug already exists.
    
    Args:
        organization_name: The organization name (can contain Hebrew/Unicode)
    
    Returns:
        A unique, URL-friendly slug (e.g., "acme-corp" or "acme-corp-1234")
    
    Example:
        >>> await generate_slug("Acme Corp")
        "acme-corp"
        
        >>> await generate_slug("חברת אקמה בע״מ")
        "hevrat-akma-bm"
        
        >>> await generate_slug("Test Org")  # If "test-org" exists
        "test-org-5678"  # Random 4-digit suffix
    """
    if not organization_name or not organization_name.strip():
        raise ValueError("Organization name cannot be empty")
    
    # Step 1: Transliterate Hebrew/Unicode to ASCII
    # unidecode converts Hebrew characters to their ASCII equivalents
    # e.g., "חברת אקמה" -> "hevrat akma"
    transliterated = unidecode(organization_name)
    
    # Step 2: Lowercase
    slug = transliterated.lower()
    
    # Step 3: Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # Step 4: Remove special characters, keep only alphanumeric and hyphens
    # This removes Hebrew characters that weren't transliterated, punctuation, etc.
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    
    # Step 5: Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Step 6: Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Step 7: Ensure slug is not empty (fallback if all characters were removed)
    if not slug:
        slug = 'org'
    
    # Step 8: Check uniqueness and append suffix if needed
    unique_slug = await _ensure_unique_slug(slug)
    
    return unique_slug


async def _ensure_unique_slug(base_slug: str, max_attempts: int = 10) -> str:
    """
    Ensure slug uniqueness by checking database and appending random suffix if needed.
    
    Args:
        base_slug: The base slug to check
        max_attempts: Maximum attempts to find a unique slug (default: 10)
    
    Returns:
        A unique slug (either base_slug or base_slug with random suffix)
    """
    # Check if base slug exists
    existing = await prisma.organization.find_unique(
        where={"slug": base_slug}
    )
    
    if not existing:
        return base_slug
    
    # Slug exists, try to find unique one with random suffix
    logger.info(f"Slug '{base_slug}' already exists, generating unique variant")
    
    for attempt in range(max_attempts):
        # Generate random 4-digit suffix
        suffix = random.randint(1000, 9999)
        candidate_slug = f"{base_slug}-{suffix}"
        
        # Check if this candidate exists
        existing = await prisma.organization.find_unique(
            where={"slug": candidate_slug}
        )
        
        if not existing:
            logger.info(f"Generated unique slug: '{candidate_slug}'")
            return candidate_slug
    
    # If we've exhausted attempts, raise an error
    raise ValueError(
        f"Could not generate unique slug after {max_attempts} attempts. "
        f"Base slug: '{base_slug}'"
    )


def sanitize_slug(slug: str) -> str:
    """
    Sanitize a slug string (removes invalid characters, normalizes).
    
    This is a synchronous helper function for basic slug sanitization
    without database checks. Use generate_slug() for full functionality.
    
    Args:
        slug: Raw slug string
    
    Returns:
        Sanitized slug string
    """
    if not slug:
        return ''
    
    # Transliterate Unicode to ASCII
    slug = unidecode(slug)
    
    # Lowercase
    slug = slug.lower()
    
    # Replace spaces/underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # Remove special characters
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    
    # Remove multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug or 'slug'
