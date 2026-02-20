"""
Analytics API Endpoints

Provides aggregated statistics and insights across meetings for organizations.
Supports dashboard visualizations and reporting.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from collections import defaultdict

from app.core.database import get_prisma
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ==================== Response Models ====================

class ActionItemStats(BaseModel):
    """Statistics for action items."""
    total: int = Field(..., description="Total action items extracted")
    pending: int = Field(..., description="Action items without completion")
    high_confidence: int = Field(..., description="Items with confidence >= 0.8")
    by_assignee: Dict[str, int] = Field(default_factory=dict, description="Count by assignee")


class SentimentBreakdown(BaseModel):
    """Sentiment analysis breakdown."""
    positive: int = Field(0, description="Positive sentiment count")
    neutral: int = Field(0, description="Neutral sentiment count")
    negative: int = Field(0, description="Negative sentiment count")
    average_score: float = Field(0.0, description="Average sentiment score (0-1)")


class DealHeatStats(BaseModel):
    """Deal heat distribution."""
    hot: int = Field(0, description="High probability deals")
    warm: int = Field(0, description="Medium probability deals")
    cold: int = Field(0, description="Low probability deals")
    total_pipeline_value: float = Field(0.0, description="Total value of all deals")
    currency: str = Field("ILS", description="Currency for pipeline value")


class TimeSeriesPoint(BaseModel):
    """Single point in time series data."""
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    value: float = Field(..., description="Value for this date")


class AnalyticsSummary(BaseModel):
    """Complete analytics summary for an organization."""
    org_id: str = Field(..., description="Organization ID")
    period_start: str = Field(..., description="Start of analysis period")
    period_end: str = Field(..., description="End of analysis period")
    
    # Meeting counts
    total_meetings: int = Field(..., description="Total meetings in period")
    completed_meetings: int = Field(..., description="Successfully processed meetings")
    failed_meetings: int = Field(..., description="Failed processing attempts")
    pending_meetings: int = Field(..., description="Meetings awaiting processing")
    
    # Time metrics
    total_duration_minutes: float = Field(..., description="Total call duration in minutes")
    average_duration_minutes: float = Field(..., description="Average call duration")
    
    # AI insights
    action_items: ActionItemStats = Field(..., description="Action item statistics")
    sentiment: SentimentBreakdown = Field(..., description="Sentiment analysis")
    deal_heat: DealHeatStats = Field(..., description="Deal heat distribution")
    
    # Confidence metrics
    average_confidence: float = Field(..., description="Average AI confidence score")
    requires_review_count: int = Field(..., description="Meetings flagged for review")
    
    # Trends
    meetings_by_day: List[TimeSeriesPoint] = Field(default_factory=list, description="Daily meeting counts")
    pipeline_by_day: List[TimeSeriesPoint] = Field(default_factory=list, description="Daily pipeline values")
    
    # Top performers
    top_users: List[Dict[str, Any]] = Field(default_factory=list, description="Top users by meeting count")
    
    # Metadata
    generated_at: str = Field(..., description="Report generation timestamp")


class QuickStats(BaseModel):
    """Quick stats for dashboard widgets."""
    total_meetings: int
    total_duration_hours: float
    action_items_pending: int
    pipeline_value: float
    average_deal_heat: float
    meetings_this_week: int
    meetings_change_percent: float = Field(..., description="Week-over-week change")


# ==================== API Endpoints ====================

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    org_id: str = Query(..., description="Organization ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get comprehensive analytics summary for an organization.
    
    Aggregates statistics across all meetings including:
    - Total meetings and processing status
    - Average sentiment and confidence scores
    - Action item counts and distribution
    - Deal pipeline values and heat scores
    - Time series data for trends
    
    Args:
        org_id: Organization ID to analyze
        days: Number of days to include in analysis (default: 30)
        
    Returns:
        AnalyticsSummary with complete organization metrics
    """
    prisma = get_prisma()
    
    # DEV_ONLY_WARNING: In development, use DEV_ORG_ID if provided org_id is invalid
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        logger.warning(f"DEV_ONLY: Using DEV_ORG_ID instead of: {org_id}")
        org_id = settings.dev_org_id
    
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)
    
    try:
        # Fetch all meetings in period
        meetings = await prisma.meeting.find_many(
            where={
                "org_id": org_id,
                "created_at": {
                    "gte": period_start,
                    "lte": period_end,
                },
            },
            order={"created_at": "desc"},
        )
        
        if not meetings:
            logger.info(f"No meetings found for org {org_id} in the last {days} days")
            return AnalyticsSummary(
                org_id=org_id,
                period_start=period_start.isoformat(),
                period_end=period_end.isoformat(),
                total_meetings=0,
                completed_meetings=0,
                failed_meetings=0,
                pending_meetings=0,
                total_duration_minutes=0,
                average_duration_minutes=0,
                action_items=ActionItemStats(
                    total=0, pending=0, high_confidence=0, by_assignee={}
                ),
                sentiment=SentimentBreakdown(),
                deal_heat=DealHeatStats(),
                average_confidence=0,
                requires_review_count=0,
                meetings_by_day=[],
                pipeline_by_day=[],
                top_users=[],
                generated_at=datetime.utcnow().isoformat(),
            )
        
        # Count by status
        status_counts = defaultdict(int)
        for m in meetings:
            status_counts[m.status] += 1
        
        # Calculate duration metrics
        total_seconds = sum(m.duration_seconds or 0 for m in meetings)
        meetings_with_duration = [m for m in meetings if m.duration_seconds]
        avg_seconds = (
            total_seconds / len(meetings_with_duration)
            if meetings_with_duration else 0
        )
        
        # Aggregate action items
        action_item_stats = await _aggregate_action_items(meetings)
        
        # Aggregate sentiment
        sentiment_stats = await _aggregate_sentiment(meetings)
        
        # Aggregate deal heat
        deal_heat_stats = await _aggregate_deal_heat(meetings)
        
        # Calculate confidence metrics
        confidence_scores = []
        requires_review = 0
        for m in meetings:
            if m.summary and isinstance(m.summary, dict):
                governance = m.summary.get("governance", {})
                if governance:
                    score = governance.get("confidence_score")
                    if score is not None:
                        confidence_scores.append(score)
                    if governance.get("requires_review"):
                        requires_review += 1
        
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0
        )
        
        # Generate time series
        meetings_by_day = _generate_daily_series(meetings, "count", days)
        pipeline_by_day = _generate_pipeline_series(meetings, days)
        
        # Top users
        top_users = _calculate_top_users(meetings)
        
        return AnalyticsSummary(
            org_id=org_id,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            total_meetings=len(meetings),
            completed_meetings=status_counts.get("COMPLETED", 0),
            failed_meetings=status_counts.get("FAILED", 0),
            pending_meetings=status_counts.get("PENDING", 0) + status_counts.get("PROCESSING", 0),
            total_duration_minutes=total_seconds / 60,
            average_duration_minutes=avg_seconds / 60,
            action_items=action_item_stats,
            sentiment=sentiment_stats,
            deal_heat=deal_heat_stats,
            average_confidence=avg_confidence,
            requires_review_count=requires_review,
            meetings_by_day=meetings_by_day,
            pipeline_by_day=pipeline_by_day,
            top_users=top_users,
            generated_at=datetime.utcnow().isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Analytics query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate analytics summary",
        )


@router.get("/quick-stats", response_model=QuickStats)
async def get_quick_stats(
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get quick stats for dashboard widgets.
    
    Provides key metrics optimized for dashboard display:
    - Total meetings count
    - Total duration in hours
    - Pending action items
    - Pipeline value
    - Average deal heat
    - Week-over-week comparison
    
    Args:
        org_id: Organization ID
        
    Returns:
        QuickStats with key dashboard metrics
    """
    prisma = get_prisma()
    
    # DEV_ONLY_WARNING: Use DEV_ORG_ID if needed
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    now = datetime.utcnow()
    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)
    
    try:
        # Fetch meetings for this week and last week
        all_meetings = await prisma.meeting.find_many(
            where={
                "org_id": org_id,
                "created_at": {"gte": last_week_start},
            },
        )
        
        this_week = [m for m in all_meetings if m.created_at >= this_week_start]
        last_week = [m for m in all_meetings if m.created_at < this_week_start]
        
        # Calculate metrics
        total_meetings = len(all_meetings)
        total_seconds = sum(m.duration_seconds or 0 for m in all_meetings)
        
        # Count pending action items
        pending_actions = 0
        pipeline_value = 0.0
        deal_heat_scores = []
        
        for m in all_meetings:
            if m.summary and isinstance(m.summary, dict):
                # Action items
                action_items = m.summary.get("action_items", [])
                pending_actions += len(action_items)
                
                # Deal value
                crm_entities = m.summary.get("crm_entities", {})
                if crm_entities:
                    deal_value = crm_entities.get("deal_value", {})
                    if deal_value and deal_value.get("value"):
                        pipeline_value += deal_value.get("value", 0)
                
                # Deal heat (from confidence)
                governance = m.summary.get("governance", {})
                if governance and governance.get("confidence_score"):
                    deal_heat_scores.append(governance["confidence_score"])
        
        avg_heat = sum(deal_heat_scores) / len(deal_heat_scores) if deal_heat_scores else 0.5
        
        # Week-over-week change
        this_week_count = len(this_week)
        last_week_count = len(last_week)
        change_percent = (
            ((this_week_count - last_week_count) / last_week_count * 100)
            if last_week_count > 0 else 0
        )
        
        return QuickStats(
            total_meetings=total_meetings,
            total_duration_hours=total_seconds / 3600,
            action_items_pending=pending_actions,
            pipeline_value=pipeline_value,
            average_deal_heat=avg_heat,
            meetings_this_week=this_week_count,
            meetings_change_percent=round(change_percent, 1),
        )
        
    except Exception as e:
        logger.error(f"Quick stats query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch quick stats",
        )


@router.get("/action-items")
async def get_pending_action_items(
    org_id: str = Query(..., description="Organization ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    assignee: Optional[str] = Query(None, description="Filter by assignee name"),
):
    """
    Get all pending action items across meetings.
    
    Aggregates action items from all completed meetings,
    optionally filtered by assignee.
    
    Args:
        org_id: Organization ID
        limit: Maximum items to return
        assignee: Optional assignee filter
        
    Returns:
        List of action items with meeting context
    """
    prisma = get_prisma()
    
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        meetings = await prisma.meeting.find_many(
            where={
                "org_id": org_id,
                "status": "COMPLETED",
            },
            order={"created_at": "desc"},
            take=200,  # Reasonable limit for aggregation
        )
        
        action_items = []
        for m in meetings:
            if m.summary and isinstance(m.summary, dict):
                items = m.summary.get("action_items", [])
                for item in items:
                    # Apply assignee filter if specified
                    if assignee and item.get("assignee", "").lower() != assignee.lower():
                        continue
                    
                    action_items.append({
                        "meeting_id": m.id,
                        "meeting_date": m.created_at.isoformat(),
                        "client_name": m.client_name,
                        "task": item.get("task"),
                        "due": item.get("due"),
                        "assignee": item.get("assignee"),
                        "confidence": item.get("confidence", 0),
                        "source": item.get("source"),
                    })
        
        # Sort by due date (items with due dates first)
        action_items.sort(
            key=lambda x: (x["due"] is None, x["due"] or "", -x["confidence"])
        )
        
        return {
            "org_id": org_id,
            "total_count": len(action_items),
            "returned_count": min(len(action_items), limit),
            "action_items": action_items[:limit],
        }
        
    except Exception as e:
        logger.error(f"Action items query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch action items",
        )


@router.get("/pipeline")
async def get_pipeline_summary(
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get sales pipeline summary from deal values.
    
    Aggregates deal values from all meetings and
    categorizes by deal stage/heat.
    
    Args:
        org_id: Organization ID
        
    Returns:
        Pipeline summary with stage breakdown
    """
    prisma = get_prisma()
    
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        meetings = await prisma.meeting.find_many(
            where={
                "org_id": org_id,
                "status": "COMPLETED",
            },
        )
        
        pipeline = {
            "total_value": 0,
            "deal_count": 0,
            "by_heat": {"hot": 0, "warm": 0, "cold": 0},
            "by_heat_value": {"hot": 0, "warm": 0, "cold": 0},
            "deals": [],
        }
        
        for m in meetings:
            if m.summary and isinstance(m.summary, dict):
                crm_entities = m.summary.get("crm_entities", {})
                if not crm_entities:
                    continue
                
                deal_value = crm_entities.get("deal_value", {})
                if not deal_value or not deal_value.get("value"):
                    continue
                
                value = deal_value.get("value", 0)
                confidence = m.summary.get("governance", {}).get("confidence_score", 0.5)
                
                # Determine heat level
                if confidence >= 0.75:
                    heat = "hot"
                elif confidence >= 0.5:
                    heat = "warm"
                else:
                    heat = "cold"
                
                pipeline["total_value"] += value
                pipeline["deal_count"] += 1
                pipeline["by_heat"][heat] += 1
                pipeline["by_heat_value"][heat] += value
                
                pipeline["deals"].append({
                    "meeting_id": m.id,
                    "client_name": m.client_name,
                    "value": value,
                    "currency": deal_value.get("currency", "ILS"),
                    "heat": heat,
                    "confidence": confidence,
                    "date": m.created_at.isoformat(),
                })
        
        # Sort deals by value
        pipeline["deals"].sort(key=lambda x: -x["value"])
        
        return {
            "org_id": org_id,
            "currency": "ILS",
            **pipeline,
        }
        
    except Exception as e:
        logger.error(f"Pipeline query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch pipeline summary",
        )


# ==================== Helper Functions ====================

async def _aggregate_action_items(meetings: list) -> ActionItemStats:
    """Aggregate action item statistics from meetings."""
    total = 0
    high_confidence = 0
    by_assignee = defaultdict(int)
    
    for m in meetings:
        if m.summary and isinstance(m.summary, dict):
            items = m.summary.get("action_items", [])
            for item in items:
                total += 1
                
                confidence = item.get("confidence", 0)
                if confidence >= 0.8:
                    high_confidence += 1
                
                assignee = item.get("assignee") or "Unassigned"
                by_assignee[assignee] += 1
    
    return ActionItemStats(
        total=total,
        pending=total,  # All items considered pending until CRM integration
        high_confidence=high_confidence,
        by_assignee=dict(by_assignee),
    )


async def _aggregate_sentiment(meetings: list) -> SentimentBreakdown:
    """Aggregate sentiment statistics from meetings."""
    positive = 0
    neutral = 0
    negative = 0
    scores = []
    
    for m in meetings:
        if m.summary and isinstance(m.summary, dict):
            governance = m.summary.get("governance", {})
            confidence = governance.get("confidence_score", 0.5)
            scores.append(confidence)
            
            # Map confidence to sentiment (simplified)
            if confidence >= 0.7:
                positive += 1
            elif confidence >= 0.4:
                neutral += 1
            else:
                negative += 1
    
    return SentimentBreakdown(
        positive=positive,
        neutral=neutral,
        negative=negative,
        average_score=sum(scores) / len(scores) if scores else 0.5,
    )


async def _aggregate_deal_heat(meetings: list) -> DealHeatStats:
    """Aggregate deal heat statistics from meetings."""
    hot = 0
    warm = 0
    cold = 0
    total_value = 0.0
    
    for m in meetings:
        if m.summary and isinstance(m.summary, dict):
            governance = m.summary.get("governance", {})
            confidence = governance.get("confidence_score", 0.5)
            
            if confidence >= 0.75:
                hot += 1
            elif confidence >= 0.5:
                warm += 1
            else:
                cold += 1
            
            crm_entities = m.summary.get("crm_entities", {})
            if crm_entities:
                deal_value = crm_entities.get("deal_value", {})
                if deal_value and deal_value.get("value"):
                    total_value += deal_value.get("value", 0)
    
    return DealHeatStats(
        hot=hot,
        warm=warm,
        cold=cold,
        total_pipeline_value=total_value,
        currency="ILS",
    )


def _generate_daily_series(meetings: list, metric: str, days: int) -> List[TimeSeriesPoint]:
    """Generate daily time series data."""
    today = datetime.utcnow().date()
    daily_counts = defaultdict(int)
    
    for m in meetings:
        date_str = m.created_at.strftime("%Y-%m-%d")
        daily_counts[date_str] += 1
    
    series = []
    for i in range(days):
        date = today - timedelta(days=days - 1 - i)
        date_str = date.strftime("%Y-%m-%d")
        series.append(TimeSeriesPoint(
            date=date_str,
            value=float(daily_counts.get(date_str, 0)),
        ))
    
    return series


def _generate_pipeline_series(meetings: list, days: int) -> List[TimeSeriesPoint]:
    """Generate daily pipeline value series."""
    today = datetime.utcnow().date()
    daily_values = defaultdict(float)
    
    for m in meetings:
        if m.summary and isinstance(m.summary, dict):
            crm_entities = m.summary.get("crm_entities", {})
            if crm_entities:
                deal_value = crm_entities.get("deal_value", {})
                if deal_value and deal_value.get("value"):
                    date_str = m.created_at.strftime("%Y-%m-%d")
                    daily_values[date_str] += deal_value.get("value", 0)
    
    series = []
    cumulative = 0.0
    for i in range(days):
        date = today - timedelta(days=days - 1 - i)
        date_str = date.strftime("%Y-%m-%d")
        cumulative += daily_values.get(date_str, 0)
        series.append(TimeSeriesPoint(
            date=date_str,
            value=cumulative,
        ))
    
    return series


def _calculate_top_users(meetings: list, limit: int = 5) -> List[Dict[str, Any]]:
    """Calculate top users by meeting count."""
    user_stats = defaultdict(lambda: {"meeting_count": 0, "total_duration": 0})
    
    for m in meetings:
        if m.user_id:
            user_stats[m.user_id]["meeting_count"] += 1
            user_stats[m.user_id]["total_duration"] += m.duration_seconds or 0
    
    # Sort by meeting count
    sorted_users = sorted(
        user_stats.items(),
        key=lambda x: -x[1]["meeting_count"],
    )[:limit]
    
    return [
        {
            "user_id": user_id,
            "meeting_count": stats["meeting_count"],
            "total_duration_minutes": stats["total_duration"] / 60,
        }
        for user_id, stats in sorted_users
    ]
