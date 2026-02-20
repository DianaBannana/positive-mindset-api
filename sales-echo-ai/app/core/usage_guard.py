"""
Usage Guard - Trial Constraints & Feature Flag Enforcement

This module provides:
- Quota checking (meetings, minutes)
- Trial expiration validation
- Feature bundle verification
- Usage tracking
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException

from app.core.database import get_prisma

logger = logging.getLogger(__name__)


class FeatureBundle(Enum):
    """Available subscription tiers."""
    TRIAL = "trial"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Feature definitions per bundle
BUNDLE_FEATURES: Dict[str, Dict[str, Any]] = {
    "trial": {
        "email": True,
        "whatsapp": True,
        "calendar": False,
        "crm": False,
        "api_access": False,
        "priority_support": False,
        "max_meetings": 10,
        "max_minutes": 60,
        "historical_context": False,  # No client history in trial
        "custom_brain": False,  # No custom prompts in trial
    },
    "starter": {
        "email": True,
        "whatsapp": True,
        "calendar": True,
        "crm": False,
        "api_access": False,
        "priority_support": False,
        "max_meetings": 50,
        "max_minutes": 300,
        "historical_context": True,
        "custom_brain": True,
    },
    "pro": {
        "email": True,
        "whatsapp": True,
        "calendar": True,
        "crm": True,
        "api_access": True,
        "priority_support": False,
        "max_meetings": 200,
        "max_minutes": 1000,
        "historical_context": True,
        "custom_brain": True,
    },
    "enterprise": {
        "email": True,
        "whatsapp": True,
        "calendar": True,
        "crm": True,
        "api_access": True,
        "priority_support": True,
        "max_meetings": 0,  # Unlimited
        "max_minutes": 0,   # Unlimited
        "historical_context": True,
        "custom_brain": True,
    },
}


@dataclass
class UsageStatus:
    """Current usage status for an organization."""
    org_id: str
    bundle: str
    meetings_used: int
    meetings_limit: int
    minutes_used: float
    minutes_limit: int
    trial_expires_at: Optional[datetime]
    is_trial: bool
    is_expired: bool
    is_over_quota: bool
    days_remaining: Optional[int]
    meetings_remaining: int
    minutes_remaining: float
    
    @property
    def can_process(self) -> bool:
        """Check if org can process a new meeting."""
        return not self.is_expired and not self.is_over_quota
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "org_id": self.org_id,
            "bundle": self.bundle,
            "is_trial": self.is_trial,
            "is_expired": self.is_expired,
            "is_over_quota": self.is_over_quota,
            "can_process": self.can_process,
            "meetings": {
                "used": self.meetings_used,
                "limit": self.meetings_limit,
                "remaining": self.meetings_remaining,
                "unlimited": self.meetings_limit == 0,
            },
            "minutes": {
                "used": round(self.minutes_used, 1),
                "limit": self.minutes_limit,
                "remaining": round(self.minutes_remaining, 1),
                "unlimited": self.minutes_limit == 0,
            },
            "trial": {
                "expires_at": self.trial_expires_at.isoformat() if self.trial_expires_at else None,
                "days_remaining": self.days_remaining,
            } if self.is_trial else None,
        }


class UsageGuardError(HTTPException):
    """Custom exception for usage guard violations."""
    
    def __init__(self, reason: str, usage_status: UsageStatus):
        self.usage_status = usage_status
        detail = {
            "error": "quota_exceeded",
            "reason": reason,
            "usage": usage_status.to_dict(),
            "upgrade_url": "/dashboard/settings?tab=billing",
            "message": self._get_friendly_message(reason),
        }
        super().__init__(status_code=402, detail=detail)
    
    def _get_friendly_message(self, reason: str) -> str:
        """Get user-friendly error message."""
        if reason == "trial_expired":
            return "Your trial has expired. Upgrade to continue analyzing calls."
        elif reason == "meetings_quota":
            return f"You've used all {self.usage_status.meetings_limit} meetings in your plan. Upgrade for more."
        elif reason == "minutes_quota":
            return f"You've used all {self.usage_status.minutes_limit} minutes in your plan. Upgrade for more."
        else:
            return "Usage limit reached. Please upgrade your plan."


async def get_usage_status(org_id: str) -> UsageStatus:
    """
    Get current usage status for an organization.
    
    Args:
        org_id: Organization ID
        
    Returns:
        UsageStatus object with current quotas and usage
    """
    prisma = get_prisma()
    
    # Fetch org settings
    settings = await prisma.organizationsettings.find_unique(
        where={"org_id": org_id}
    )
    
    if not settings:
        # Create default trial settings if none exist
        settings = await prisma.organizationsettings.create(
            data={
                "org_id": org_id,
                "feature_bundle": "trial",
                "max_meetings": 10,
                "meetings_count": 0,
                "max_minutes": 60,
                "minutes_used": 0,
                "trial_expires_at": datetime.utcnow().replace(
                    hour=23, minute=59, second=59
                ) + __import__("datetime").timedelta(days=14),  # 14-day trial
            }
        )
    
    bundle = settings.feature_bundle or "trial"
    is_trial = bundle == "trial"
    
    # Check trial expiration
    trial_expires_at = settings.trial_expires_at
    is_expired = False
    days_remaining = None
    
    if is_trial and trial_expires_at:
        now = datetime.utcnow()
        if now > trial_expires_at:
            is_expired = True
            days_remaining = 0
        else:
            days_remaining = (trial_expires_at - now).days
    
    # Check quotas
    meetings_used = settings.meetings_count or 0
    meetings_limit = settings.max_meetings or 0
    minutes_used = settings.minutes_used or 0.0
    minutes_limit = settings.max_minutes or 0
    
    # Calculate remaining (0 = unlimited)
    meetings_remaining = max(0, meetings_limit - meetings_used) if meetings_limit > 0 else float("inf")
    minutes_remaining = max(0, minutes_limit - minutes_used) if minutes_limit > 0 else float("inf")
    
    # Check if over quota
    is_over_quota = False
    if meetings_limit > 0 and meetings_used >= meetings_limit:
        is_over_quota = True
    if minutes_limit > 0 and minutes_used >= minutes_limit:
        is_over_quota = True
    
    return UsageStatus(
        org_id=org_id,
        bundle=bundle,
        meetings_used=meetings_used,
        meetings_limit=meetings_limit,
        minutes_used=minutes_used,
        minutes_limit=minutes_limit,
        trial_expires_at=trial_expires_at,
        is_trial=is_trial,
        is_expired=is_expired,
        is_over_quota=is_over_quota,
        days_remaining=days_remaining,
        meetings_remaining=int(meetings_remaining) if meetings_remaining != float("inf") else -1,
        minutes_remaining=float(minutes_remaining) if minutes_remaining != float("inf") else -1,
    )


async def check_can_process(org_id: str, is_simulation: bool = False) -> UsageStatus:
    """
    Check if organization can process a new meeting.
    
    Args:
        org_id: Organization ID
        is_simulation: If True, skip quota check (for demo purposes)
        
    Returns:
        UsageStatus if allowed
        
    Raises:
        UsageGuardError (402) if quota exceeded or trial expired
    """
    status = await get_usage_status(org_id)
    
    # Simulations don't count towards quota
    if is_simulation:
        logger.info(f"[UsageGuard] Simulation mode - skipping quota check for {org_id}")
        return status
    
    # Check trial expiration
    if status.is_expired:
        logger.warning(f"[UsageGuard] Trial expired for org {org_id}")
        raise UsageGuardError("trial_expired", status)
    
    # Check meeting quota
    if status.meetings_limit > 0 and status.meetings_used >= status.meetings_limit:
        logger.warning(f"[UsageGuard] Meeting quota exceeded for org {org_id}: {status.meetings_used}/{status.meetings_limit}")
        raise UsageGuardError("meetings_quota", status)
    
    # Check minutes quota
    if status.minutes_limit > 0 and status.minutes_used >= status.minutes_limit:
        logger.warning(f"[UsageGuard] Minutes quota exceeded for org {org_id}: {status.minutes_used}/{status.minutes_limit}")
        raise UsageGuardError("minutes_quota", status)
    
    logger.info(f"[UsageGuard] Quota check passed for org {org_id}: {status.meetings_used}/{status.meetings_limit} meetings")
    return status


async def increment_usage(
    org_id: str,
    meetings: int = 1,
    minutes: float = 0,
    is_simulation: bool = False,
) -> None:
    """
    Increment usage counters for an organization.
    
    Args:
        org_id: Organization ID
        meetings: Number of meetings to add
        minutes: Number of minutes to add
        is_simulation: If True, skip increment (for demo purposes)
    """
    if is_simulation:
        logger.info(f"[UsageGuard] Simulation mode - skipping usage increment for {org_id}")
        return
    
    prisma = get_prisma()
    
    await prisma.organizationsettings.update(
        where={"org_id": org_id},
        data={
            "meetings_count": {"increment": meetings},
            "minutes_used": {"increment": minutes},
        }
    )
    
    logger.info(f"[UsageGuard] Incremented usage for {org_id}: +{meetings} meetings, +{minutes:.1f} minutes")


async def check_feature_access(org_id: str, feature: str) -> Tuple[bool, Optional[str]]:
    """
    Check if organization has access to a specific feature.
    
    Args:
        org_id: Organization ID
        feature: Feature name (e.g., "crm", "api_access")
        
    Returns:
        Tuple of (has_access, required_bundle)
        If has_access is False, required_bundle indicates minimum bundle needed
    """
    prisma = get_prisma()
    
    settings = await prisma.organizationsettings.find_unique(
        where={"org_id": org_id}
    )
    
    if not settings:
        # Default to trial features
        bundle = "trial"
    else:
        bundle = settings.feature_bundle or "trial"
    
    bundle_config = BUNDLE_FEATURES.get(bundle, BUNDLE_FEATURES["trial"])
    has_access = bundle_config.get(feature, False)
    
    if has_access:
        return True, None
    
    # Find minimum bundle that has this feature
    for bundle_name in ["starter", "pro", "enterprise"]:
        if BUNDLE_FEATURES[bundle_name].get(feature, False):
            return False, bundle_name
    
    return False, None


async def get_bundle_features(org_id: str) -> Dict[str, Any]:
    """
    Get all features available to an organization.
    
    Args:
        org_id: Organization ID
        
    Returns:
        Dict of feature_name -> is_available
    """
    prisma = get_prisma()
    
    settings = await prisma.organizationsettings.find_unique(
        where={"org_id": org_id}
    )
    
    bundle = settings.feature_bundle if settings else "trial"
    return BUNDLE_FEATURES.get(bundle, BUNDLE_FEATURES["trial"])


def get_bundle_info(bundle: str) -> Dict[str, Any]:
    """Get information about a specific bundle."""
    features = BUNDLE_FEATURES.get(bundle, BUNDLE_FEATURES["trial"])
    
    bundle_names = {
        "trial": "Trial",
        "starter": "Starter",
        "pro": "Pro",
        "enterprise": "Enterprise",
    }
    
    bundle_prices = {
        "trial": 0,
        "starter": 49,
        "pro": 149,
        "enterprise": 499,
    }
    
    return {
        "id": bundle,
        "name": bundle_names.get(bundle, bundle.title()),
        "price_monthly": bundle_prices.get(bundle, 0),
        "features": features,
    }


def get_all_bundles() -> list:
    """Get information about all available bundles."""
    return [get_bundle_info(b) for b in ["trial", "starter", "pro", "enterprise"]]
