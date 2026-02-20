"""
Client API - Client Directory and Timeline Endpoints

Provides REST endpoints for:
- Listing clients with search/filter
- Getting client details with meeting timeline
- Updating client information
- Linking clients to external CRM
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_prisma
from app.services.client_service import (
    get_all_clients,
    get_client_timeline,
    resolve_or_create_client,
    update_client_stats,
    normalize_phone,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class ClientCreate(BaseModel):
    """Request model for creating a client."""
    phone: str = Field(..., description="Phone number (will be normalized)")
    email: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ClientUpdate(BaseModel):
    """Request model for updating a client."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    external_crm_id: Optional[str] = None
    external_crm_type: Optional[str] = None
    relationship_stage: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ClientResponse(BaseModel):
    """Response model for a single client."""
    id: str
    phone: str
    email: Optional[str]
    full_name: Optional[str]
    company_name: Optional[str]
    total_meetings: int
    relationship_stage: str
    avg_sentiment_score: Optional[float]
    first_contact_at: Optional[str]
    last_contact_at: Optional[str]
    external_crm_id: Optional[str]
    external_crm_type: Optional[str]
    metadata: Optional[Dict[str, Any]]


class ClientListResponse(BaseModel):
    """Response model for client list."""
    clients: List[ClientResponse]
    total: int
    limit: int
    offset: int


class MeetingSummary(BaseModel):
    """Summary of a meeting for timeline."""
    id: str
    created_at: Optional[str]
    status: str
    duration_seconds: Optional[int]
    summary_text: Optional[str]
    confidence_score: Optional[float]
    deal_heat: Optional[str]


class SentimentPoint(BaseModel):
    """Sentiment data point for trend."""
    date: Optional[str]
    score: Optional[float]
    label: Optional[str]


class ClientTimelineResponse(BaseModel):
    """Response model for client timeline view."""
    client: ClientResponse
    meetings: List[MeetingSummary]
    sentiment_trend: List[SentimentPoint]


# ============================================
# Client CRUD Endpoints
# ============================================

@router.get("/clients", response_model=ClientListResponse)
async def list_clients(
    org_id: str = Query(..., description="Organization ID"),
    search: Optional[str] = Query(None, description="Search by name, phone, email"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List all clients for an organization with optional search.
    """
    # DEV_ONLY_WARNING: org_id should come from JWT in production
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        clients, total = await get_all_clients(
            org_id=org_id,
            search=search,
            limit=limit,
            offset=offset,
        )
        
        return ClientListResponse(
            clients=[ClientResponse(**c) for c in clients],
            total=total,
            limit=limit,
            offset=offset,
        )
        
    except Exception as e:
        logger.error(f"Error listing clients: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch clients")


@router.get("/clients/{client_id}", response_model=ClientTimelineResponse)
async def get_client(
    client_id: str,
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get client details with meeting timeline.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        result = await get_client_timeline(client_id=client_id, org_id=org_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return ClientTimelineResponse(
            client=ClientResponse(**result["client"]),
            meetings=[MeetingSummary(**m) for m in result["meetings"]],
            sentiment_trend=[SentimentPoint(**s) for s in result["sentiment_trend"]],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client {client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch client")


@router.post("/clients", response_model=ClientResponse)
async def create_client(
    client: ClientCreate,
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Create a new client or return existing if phone matches.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        client_id, is_new = await resolve_or_create_client(
            org_id=org_id,
            phone=client.phone,
            email=client.email,
            full_name=client.full_name,
            company_name=client.company_name,
            metadata=client.metadata,
        )
        
        # Fetch and return the client
        result = await get_client_timeline(client_id=client_id, org_id=org_id)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to fetch created client")
        
        return ClientResponse(**result["client"])
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating client: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create client")


@router.patch("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    update: ClientUpdate,
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Update client information.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        prisma = get_prisma()
        
        # Verify client exists and belongs to org
        existing = await prisma.client.find_first(
            where={"id": client_id, "org_id": org_id}
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Build update data (only non-None values)
        update_data: Dict[str, Any] = {}
        
        if update.email is not None:
            update_data["email"] = update.email
        if update.full_name is not None:
            update_data["full_name"] = update.full_name
        if update.company_name is not None:
            update_data["company_name"] = update.company_name
        if update.external_crm_id is not None:
            update_data["external_crm_id"] = update.external_crm_id
        if update.external_crm_type is not None:
            update_data["external_crm_type"] = update.external_crm_type
        if update.relationship_stage is not None:
            update_data["relationship_stage"] = update.relationship_stage
        if update.notes is not None:
            update_data["notes"] = update.notes
        if update.metadata is not None:
            update_data["metadata"] = update.metadata
        
        if update_data:
            await prisma.client.update(
                where={"id": client_id},
                data=update_data,
            )
        
        # Return updated client
        result = await get_client_timeline(client_id=client_id, org_id=org_id)
        return ClientResponse(**result["client"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client {client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update client")


@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: str,
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Soft-delete a client (set is_active = false).
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        prisma = get_prisma()
        
        # Verify client exists and belongs to org
        existing = await prisma.client.find_first(
            where={"id": client_id, "org_id": org_id}
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="Client not found")
        
        await prisma.client.update(
            where={"id": client_id},
            data={"is_active": False},
        )
        
        return {"message": "Client deleted", "client_id": client_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting client {client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete client")


# ============================================
# Client Analytics Endpoints
# ============================================

@router.get("/clients/stats/overview")
async def get_clients_overview(
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get overview statistics for all clients.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        prisma = get_prisma()
        
        # Count by relationship stage
        total = await prisma.client.count(where={"org_id": org_id, "is_active": True})
        
        stages = ["new", "engaged", "nurturing", "closing", "won", "lost"]
        stage_counts = {}
        
        for stage in stages:
            count = await prisma.client.count(
                where={"org_id": org_id, "is_active": True, "relationship_stage": stage}
            )
            stage_counts[stage] = count
        
        # Top clients by meetings
        top_clients = await prisma.client.find_many(
            where={"org_id": org_id, "is_active": True},
            order_by={"total_meetings": "desc"},
            take=5,
        )
        
        return {
            "total_clients": total,
            "by_stage": stage_counts,
            "top_clients": [
                {
                    "id": c.id,
                    "name": c.full_name or c.company_name or c.phone,
                    "total_meetings": c.total_meetings,
                    "relationship_stage": c.relationship_stage,
                }
                for c in top_clients
            ],
        }
        
    except Exception as e:
        logger.error(f"Error fetching client stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch client statistics")


@router.post("/clients/{client_id}/refresh-stats")
async def refresh_client_stats(
    client_id: str,
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Manually refresh client statistics from meetings.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        await update_client_stats(client_id=client_id, org_id=org_id)
        
        result = await get_client_timeline(client_id=client_id, org_id=org_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return ClientResponse(**result["client"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing client stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to refresh client statistics")
