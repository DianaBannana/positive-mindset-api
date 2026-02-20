"""
Client Service - Client Identity Resolution and Historical Context

This module provides:
- Phone number normalization
- Client lookup/creation based on phone
- Historical meeting context for AI injection
- Client relationship statistics
"""

import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from app.core.database import get_prisma

logger = logging.getLogger(__name__)


@dataclass
class ClientContext:
    """Historical context for AI injection."""
    client_id: str
    client_name: Optional[str]
    total_meetings: int
    relationship_stage: str
    avg_sentiment: Optional[float]
    recent_summaries: List[Dict[str, Any]]  # Last 3 meeting summaries
    key_topics: List[str]  # Extracted from historical data
    last_action_items: List[Dict[str, Any]]  # Pending items from last meeting
    
    def to_prompt_block(self) -> str:
        """Generate the === CLIENT HISTORY === block for AI prompt."""
        lines = [
            "=== CLIENT HISTORY ===",
            f"Client: {self.client_name or 'Unknown'}",
            f"Total Previous Meetings: {self.total_meetings}",
            f"Relationship Stage: {self.relationship_stage}",
        ]
        
        if self.avg_sentiment is not None:
            sentiment_label = (
                "Positive" if self.avg_sentiment > 0.3 else
                "Negative" if self.avg_sentiment < -0.3 else
                "Neutral"
            )
            lines.append(f"Overall Sentiment: {sentiment_label} ({self.avg_sentiment:.2f})")
        
        if self.recent_summaries:
            lines.append("")
            lines.append("--- Recent Meeting Summaries ---")
            for i, summary in enumerate(self.recent_summaries, 1):
                date = summary.get("date", "Unknown date")
                text = summary.get("summary_text", "No summary available")
                # Truncate long summaries
                if len(text) > 500:
                    text = text[:500] + "..."
                lines.append(f"Meeting {i} ({date}):")
                lines.append(text)
                lines.append("")
        
        if self.last_action_items:
            lines.append("--- Pending Action Items from Last Meeting ---")
            for item in self.last_action_items[:5]:  # Max 5 items
                task = item.get("task", "")
                due = item.get("due", "")
                assignee = item.get("assignee", "")
                lines.append(f"• {task}" + (f" (Due: {due})" if due else "") + (f" [{assignee}]" if assignee else ""))
        
        if self.key_topics:
            lines.append("")
            lines.append(f"Key Topics Discussed: {', '.join(self.key_topics[:10])}")
        
        lines.append("=== END CLIENT HISTORY ===")
        return "\n".join(lines)


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to a standard format.
    
    Examples:
    - "050-1234567" -> "+972501234567"
    - "+972-50-123-4567" -> "+972501234567"
    - "0501234567" -> "+972501234567"
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Handle Israeli numbers
    if cleaned.startswith('0') and len(cleaned) == 10:
        # Convert local Israeli to international
        cleaned = '+972' + cleaned[1:]
    elif cleaned.startswith('972') and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    elif not cleaned.startswith('+') and len(cleaned) >= 10:
        # Assume Israeli if 10 digits starting with 5
        if cleaned.startswith('5') and len(cleaned) == 9:
            cleaned = '+972' + cleaned
    
    return cleaned


async def resolve_or_create_client(
    org_id: str,
    phone: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    company_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[str, bool]:
    """
    Resolve an existing client or create a new one based on phone number.
    
    Args:
        org_id: Organization ID
        phone: Client phone number (will be normalized)
        email: Optional email address
        full_name: Optional client name
        company_name: Optional company name
        metadata: Optional metadata dict
        
    Returns:
        Tuple of (client_id, is_new_client)
    """
    prisma = get_prisma()
    normalized_phone = normalize_phone(phone)
    
    if not normalized_phone:
        raise ValueError("Invalid phone number provided")
    
    # Try to find existing client
    existing = await prisma.client.find_first(
        where={
            "org_id": org_id,
            "phone": normalized_phone,
        }
    )
    
    if existing:
        # Update with any new information
        update_data: Dict[str, Any] = {"last_contact_at": datetime.utcnow()}
        
        if email and not existing.email:
            update_data["email"] = email
        if full_name and not existing.full_name:
            update_data["full_name"] = full_name
        if company_name and not existing.company_name:
            update_data["company_name"] = company_name
        
        await prisma.client.update(
            where={"id": existing.id},
            data=update_data,
        )
        
        logger.info(f"Resolved existing client: {existing.id} for phone {normalized_phone}")
        return existing.id, False
    
    # Create new client
    new_client = await prisma.client.create(
        data={
            "org_id": org_id,
            "phone": normalized_phone,
            "email": email,
            "full_name": full_name,
            "company_name": company_name,
            "metadata": metadata or {},
            "first_contact_at": datetime.utcnow(),
            "last_contact_at": datetime.utcnow(),
            "total_meetings": 0,
            "relationship_stage": "new",
        }
    )
    
    logger.info(f"Created new client: {new_client.id} for phone {normalized_phone}")
    return new_client.id, True


async def get_client_history(
    client_id: str,
    org_id: str,
    max_meetings: int = 3,
) -> Optional[ClientContext]:
    """
    Fetch historical context for a client (optimized - no full transcripts).
    
    Args:
        client_id: Client ID
        org_id: Organization ID (for security)
        max_meetings: Maximum number of recent meetings to include
        
    Returns:
        ClientContext object or None if client not found
    """
    prisma = get_prisma()
    
    # Fetch client with recent meetings (summary only, no transcript)
    client = await prisma.client.find_first(
        where={
            "id": client_id,
            "org_id": org_id,
        },
    )
    
    if not client:
        return None
    
    # Fetch recent completed meetings (summary only)
    recent_meetings = await prisma.meeting.find_many(
        where={
            "client_id": client_id,
            "org_id": org_id,
            "status": "COMPLETED",
        },
        order_by={"created_at": "desc"},
        take=max_meetings,
    )
    
    # Build recent summaries list
    recent_summaries = []
    last_action_items = []
    key_topics_set: set = set()
    
    for meeting in recent_meetings:
        summary_text = meeting.summary_text or ""
        summary_data = meeting.summary or {}
        
        # Get date
        meeting_date = meeting.created_at.strftime("%Y-%m-%d") if meeting.created_at else "Unknown"
        
        recent_summaries.append({
            "date": meeting_date,
            "summary_text": summary_text,
            "duration_seconds": meeting.duration_seconds,
        })
        
        # Extract action items from most recent meeting
        if not last_action_items and isinstance(summary_data, dict):
            content = summary_data.get("content", {})
            if isinstance(content, dict):
                items = content.get("action_items", [])
                if isinstance(items, list):
                    last_action_items = items[:5]
        
        # Extract key topics (from objections, key points, etc.)
        if isinstance(summary_data, dict):
            content = summary_data.get("content", {})
            if isinstance(content, dict):
                # Key points
                key_points = content.get("key_points", [])
                for kp in key_points[:3]:
                    if isinstance(kp, dict) and "point" in kp:
                        # Extract first few words as topic
                        topic = " ".join(kp["point"].split()[:5])
                        key_topics_set.add(topic)
                    elif isinstance(kp, str):
                        key_topics_set.add(" ".join(kp.split()[:5]))
                
                # Objections
                objections = content.get("objections_detected", [])
                for obj in objections[:3]:
                    if isinstance(obj, dict) and "objection" in obj:
                        key_topics_set.add(f"Objection: {obj['objection'][:50]}")
    
    return ClientContext(
        client_id=client.id,
        client_name=client.full_name or client.company_name,
        total_meetings=client.total_meetings,
        relationship_stage=client.relationship_stage,
        avg_sentiment=client.avg_sentiment_score,
        recent_summaries=recent_summaries,
        key_topics=list(key_topics_set)[:10],
        last_action_items=last_action_items,
    )


async def update_client_stats(client_id: str, org_id: str) -> None:
    """
    Update client statistics after a meeting is processed.
    
    This aggregates:
    - Total meetings count
    - Total talk time
    - Average sentiment score
    - Relationship stage (based on patterns)
    """
    prisma = get_prisma()
    
    # Get all completed meetings for this client
    meetings = await prisma.meeting.find_many(
        where={
            "client_id": client_id,
            "org_id": org_id,
            "status": "COMPLETED",
        },
        order_by={"created_at": "desc"},
    )
    
    if not meetings:
        return
    
    total_meetings = len(meetings)
    total_duration = sum(m.duration_seconds or 0 for m in meetings)
    
    # Calculate average sentiment from summaries
    sentiments = []
    for meeting in meetings:
        if meeting.summary and isinstance(meeting.summary, dict):
            content = meeting.summary.get("content", {})
            if isinstance(content, dict):
                sentiment = content.get("overall_sentiment")
                if isinstance(sentiment, dict):
                    score = sentiment.get("score")
                    if score is not None:
                        sentiments.append(score)
    
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None
    
    # Determine relationship stage based on patterns
    stage = determine_relationship_stage(
        total_meetings=total_meetings,
        avg_sentiment=avg_sentiment,
        last_meeting=meetings[0] if meetings else None,
    )
    
    # Update client
    await prisma.client.update(
        where={"id": client_id},
        data={
            "total_meetings": total_meetings,
            "total_talk_minutes": total_duration / 60.0,
            "avg_sentiment_score": avg_sentiment,
            "relationship_stage": stage,
            "last_contact_at": meetings[0].created_at if meetings else None,
        }
    )
    
    logger.info(f"Updated client {client_id} stats: {total_meetings} meetings, stage={stage}")


def determine_relationship_stage(
    total_meetings: int,
    avg_sentiment: Optional[float],
    last_meeting: Optional[Any],
) -> str:
    """
    Determine relationship stage based on meeting patterns.
    
    Stages:
    - new: 1 meeting
    - engaged: 2-3 meetings with positive sentiment
    - nurturing: 4+ meetings, ongoing discussions
    - closing: Deal heat is hot, action items include proposals
    - won: Deal closed (from CRM sync)
    - lost: Negative sentiment trend, no recent contact
    """
    if total_meetings <= 1:
        return "new"
    
    if total_meetings <= 3:
        if avg_sentiment and avg_sentiment > 0.2:
            return "engaged"
        return "new"
    
    # Check for deal indicators in last meeting
    if last_meeting and last_meeting.summary:
        summary = last_meeting.summary
        if isinstance(summary, dict):
            content = summary.get("content", {})
            if isinstance(content, dict):
                deal_heat = content.get("deal_heat")
                if deal_heat == "hot":
                    return "closing"
    
    # Check sentiment for lost opportunities
    if avg_sentiment and avg_sentiment < -0.3 and total_meetings >= 3:
        return "lost"
    
    return "nurturing"


async def get_all_clients(
    org_id: str,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get all clients for an organization with optional search.
    
    Returns:
        Tuple of (clients list, total count)
    """
    prisma = get_prisma()
    
    where_clause: Dict[str, Any] = {"org_id": org_id, "is_active": True}
    
    if search:
        # Search by name, phone, email, or company
        where_clause["OR"] = [
            {"full_name": {"contains": search, "mode": "insensitive"}},
            {"phone": {"contains": search}},
            {"email": {"contains": search, "mode": "insensitive"}},
            {"company_name": {"contains": search, "mode": "insensitive"}},
        ]
    
    # Get total count
    total = await prisma.client.count(where=where_clause)
    
    # Get clients
    clients = await prisma.client.find_many(
        where=where_clause,
        order_by={"last_contact_at": "desc"},
        skip=offset,
        take=limit,
    )
    
    return [
        {
            "id": c.id,
            "phone": c.phone,
            "email": c.email,
            "full_name": c.full_name,
            "company_name": c.company_name,
            "total_meetings": c.total_meetings,
            "relationship_stage": c.relationship_stage,
            "avg_sentiment_score": c.avg_sentiment_score,
            "first_contact_at": c.first_contact_at.isoformat() if c.first_contact_at else None,
            "last_contact_at": c.last_contact_at.isoformat() if c.last_contact_at else None,
            "external_crm_id": c.external_crm_id,
            "external_crm_type": c.external_crm_type,
            "metadata": c.metadata,
        }
        for c in clients
    ], total


async def get_client_timeline(
    client_id: str,
    org_id: str,
    limit: int = 20,
) -> Optional[Dict[str, Any]]:
    """
    Get client details with meeting timeline.
    
    Returns full client info plus all meetings in chronological order.
    """
    prisma = get_prisma()
    
    client = await prisma.client.find_first(
        where={
            "id": client_id,
            "org_id": org_id,
        },
    )
    
    if not client:
        return None
    
    # Get all meetings for timeline
    meetings = await prisma.meeting.find_many(
        where={
            "client_id": client_id,
            "org_id": org_id,
        },
        order_by={"created_at": "desc"},
        take=limit,
    )
    
    # Build sentiment trend
    sentiment_trend = []
    for meeting in reversed(meetings):  # Chronological order
        if meeting.summary and isinstance(meeting.summary, dict):
            content = meeting.summary.get("content", {})
            if isinstance(content, dict):
                sentiment = content.get("overall_sentiment", {})
                if isinstance(sentiment, dict):
                    sentiment_trend.append({
                        "date": meeting.created_at.strftime("%Y-%m-%d") if meeting.created_at else None,
                        "score": sentiment.get("score"),
                        "label": sentiment.get("label"),
                    })
    
    return {
        "client": {
            "id": client.id,
            "phone": client.phone,
            "email": client.email,
            "full_name": client.full_name,
            "company_name": client.company_name,
            "total_meetings": client.total_meetings,
            "total_talk_minutes": client.total_talk_minutes,
            "relationship_stage": client.relationship_stage,
            "avg_sentiment_score": client.avg_sentiment_score,
            "first_contact_at": client.first_contact_at.isoformat() if client.first_contact_at else None,
            "last_contact_at": client.last_contact_at.isoformat() if client.last_contact_at else None,
            "external_crm_id": client.external_crm_id,
            "external_crm_type": client.external_crm_type,
            "metadata": client.metadata,
            "notes": client.notes,
        },
        "meetings": [
            {
                "id": m.id,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "status": m.status,
                "duration_seconds": m.duration_seconds,
                "summary_text": m.summary_text,
                "confidence_score": m.confidence_score,
                "deal_heat": (
                    m.summary.get("content", {}).get("deal_heat")
                    if m.summary and isinstance(m.summary, dict)
                    else None
                ),
            }
            for m in meetings
        ],
        "sentiment_trend": sentiment_trend,
    }
