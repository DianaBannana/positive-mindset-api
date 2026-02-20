"""
Manager Analytics API - Sales Excellence Dashboard

Provides analytics endpoints for managers:
- Pipeline Value aggregation
- Win Rate & Conversion metrics
- Sales Cycle Length
- Activity Heatmap
- Team Performance
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_prisma

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Response Models
# ============================================

class PipelineMetrics(BaseModel):
    """Pipeline value metrics."""
    total_value: float
    currency: str
    by_stage: Dict[str, float]  # stage -> value
    by_rep: List[Dict[str, Any]]  # Top reps by pipeline
    trend: List[Dict[str, Any]]  # Daily pipeline trend


class ConversionMetrics(BaseModel):
    """Win rate and conversion metrics."""
    total_meetings: int
    hot_deals: int
    warm_deals: int
    cold_deals: int
    win_rate: float  # hot / total
    conversion_funnel: Dict[str, int]  # stage -> count


class CycleMetrics(BaseModel):
    """Sales cycle length metrics."""
    avg_days_to_hot: float  # Average days from first meeting to "hot" deal
    avg_meetings_to_hot: float  # Average meetings needed
    by_rep: List[Dict[str, Any]]  # Per-rep cycle times


class ActivityHeatmap(BaseModel):
    """Activity volume heatmap data."""
    by_hour: Dict[int, int]  # hour (0-23) -> count
    by_day: Dict[str, int]  # day name -> count
    by_rep: List[Dict[str, Any]]  # Per-rep activity
    peak_hour: int
    peak_day: str


class SalesExcellenceResponse(BaseModel):
    """Complete Sales Excellence dashboard data."""
    pipeline: PipelineMetrics
    conversion: ConversionMetrics
    cycle: CycleMetrics
    activity: ActivityHeatmap
    period_days: int
    generated_at: str


# ============================================
# Analytics Endpoints
# ============================================

@router.get("/manager/excellence", response_model=SalesExcellenceResponse)
async def get_sales_excellence(
    org_id: str = Query(..., description="Organization ID"),
    days: int = Query(30, description="Analysis period in days"),
):
    """
    Get complete Sales Excellence dashboard metrics.
    
    Requires: Manager or Admin role.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    prisma = get_prisma()
    start_date = datetime.utcnow() - timedelta(days=days)
    
    try:
        # Fetch all completed meetings in period
        meetings = await prisma.meeting.find_many(
            where={
                "org_id": org_id,
                "created_at": {"gte": start_date},
                "status": "COMPLETED",
            },
            include={"user": True, "client": True}
        )
        
        # Fetch users for rep mapping
        users = await prisma.user.find_many(where={"org_id": org_id})
        user_map = {u.id: u.name for u in users}
        
        # ===== PIPELINE METRICS =====
        pipeline_by_rep: Dict[str, float] = defaultdict(float)
        pipeline_by_stage: Dict[str, float] = defaultdict(float)
        pipeline_by_day: Dict[str, float] = defaultdict(float)
        total_pipeline = 0.0
        
        # ===== CONVERSION METRICS =====
        hot_deals = 0
        warm_deals = 0
        cold_deals = 0
        
        # ===== CYCLE METRICS =====
        client_first_meeting: Dict[str, datetime] = {}
        client_hot_meeting: Dict[str, datetime] = {}
        client_meeting_count: Dict[str, int] = defaultdict(int)
        
        # ===== ACTIVITY METRICS =====
        activity_by_hour: Dict[int, int] = defaultdict(int)
        activity_by_day: Dict[str, int] = defaultdict(int)
        activity_by_rep: Dict[str, int] = defaultdict(int)
        
        for meeting in meetings:
            user_id = meeting.user_id
            user_name = user_map.get(user_id, "Unknown")
            client_id = meeting.client_id
            created_at = meeting.created_at
            
            # Activity tracking
            if created_at:
                activity_by_hour[created_at.hour] += 1
                day_name = created_at.strftime("%A")
                activity_by_day[day_name] += 1
                activity_by_rep[user_name] += 1
            
            # Process summary data
            summary = meeting.summary
            if not summary or not isinstance(summary, dict):
                continue
            
            content = summary.get("content", {})
            if not isinstance(content, dict):
                continue
            
            # Deal heat
            deal_heat = content.get("deal_heat", "cold")
            if deal_heat == "hot":
                hot_deals += 1
            elif deal_heat == "warm":
                warm_deals += 1
            else:
                cold_deals += 1
            
            # Pipeline value
            crm_entities = content.get("crm_entities", {})
            if isinstance(crm_entities, dict):
                deal_value_obj = crm_entities.get("deal_value", {})
                if isinstance(deal_value_obj, dict):
                    value = deal_value_obj.get("value", 0) or 0
                    total_pipeline += value
                    pipeline_by_rep[user_name] += value
                    pipeline_by_stage[deal_heat] += value
                    
                    if created_at:
                        day_key = created_at.strftime("%Y-%m-%d")
                        pipeline_by_day[day_key] += value
            
            # Client cycle tracking
            if client_id:
                client_meeting_count[client_id] += 1
                
                if client_id not in client_first_meeting:
                    client_first_meeting[client_id] = created_at
                
                if deal_heat == "hot" and client_id not in client_hot_meeting:
                    client_hot_meeting[client_id] = created_at
        
        # Calculate cycle metrics
        days_to_hot = []
        meetings_to_hot = []
        
        for client_id in client_hot_meeting:
            first = client_first_meeting.get(client_id)
            hot = client_hot_meeting[client_id]
            
            if first and hot:
                delta_days = (hot - first).days
                days_to_hot.append(delta_days)
                meetings_to_hot.append(client_meeting_count[client_id])
        
        avg_days_to_hot = sum(days_to_hot) / len(days_to_hot) if days_to_hot else 0
        avg_meetings_to_hot = sum(meetings_to_hot) / len(meetings_to_hot) if meetings_to_hot else 0
        
        # Calculate win rate
        total_deals = hot_deals + warm_deals + cold_deals
        win_rate = (hot_deals / total_deals * 100) if total_deals > 0 else 0
        
        # Find peaks
        peak_hour = max(activity_by_hour.keys(), key=lambda h: activity_by_hour[h], default=9)
        peak_day = max(activity_by_day.keys(), key=lambda d: activity_by_day[d], default="Monday")
        
        # Build response
        pipeline = PipelineMetrics(
            total_value=total_pipeline,
            currency="ILS",
            by_stage=dict(pipeline_by_stage),
            by_rep=sorted(
                [{"name": k, "value": v} for k, v in pipeline_by_rep.items()],
                key=lambda x: x["value"],
                reverse=True
            )[:10],
            trend=sorted(
                [{"date": k, "value": v} for k, v in pipeline_by_day.items()],
                key=lambda x: x["date"]
            )[-30:],
        )
        
        conversion = ConversionMetrics(
            total_meetings=len(meetings),
            hot_deals=hot_deals,
            warm_deals=warm_deals,
            cold_deals=cold_deals,
            win_rate=round(win_rate, 1),
            conversion_funnel={
                "all_meetings": len(meetings),
                "with_deal_value": len([m for m in meetings if _has_deal_value(m)]),
                "warm_or_hot": hot_deals + warm_deals,
                "hot": hot_deals,
            }
        )
        
        cycle = CycleMetrics(
            avg_days_to_hot=round(avg_days_to_hot, 1),
            avg_meetings_to_hot=round(avg_meetings_to_hot, 1),
            by_rep=[],  # Could be expanded
        )
        
        activity = ActivityHeatmap(
            by_hour=dict(activity_by_hour),
            by_day=dict(activity_by_day),
            by_rep=sorted(
                [{"name": k, "count": v} for k, v in activity_by_rep.items()],
                key=lambda x: x["count"],
                reverse=True
            ),
            peak_hour=peak_hour,
            peak_day=peak_day,
        )
        
        return SalesExcellenceResponse(
            pipeline=pipeline,
            conversion=conversion,
            cycle=cycle,
            activity=activity,
            period_days=days,
            generated_at=datetime.utcnow().isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Error generating excellence metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate metrics")


def _has_deal_value(meeting) -> bool:
    """Check if meeting has a deal value extracted."""
    if not meeting.summary or not isinstance(meeting.summary, dict):
        return False
    content = meeting.summary.get("content", {})
    if not isinstance(content, dict):
        return False
    crm = content.get("crm_entities", {})
    if not isinstance(crm, dict):
        return False
    deal = crm.get("deal_value", {})
    return isinstance(deal, dict) and deal.get("value")


@router.get("/manager/pipeline/trend")
async def get_pipeline_trend(
    org_id: str = Query(...),
    days: int = Query(90),
):
    """
    Get detailed pipeline trend over time.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    prisma = get_prisma()
    start_date = datetime.utcnow() - timedelta(days=days)
    
    try:
        meetings = await prisma.meeting.find_many(
            where={
                "org_id": org_id,
                "created_at": {"gte": start_date},
                "status": "COMPLETED",
            },
            order_by={"created_at": "asc"}
        )
        
        daily_values: Dict[str, float] = defaultdict(float)
        cumulative = 0.0
        cumulative_data = []
        
        for meeting in meetings:
            if not meeting.summary or not isinstance(meeting.summary, dict):
                continue
            
            content = meeting.summary.get("content", {})
            if not isinstance(content, dict):
                continue
            
            crm = content.get("crm_entities", {})
            if isinstance(crm, dict):
                deal = crm.get("deal_value", {})
                if isinstance(deal, dict) and deal.get("value"):
                    day_key = meeting.created_at.strftime("%Y-%m-%d")
                    daily_values[day_key] += deal["value"]
        
        # Build cumulative
        for day_key in sorted(daily_values.keys()):
            cumulative += daily_values[day_key]
            cumulative_data.append({
                "date": day_key,
                "daily": daily_values[day_key],
                "cumulative": cumulative,
            })
        
        return {
            "period_days": days,
            "total_pipeline": cumulative,
            "trend": cumulative_data,
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline trend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get pipeline trend")


@router.get("/manager/activity/heatmap")
async def get_activity_heatmap(
    org_id: str = Query(...),
    days: int = Query(30),
):
    """
    Get detailed activity heatmap by hour and day.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    prisma = get_prisma()
    start_date = datetime.utcnow() - timedelta(days=days)
    
    try:
        meetings = await prisma.meeting.find_many(
            where={
                "org_id": org_id,
                "created_at": {"gte": start_date},
            }
        )
        
        # Build 7x24 grid
        heatmap: Dict[str, Dict[int, int]] = {
            "Monday": {h: 0 for h in range(24)},
            "Tuesday": {h: 0 for h in range(24)},
            "Wednesday": {h: 0 for h in range(24)},
            "Thursday": {h: 0 for h in range(24)},
            "Friday": {h: 0 for h in range(24)},
            "Saturday": {h: 0 for h in range(24)},
            "Sunday": {h: 0 for h in range(24)},
        }
        
        for meeting in meetings:
            if meeting.created_at:
                day = meeting.created_at.strftime("%A")
                hour = meeting.created_at.hour
                if day in heatmap:
                    heatmap[day][hour] += 1
        
        # Convert to list format
        grid = []
        for day_name in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            for hour in range(24):
                count = heatmap.get(day_name, {}).get(hour, 0)
                grid.append({
                    "day": day_name,
                    "hour": hour,
                    "count": count,
                })
        
        return {
            "period_days": days,
            "total_meetings": len(meetings),
            "grid": grid,
        }
        
    except Exception as e:
        logger.error(f"Error getting activity heatmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get heatmap")
