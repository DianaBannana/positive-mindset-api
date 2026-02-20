"""
Role-Based Access Control (RBAC) System

Defines roles, permissions, and access control logic for SalesEcho AI.

Roles:
- SALES_REP: Access to own meetings, clients, action center
- MANAGER: Access to team analytics, all meetings in org, settings
- ADMIN: Full access including billing, integrations, user management
"""

import logging
from enum import Enum
from typing import List, Optional, Set, Dict, Any
from dataclasses import dataclass
from functools import wraps

from fastapi import HTTPException

from app.core.database import get_prisma

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """User roles with hierarchical access."""
    SALES_REP = "sales_rep"
    MANAGER = "manager"
    ADMIN = "admin"


class Permission(str, Enum):
    """Granular permissions for fine-tuned access control."""
    # Meeting permissions
    VIEW_OWN_MEETINGS = "view_own_meetings"
    VIEW_TEAM_MEETINGS = "view_team_meetings"
    VIEW_ALL_MEETINGS = "view_all_meetings"
    EDIT_MEETINGS = "edit_meetings"
    DELETE_MEETINGS = "delete_meetings"
    
    # Client permissions
    VIEW_CLIENTS = "view_clients"
    EDIT_CLIENTS = "edit_clients"
    DELETE_CLIENTS = "delete_clients"
    
    # Analytics permissions
    VIEW_OWN_ANALYTICS = "view_own_analytics"
    VIEW_TEAM_ANALYTICS = "view_team_analytics"
    VIEW_ORG_ANALYTICS = "view_org_analytics"
    EXPORT_ANALYTICS = "export_analytics"
    
    # Action Center permissions
    SEND_EMAILS = "send_emails"
    SEND_WHATSAPP = "send_whatsapp"
    SYNC_CRM = "sync_crm"
    APPROVE_ACTIONS = "approve_actions"
    
    # Settings permissions
    VIEW_SETTINGS = "view_settings"
    EDIT_SETTINGS = "edit_settings"
    MANAGE_USERS = "manage_users"
    MANAGE_INTEGRATIONS = "manage_integrations"
    MANAGE_BILLING = "manage_billing"
    
    # API & Webhook permissions
    MANAGE_API_KEYS = "manage_api_keys"
    VIEW_AUDIT_LOGS = "view_audit_logs"


# Role → Default Permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SALES_REP: {
        Permission.VIEW_OWN_MEETINGS,
        Permission.VIEW_CLIENTS,
        Permission.VIEW_OWN_ANALYTICS,
        Permission.SEND_EMAILS,
        Permission.SEND_WHATSAPP,
        Permission.SYNC_CRM,
    },
    Role.MANAGER: {
        # All sales rep permissions
        Permission.VIEW_OWN_MEETINGS,
        Permission.VIEW_TEAM_MEETINGS,
        Permission.VIEW_CLIENTS,
        Permission.EDIT_CLIENTS,
        Permission.VIEW_OWN_ANALYTICS,
        Permission.VIEW_TEAM_ANALYTICS,
        Permission.VIEW_ORG_ANALYTICS,
        Permission.EXPORT_ANALYTICS,
        Permission.SEND_EMAILS,
        Permission.SEND_WHATSAPP,
        Permission.SYNC_CRM,
        Permission.APPROVE_ACTIONS,
        Permission.VIEW_SETTINGS,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOGS,
    },
    Role.ADMIN: {
        # All permissions
        *Permission,
    },
}


@dataclass
class UserContext:
    """Current user context with role and permissions."""
    user_id: str
    org_id: str
    role: Role
    permissions: Set[Permission]
    name: str
    email: str
    team_id: Optional[str] = None
    reports_to: Optional[str] = None
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(p in self.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions."""
        return all(p in self.permissions for p in permissions)
    
    def can_view_meeting(self, meeting_user_id: str) -> bool:
        """Check if user can view a specific meeting."""
        if Permission.VIEW_ALL_MEETINGS in self.permissions:
            return True
        if Permission.VIEW_TEAM_MEETINGS in self.permissions:
            # TODO: Check if meeting user is in same team
            return True
        if Permission.VIEW_OWN_MEETINGS in self.permissions:
            return meeting_user_id == self.user_id
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "user_id": self.user_id,
            "org_id": self.org_id,
            "role": self.role.value,
            "permissions": [p.value for p in self.permissions],
            "name": self.name,
            "email": self.email,
            "team_id": self.team_id,
            "reports_to": self.reports_to,
        }


async def get_user_context(user_id: str, org_id: str) -> Optional[UserContext]:
    """
    Build user context from database.
    
    Args:
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        UserContext object or None if user not found
    """
    prisma = get_prisma()
    
    user = await prisma.user.find_first(
        where={
            "id": user_id,
            "org_id": org_id,
        }
    )
    
    if not user:
        return None
    
    # Parse role
    try:
        role = Role(user.role)
    except ValueError:
        role = Role.SALES_REP
    
    # Get default permissions for role
    permissions = ROLE_PERMISSIONS.get(role, set()).copy()
    
    # Add any custom permissions from database
    if user.permissions and isinstance(user.permissions, list):
        for perm_str in user.permissions:
            try:
                permissions.add(Permission(perm_str))
            except ValueError:
                pass
    
    return UserContext(
        user_id=user.id,
        org_id=user.org_id,
        role=role,
        permissions=permissions,
        name=user.name,
        email=user.email,
        team_id=user.team_id,
        reports_to=user.reports_to,
    )


def require_permission(*required_permissions: Permission):
    """
    Decorator for FastAPI endpoints to require specific permissions.
    
    Usage:
    @router.get("/meetings")
    @require_permission(Permission.VIEW_OWN_MEETINGS)
    async def get_meetings(user_context: UserContext = Depends(get_current_user)):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user context from kwargs
            user_context = kwargs.get("user_context")
            
            if not user_context:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not user_context.has_all_permissions(list(required_permissions)):
                missing = [p.value for p in required_permissions if p not in user_context.permissions]
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "permission_denied",
                        "required": [p.value for p in required_permissions],
                        "missing": missing,
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*required_roles: Role):
    """
    Decorator for FastAPI endpoints to require specific roles.
    
    Usage:
    @router.get("/settings")
    @require_role(Role.MANAGER, Role.ADMIN)
    async def get_settings(user_context: UserContext = Depends(get_current_user)):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_context = kwargs.get("user_context")
            
            if not user_context:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if user_context.role not in required_roles:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "role_required",
                        "required_roles": [r.value for r in required_roles],
                        "current_role": user_context.role.value,
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Route definitions for frontend navigation
ROUTE_ACCESS: Dict[str, Dict[str, Any]] = {
    "/dashboard": {
        "roles": [Role.SALES_REP, Role.MANAGER, Role.ADMIN],
        "label": "Dashboard",
    },
    "/dashboard/meetings": {
        "roles": [Role.SALES_REP, Role.MANAGER, Role.ADMIN],
        "label": "Meetings",
    },
    "/dashboard/clients": {
        "roles": [Role.SALES_REP, Role.MANAGER, Role.ADMIN],
        "label": "Clients",
    },
    "/dashboard/analytics": {
        "roles": [Role.MANAGER, Role.ADMIN],
        "label": "Analytics",
        "permission": Permission.VIEW_ORG_ANALYTICS,
    },
    "/dashboard/team": {
        "roles": [Role.MANAGER, Role.ADMIN],
        "label": "Team Overview",
        "permission": Permission.VIEW_TEAM_ANALYTICS,
    },
    "/dashboard/settings": {
        "roles": [Role.MANAGER, Role.ADMIN],
        "label": "Settings",
        "permission": Permission.VIEW_SETTINGS,
    },
}


def get_accessible_routes(role: Role, permissions: Set[Permission]) -> List[Dict[str, Any]]:
    """Get list of routes accessible to a user based on role and permissions."""
    accessible = []
    
    for path, config in ROUTE_ACCESS.items():
        if role in config["roles"]:
            # Check additional permission if required
            if "permission" in config:
                if config["permission"] not in permissions:
                    continue
            accessible.append({
                "path": path,
                "label": config["label"],
            })
    
    return accessible
