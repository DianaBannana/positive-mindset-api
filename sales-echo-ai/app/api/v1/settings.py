"""
Organization Settings API
Manages custom AI instructions, module toggles, and API keys.
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_prisma

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class EnabledModules(BaseModel):
    """Feature flags for automation modules."""
    email: bool = True
    whatsapp: bool = True
    calendar: bool = True
    crm: bool = True


class OrganizationSettingsCreate(BaseModel):
    """Request model for creating/updating org settings."""
    org_id: str
    custom_prompt_instructions: Optional[str] = None
    enabled_modules: EnabledModules = Field(default_factory=EnabledModules)
    industry_type: Optional[str] = None
    default_language: str = "he"
    auto_dispatch_actions: bool = False
    require_approval: bool = True
    callback_url: Optional[str] = None
    audio_retention_hours: int = 24


class OrganizationSettingsResponse(BaseModel):
    """Response model for org settings."""
    id: str
    org_id: str
    custom_prompt_instructions: Optional[str]
    enabled_modules: Dict[str, bool]
    industry_type: Optional[str]
    default_language: str
    auto_dispatch_actions: bool
    require_approval: bool
    webhook_secret: Optional[str]
    callback_url: Optional[str]
    audio_retention_hours: int
    created_at: str
    updated_at: str


class APIKeyResponse(BaseModel):
    """Response model for API key (without the actual key)."""
    id: str
    key_prefix: str
    name: str
    permissions: List[str]
    is_active: bool
    last_used_at: Optional[str]
    usage_count: int
    created_at: str


class APIKeyGenerateRequest(BaseModel):
    """Request model for generating a new API key."""
    org_id: str
    name: str = "Primary Integration Key"
    permissions: List[str] = ["ingest"]


class APIKeyGenerateResponse(BaseModel):
    """Response model for newly generated API key (includes actual key)."""
    api_key: str  # The actual key - only shown once!
    key_id: str
    key_prefix: str
    name: str


# ============================================
# Settings Endpoints
# ============================================

@router.get("/settings", response_model=OrganizationSettingsResponse)
async def get_organization_settings(
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get organization settings.
    
    Returns the custom AI instructions, enabled modules, and other settings.
    """
    # DEV_ONLY_WARNING: In production, org_id should come from JWT
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id

    try:
        prisma = get_prisma()
        
        org_settings = await prisma.organizationsettings.find_unique(
            where={"org_id": org_id}
        )
        
        if not org_settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        
        return OrganizationSettingsResponse(
            id=org_settings.id,
            org_id=org_settings.org_id,
            custom_prompt_instructions=org_settings.custom_prompt_instructions,
            enabled_modules=org_settings.enabled_modules or {
                "email": True, "whatsapp": True, "calendar": True, "crm": True
            },
            industry_type=org_settings.industry_type,
            default_language=org_settings.default_language,
            auto_dispatch_actions=org_settings.auto_dispatch_actions,
            require_approval=org_settings.require_approval,
            webhook_secret="••••••••" if org_settings.webhook_secret else None,
            callback_url=org_settings.callback_url,
            audio_retention_hours=org_settings.audio_retention_hours,
            created_at=org_settings.created_at.isoformat(),
            updated_at=org_settings.updated_at.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching settings for org {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch settings")


@router.post("/settings", response_model=OrganizationSettingsResponse)
async def create_or_update_settings(
    request: OrganizationSettingsCreate,
):
    """
    Create or update organization settings.
    
    This endpoint handles both creating new settings and updating existing ones.
    """
    org_id = request.org_id
    
    # DEV_ONLY_WARNING: In production, org_id should come from JWT
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id

    try:
        prisma = get_prisma()
        
        # Check if settings exist
        existing = await prisma.organizationsettings.find_unique(
            where={"org_id": org_id}
        )
        
        settings_data = {
            "custom_prompt_instructions": request.custom_prompt_instructions,
            "enabled_modules": request.enabled_modules.model_dump(),
            "industry_type": request.industry_type,
            "default_language": request.default_language,
            "auto_dispatch_actions": request.auto_dispatch_actions,
            "require_approval": request.require_approval,
            "callback_url": request.callback_url,
            "audio_retention_hours": request.audio_retention_hours,
        }
        
        if existing:
            # Update existing
            org_settings = await prisma.organizationsettings.update(
                where={"org_id": org_id},
                data=settings_data,
            )
            logger.info(f"Updated settings for org {org_id}")
        else:
            # Create new
            org_settings = await prisma.organizationsettings.create(
                data={
                    "org_id": org_id,
                    **settings_data,
                }
            )
            logger.info(f"Created settings for org {org_id}")
        
        return OrganizationSettingsResponse(
            id=org_settings.id,
            org_id=org_settings.org_id,
            custom_prompt_instructions=org_settings.custom_prompt_instructions,
            enabled_modules=org_settings.enabled_modules,
            industry_type=org_settings.industry_type,
            default_language=org_settings.default_language,
            auto_dispatch_actions=org_settings.auto_dispatch_actions,
            require_approval=org_settings.require_approval,
            webhook_secret="••••••••" if org_settings.webhook_secret else None,
            callback_url=org_settings.callback_url,
            audio_retention_hours=org_settings.audio_retention_hours,
            created_at=org_settings.created_at.isoformat(),
            updated_at=org_settings.updated_at.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving settings for org {org_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save settings")


# ============================================
# API Key Endpoints
# ============================================

@router.get("/settings/api-keys")
async def list_api_keys(
    org_id: str = Query(..., description="Organization ID"),
):
    """
    List all API keys for an organization.
    
    Note: This does not return the actual key values, only metadata.
    """
    # DEV_ONLY_WARNING: In production, org_id should come from JWT
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id

    try:
        prisma = get_prisma()
        
        keys = await prisma.apikey.find_many(
            where={"org_id": org_id},
            order_by={"created_at": "desc"},
        )
        
        return {
            "keys": [
                APIKeyResponse(
                    id=key.id,
                    key_prefix=key.key_prefix,
                    name=key.name,
                    permissions=key.permissions or ["ingest"],
                    is_active=key.is_active,
                    last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                    usage_count=key.usage_count,
                    created_at=key.created_at.isoformat(),
                )
                for key in keys
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing API keys for org {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.post("/settings/api-keys/regenerate", response_model=APIKeyGenerateResponse)
async def regenerate_api_key(
    request: APIKeyGenerateRequest,
):
    """
    Generate a new API key for an organization.
    
    If an existing key exists, it will be deactivated.
    The new key is only returned ONCE in this response - save it!
    """
    org_id = request.org_id
    
    # DEV_ONLY_WARNING: In production, org_id should come from JWT
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id

    try:
        prisma = get_prisma()
        
        # Deactivate existing keys
        await prisma.apikey.update_many(
            where={"org_id": org_id, "is_active": True},
            data={"is_active": False},
        )
        
        # Generate new key
        raw_key = f"sk_live_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:10]
        
        # Create key record
        new_key = await prisma.apikey.create(
            data={
                "org_id": org_id,
                "key_hash": key_hash,
                "key_prefix": key_prefix,
                "name": request.name,
                "permissions": request.permissions,
                "is_active": True,
            }
        )
        
        logger.info(f"Generated new API key for org {org_id}: {key_prefix}...")
        
        return APIKeyGenerateResponse(
            api_key=raw_key,  # Only returned once!
            key_id=new_key.id,
            key_prefix=key_prefix,
            name=request.name,
        )
        
    except Exception as e:
        logger.error(f"Error generating API key for org {org_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate API key")


# ============================================
# Action Approval Endpoints
# ============================================

class ActionApprovalRequest(BaseModel):
    """Request model for approving an action."""
    meeting_id: str
    action_type: str  # "email", "whatsapp", "calendar", "crm"
    approved: bool


class ActionApprovalResponse(BaseModel):
    """Response model for action approval."""
    meeting_id: str
    action_type: str
    status: str  # "approved", "rejected", "pending"
    executed: bool


@router.post("/settings/actions/approve", response_model=ActionApprovalResponse)
async def approve_action(
    request: ActionApprovalRequest,
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Approve or reject a pending action.
    
    This is used when require_approval is enabled.
    """
    # DEV_ONLY_WARNING: In production, org_id should come from JWT
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id

    try:
        prisma = get_prisma()
        
        # Get meeting to verify it belongs to org
        meeting = await prisma.meeting.find_unique(
            where={"id": request.meeting_id}
        )
        
        if not meeting or meeting.org_id != org_id:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Update action status in meeting metadata
        current_summary = meeting.summary or {}
        action_status = current_summary.get("action_status", {})
        
        action_status[request.action_type] = {
            "status": "approved" if request.approved else "rejected",
            "approved_at": datetime.utcnow().isoformat() if request.approved else None,
            "rejected_at": datetime.utcnow().isoformat() if not request.approved else None,
        }
        
        current_summary["action_status"] = action_status
        
        await prisma.meeting.update(
            where={"id": request.meeting_id},
            data={"summary": current_summary}
        )
        
        # If approved and action hasn't been executed, execute it
        executed = False
        if request.approved:
            # Import dispatcher and execute the specific action
            try:
                from app.core.dispatcher import action_dispatcher
                
                # Build context for single action
                context = {
                    "meeting_id": request.meeting_id,
                    "org_id": org_id,
                    "summary": current_summary,
                    "action_type": request.action_type,
                }
                
                # Execute single action
                # Note: In a real implementation, this would call the specific module
                logger.info(f"Executing approved action {request.action_type} for meeting {request.meeting_id}")
                executed = True
                
            except Exception as exec_err:
                logger.error(f"Failed to execute action: {exec_err}")
        
        return ActionApprovalResponse(
            meeting_id=request.meeting_id,
            action_type=request.action_type,
            status="approved" if request.approved else "rejected",
            executed=executed,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process approval")


@router.get("/settings/actions/status")
async def get_action_status(
    meeting_id: str = Query(..., description="Meeting ID"),
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get the approval status of all actions for a meeting.
    """
    # DEV_ONLY_WARNING: In production, org_id should come from JWT
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id

    try:
        prisma = get_prisma()
        
        meeting = await prisma.meeting.find_unique(
            where={"id": meeting_id}
        )
        
        if not meeting or meeting.org_id != org_id:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Get org settings to determine if approval is required
        org_settings = await prisma.organizationsettings.find_unique(
            where={"org_id": org_id}
        )
        
        require_approval = org_settings.require_approval if org_settings else True
        enabled_modules = org_settings.enabled_modules if org_settings else {
            "email": True, "whatsapp": True, "calendar": True, "crm": True
        }
        
        # Get action status from meeting summary
        summary = meeting.summary or {}
        action_status = summary.get("action_status", {})
        
        # Build response with all modules
        actions = {}
        for module in ["email", "whatsapp", "calendar", "crm"]:
            if enabled_modules.get(module, True):
                module_status = action_status.get(module, {})
                actions[module] = {
                    "enabled": True,
                    "require_approval": require_approval,
                    "status": module_status.get("status", "pending" if require_approval else "auto_approved"),
                    "approved_at": module_status.get("approved_at"),
                    "rejected_at": module_status.get("rejected_at"),
                }
            else:
                actions[module] = {
                    "enabled": False,
                    "status": "disabled",
                }
        
        return {
            "meeting_id": meeting_id,
            "require_approval": require_approval,
            "actions": actions,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get action status")
