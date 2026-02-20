"""
Billing API - Usage tracking and subscription management

Provides endpoints for:
- Usage status (meetings, minutes, trial info)
- Bundle/feature information
- Subscription management (placeholder for Stripe integration)
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_prisma
from app.core.usage_guard import (
    get_usage_status,
    get_bundle_features,
    get_bundle_info,
    get_all_bundles,
    check_feature_access,
    BUNDLE_FEATURES,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Response Models
# ============================================

class UsageResponse(BaseModel):
    """Usage status response."""
    org_id: str
    bundle: str
    is_trial: bool
    is_expired: bool
    is_over_quota: bool
    can_process: bool
    meetings: Dict[str, Any]
    minutes: Dict[str, Any]
    trial: Optional[Dict[str, Any]]


class BundleInfo(BaseModel):
    """Bundle information response."""
    id: str
    name: str
    price_monthly: int
    features: Dict[str, Any]


class FeatureAccessResponse(BaseModel):
    """Feature access check response."""
    feature: str
    has_access: bool
    current_bundle: str
    required_bundle: Optional[str]
    upgrade_url: Optional[str]


# ============================================
# Usage Endpoints
# ============================================

@router.get("/billing/usage", response_model=UsageResponse)
async def get_org_usage(
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get current usage status for an organization.
    
    Returns meetings used, minutes used, trial status, and quota info.
    """
    # DEV_ONLY_WARNING: org_id should come from JWT in production
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        status = await get_usage_status(org_id)
        return UsageResponse(**status.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting usage status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get usage status")


@router.get("/billing/features")
async def get_org_features(
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get all features available to an organization based on their bundle.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        features = await get_bundle_features(org_id)
        
        return {
            "org_id": org_id,
            "features": features,
        }
        
    except Exception as e:
        logger.error(f"Error getting features: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get features")


@router.get("/billing/feature/{feature}", response_model=FeatureAccessResponse)
async def check_feature(
    feature: str,
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Check if organization has access to a specific feature.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        prisma = get_prisma()
        
        settings_record = await prisma.organizationsettings.find_unique(
            where={"org_id": org_id}
        )
        
        current_bundle = settings_record.feature_bundle if settings_record else "trial"
        has_access, required_bundle = await check_feature_access(org_id, feature)
        
        return FeatureAccessResponse(
            feature=feature,
            has_access=has_access,
            current_bundle=current_bundle,
            required_bundle=required_bundle,
            upgrade_url=f"/dashboard/settings?tab=billing&upgrade_to={required_bundle}" if required_bundle else None,
        )
        
    except Exception as e:
        logger.error(f"Error checking feature access: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to check feature access")


# ============================================
# Bundle Endpoints
# ============================================

@router.get("/billing/bundles", response_model=List[BundleInfo])
async def list_bundles():
    """
    Get information about all available subscription bundles.
    """
    return [BundleInfo(**b) for b in get_all_bundles()]


@router.get("/billing/bundles/{bundle_id}", response_model=BundleInfo)
async def get_bundle(bundle_id: str):
    """
    Get information about a specific bundle.
    """
    info = get_bundle_info(bundle_id)
    if not info or info["id"] == bundle_id:
        return BundleInfo(**info)
    raise HTTPException(status_code=404, detail="Bundle not found")


# ============================================
# Subscription Management (Placeholder)
# ============================================

@router.post("/billing/upgrade")
async def upgrade_subscription(
    org_id: str = Query(..., description="Organization ID"),
    bundle: str = Query(..., description="Target bundle"),
):
    """
    Initiate subscription upgrade.
    
    NOTE: This is a placeholder. In production, this would redirect to Stripe Checkout.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    if bundle not in BUNDLE_FEATURES:
        raise HTTPException(status_code=400, detail=f"Invalid bundle: {bundle}")
    
    # DEV_ONLY: Directly upgrade for testing
    prisma = get_prisma()
    
    bundle_config = BUNDLE_FEATURES[bundle]
    
    await prisma.organizationsettings.upsert(
        where={"org_id": org_id},
        create={
            "org_id": org_id,
            "feature_bundle": bundle,
            "bundle_features": bundle_config,
            "max_meetings": bundle_config.get("max_meetings", 10),
            "max_minutes": bundle_config.get("max_minutes", 60),
            "trial_expires_at": None,  # Remove trial expiration on upgrade
        },
        update={
            "feature_bundle": bundle,
            "bundle_features": bundle_config,
            "max_meetings": bundle_config.get("max_meetings", 10),
            "max_minutes": bundle_config.get("max_minutes", 60),
            "trial_expires_at": None,
        }
    )
    
    logger.info(f"[Billing] DEV_ONLY: Upgraded org {org_id} to bundle {bundle}")
    
    return {
        "success": True,
        "org_id": org_id,
        "new_bundle": bundle,
        "message": f"DEV_ONLY: Upgraded to {bundle}. In production, this would redirect to Stripe.",
    }


@router.post("/billing/extend-trial")
async def extend_trial(
    org_id: str = Query(..., description="Organization ID"),
    days: int = Query(14, description="Days to extend"),
):
    """
    Extend trial period.
    
    NOTE: This is for admin use only. In production, requires admin auth.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    prisma = get_prisma()
    
    new_expiry = datetime.utcnow() + timedelta(days=days)
    
    await prisma.organizationsettings.upsert(
        where={"org_id": org_id},
        create={
            "org_id": org_id,
            "feature_bundle": "trial",
            "trial_expires_at": new_expiry,
        },
        update={
            "trial_expires_at": new_expiry,
        }
    )
    
    logger.info(f"[Billing] Extended trial for org {org_id} to {new_expiry}")
    
    return {
        "success": True,
        "org_id": org_id,
        "trial_expires_at": new_expiry.isoformat(),
        "days_added": days,
    }


@router.post("/billing/reset-usage")
async def reset_usage(
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Reset usage counters (for billing cycle reset).
    
    NOTE: This is for admin use only. In production, triggered by billing cycle.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    prisma = get_prisma()
    
    await prisma.organizationsettings.update(
        where={"org_id": org_id},
        data={
            "meetings_count": 0,
            "minutes_used": 0,
            "billing_cycle_start": datetime.utcnow(),
        }
    )
    
    logger.info(f"[Billing] Reset usage for org {org_id}")
    
    return {
        "success": True,
        "org_id": org_id,
        "message": "Usage counters reset",
    }
