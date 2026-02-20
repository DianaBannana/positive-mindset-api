"""
Users API - User profile and RBAC endpoints

Provides endpoints for:
- Current user context
- Role/permission checks
- User profile management
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_prisma
from app.core.rbac import (
    get_user_context,
    get_accessible_routes,
    Role,
    Permission,
    ROLE_PERMISSIONS,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Response Models
# ============================================

class UserContextResponse(BaseModel):
    """User context with role and permissions."""
    user_id: str
    org_id: str
    role: str
    permissions: List[str]
    name: str
    email: str
    avatar_url: Optional[str]
    team_id: Optional[str]
    reports_to: Optional[str]
    accessible_routes: List[Dict[str, str]]


class RoleInfo(BaseModel):
    """Role information with permissions."""
    role: str
    label: str
    permissions: List[str]


# ============================================
# User Context Endpoints
# ============================================

@router.get("/users/me", response_model=UserContextResponse)
async def get_current_user(
    org_id: str = Query(..., description="Organization ID"),
    user_id: str = Query(None, description="User ID (DEV: optional)"),
):
    """
    Get current user context with role and permissions.
    
    Returns the authenticated user's profile, role, permissions,
    and list of accessible routes.
    """
    # DEV_ONLY_WARNING: In production, user_id comes from JWT
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    prisma = get_prisma()
    
    try:
        # If no user_id, try to find first user in org (DEV mode)
        if not user_id:
            user = await prisma.user.find_first(
                where={"org_id": org_id}
            )
            if user:
                user_id = user.id
            else:
                # Create a dev user
                user = await prisma.user.create(
                    data={
                        "org_id": org_id,
                        "email": "dev@salesecho.ai",
                        "name": "Dev User",
                        "role": "manager",  # Default to manager for dev
                    }
                )
                user_id = user.id
        
        # Get user context
        context = await get_user_context(user_id, org_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get accessible routes
        routes = get_accessible_routes(context.role, context.permissions)
        
        # Get user avatar
        user = await prisma.user.find_unique(where={"id": user_id})
        
        return UserContextResponse(
            user_id=context.user_id,
            org_id=context.org_id,
            role=context.role.value,
            permissions=[p.value for p in context.permissions],
            name=context.name,
            email=context.email,
            avatar_url=user.avatar_url if user else None,
            team_id=context.team_id,
            reports_to=context.reports_to,
            accessible_routes=routes,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get user context")


@router.get("/users/roles", response_model=List[RoleInfo])
async def list_roles():
    """
    Get all available roles with their permissions.
    """
    roles = []
    
    role_labels = {
        Role.SALES_REP: "Sales Representative",
        Role.MANAGER: "Manager",
        Role.ADMIN: "Administrator",
    }
    
    for role in Role:
        permissions = ROLE_PERMISSIONS.get(role, set())
        roles.append(RoleInfo(
            role=role.value,
            label=role_labels.get(role, role.value),
            permissions=[p.value for p in permissions],
        ))
    
    return roles


@router.post("/users/me/role")
async def update_user_role(
    org_id: str = Query(...),
    user_id: str = Query(...),
    new_role: str = Query(..., description="New role: sales_rep, manager, admin"),
):
    """
    Update user role.
    
    DEV_ONLY: In production, this requires admin permissions.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    # Validate role
    try:
        role = Role(new_role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {new_role}")
    
    prisma = get_prisma()
    
    try:
        user = await prisma.user.update(
            where={"id": user_id},
            data={"role": role.value}
        )
        
        return {
            "success": True,
            "user_id": user.id,
            "new_role": role.value,
        }
        
    except Exception as e:
        logger.error(f"Error updating user role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update role")


# ============================================
# Team Endpoints (Manager view)
# ============================================

@router.get("/users/team")
async def get_team_members(
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get all team members for organization (Manager+ only).
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    prisma = get_prisma()
    
    try:
        users = await prisma.user.find_many(
            where={"org_id": org_id},
            order_by={"name": "asc"},
        )
        
        # Get meeting counts per user
        result = []
        for user in users:
            meeting_count = await prisma.meeting.count(
                where={"user_id": user.id, "org_id": org_id}
            )
            
            result.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "avatar_url": user.avatar_url,
                "meeting_count": meeting_count,
                "last_active": user.last_active_at.isoformat() if user.last_active_at else None,
                "created_at": user.created_at.isoformat(),
            })
        
        return {
            "team": result,
            "total": len(result),
        }
        
    except Exception as e:
        logger.error(f"Error getting team: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get team")


@router.get("/users/team/stats")
async def get_team_stats(
    org_id: str = Query(..., description="Organization ID"),
    days: int = Query(30, description="Number of days to analyze"),
):
    """
    Get team performance statistics (Manager+ only).
    
    Returns activity volume, performance metrics per rep.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    prisma = get_prisma()
    
    from datetime import datetime, timedelta
    start_date = datetime.utcnow() - timedelta(days=days)
    
    try:
        # Get users
        users = await prisma.user.find_many(
            where={"org_id": org_id}
        )
        
        team_stats = []
        
        for user in users:
            # Get meetings for this user
            meetings = await prisma.meeting.find_many(
                where={
                    "user_id": user.id,
                    "org_id": org_id,
                    "created_at": {"gte": start_date},
                    "status": "COMPLETED",
                }
            )
            
            total_meetings = len(meetings)
            total_minutes = sum(m.duration_seconds or 0 for m in meetings) / 60
            
            # Calculate average sentiment
            sentiments = []
            total_pipeline = 0.0
            hot_deals = 0
            
            for meeting in meetings:
                if meeting.summary and isinstance(meeting.summary, dict):
                    content = meeting.summary.get("content", {})
                    if isinstance(content, dict):
                        # Sentiment
                        sentiment = content.get("overall_sentiment", {})
                        if isinstance(sentiment, dict) and sentiment.get("score"):
                            sentiments.append(sentiment["score"])
                        
                        # Pipeline value
                        crm = content.get("crm_entities", {})
                        if isinstance(crm, dict):
                            deal = crm.get("deal_value", {})
                            if isinstance(deal, dict) and deal.get("value"):
                                total_pipeline += deal["value"]
                        
                        # Hot deals
                        deal_heat = content.get("deal_heat")
                        if deal_heat == "hot":
                            hot_deals += 1
            
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None
            
            team_stats.append({
                "user_id": user.id,
                "name": user.name,
                "role": user.role,
                "metrics": {
                    "total_meetings": total_meetings,
                    "total_minutes": round(total_minutes, 1),
                    "avg_sentiment": round(avg_sentiment, 2) if avg_sentiment else None,
                    "pipeline_value": total_pipeline,
                    "hot_deals": hot_deals,
                }
            })
        
        # Sort by meeting count
        team_stats.sort(key=lambda x: x["metrics"]["total_meetings"], reverse=True)
        
        return {
            "period_days": days,
            "team_stats": team_stats,
        }
        
    except Exception as e:
        logger.error(f"Error getting team stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get team stats")
