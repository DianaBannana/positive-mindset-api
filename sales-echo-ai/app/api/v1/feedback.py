"""
Feedback API - User feedback for AI-generated content

Provides endpoints for:
- Submitting feedback on AI-generated summaries
- Tracking accuracy ratings and corrections
- Aggregating feedback for manager insights
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_prisma

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class FeedbackSubmission(BaseModel):
    """Request model for submitting feedback."""
    meeting_id: str
    section_type: str = Field(..., description="summary, action_items, deal_value, etc.")
    section_index: Optional[int] = Field(None, description="Index for array items")
    rating: str = Field(..., description="positive, negative, neutral")
    feedback_type: str = Field("accuracy", description="accuracy, missing, hallucination, incomplete, wrong_language")
    original_value: Optional[Any] = None
    corrected_value: Optional[Any] = None
    feedback_note: Optional[str] = None
    category_tags: Optional[List[str]] = None


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    id: str
    meeting_id: str
    section_type: str
    rating: str
    created_at: str
    message: str


class FeedbackStats(BaseModel):
    """Aggregated feedback statistics."""
    total_feedback: int
    positive_count: int
    negative_count: int
    neutral_count: int
    accuracy_rate: float
    by_section: Dict[str, Dict[str, int]]
    by_type: Dict[str, int]
    top_issues: List[Dict[str, Any]]
    recommendations: List[str]


class ManagerInsights(BaseModel):
    """Manager-level insights from feedback data."""
    period_days: int
    total_meetings: int
    total_feedback: int
    accuracy_rate: float
    section_accuracy: Dict[str, float]
    common_issues: List[Dict[str, Any]]
    category_distribution: Dict[str, int]
    recommendations: List[Dict[str, Any]]
    trend: str  # "improving", "stable", "declining"


# ============================================
# Feedback Submission Endpoints
# ============================================

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackSubmission,
    org_id: str = Query(..., description="Organization ID"),
    user_id: Optional[str] = Query(None, description="User ID"),
):
    """
    Submit feedback for an AI-generated section.
    
    This enables the learning loop by tracking:
    - Accuracy ratings (thumbs up/down)
    - Corrections (user-provided fixes)
    - Issue categorization (hallucination, missing info, etc.)
    """
    # DEV_ONLY_WARNING: org_id should come from JWT in production
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        prisma = get_prisma()
        
        # Verify meeting exists and belongs to org
        meeting = await prisma.meeting.find_unique(where={"id": feedback.meeting_id})
        if not meeting or meeting.org_id != org_id:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Get confidence score from meeting summary
        confidence_at_generation = None
        if meeting.summary and isinstance(meeting.summary, dict):
            governance = meeting.summary.get("governance", {})
            confidence_at_generation = governance.get("confidence_score")
        
        # Create feedback log entry
        feedback_log = await prisma.feedbacklog.create(
            data={
                "org_id": org_id,
                "user_id": user_id,
                "meeting_id": feedback.meeting_id,
                "section_type": feedback.section_type,
                "section_index": feedback.section_index,
                "rating": feedback.rating,
                "feedback_type": feedback.feedback_type,
                "original_value": feedback.original_value,
                "corrected_value": feedback.corrected_value,
                "feedback_note": feedback.feedback_note,
                "category_tags": feedback.category_tags,
                "confidence_at_generation": confidence_at_generation,
            }
        )
        
        logger.info(
            f"Feedback submitted for meeting {feedback.meeting_id}, "
            f"section {feedback.section_type}, rating: {feedback.rating}"
        )
        
        return FeedbackResponse(
            id=feedback_log.id,
            meeting_id=feedback.meeting_id,
            section_type=feedback.section_type,
            rating=feedback.rating,
            created_at=feedback_log.created_at.isoformat(),
            message="Feedback recorded successfully",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/feedback/meeting/{meeting_id}")
async def get_meeting_feedback(
    meeting_id: str,
    org_id: str = Query(..., description="Organization ID"),
):
    """
    Get all feedback for a specific meeting.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        prisma = get_prisma()
        
        feedback_logs = await prisma.feedbacklog.find_many(
            where={
                "meeting_id": meeting_id,
                "org_id": org_id,
            },
            order_by={"created_at": "desc"},
        )
        
        return {
            "meeting_id": meeting_id,
            "feedback_count": len(feedback_logs),
            "feedback": [
                {
                    "id": log.id,
                    "section_type": log.section_type,
                    "section_index": log.section_index,
                    "rating": log.rating,
                    "feedback_type": log.feedback_type,
                    "feedback_note": log.feedback_note,
                    "has_correction": log.corrected_value is not None,
                    "created_at": log.created_at.isoformat(),
                }
                for log in feedback_logs
            ],
        }
        
    except Exception as e:
        logger.error(f"Error fetching meeting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch feedback")


# ============================================
# Feedback Analytics Endpoints
# ============================================

@router.get("/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    org_id: str = Query(..., description="Organization ID"),
    days: int = Query(30, description="Number of days to analyze"),
):
    """
    Get aggregated feedback statistics for an organization.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        prisma = get_prisma()
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Fetch all feedback in period
        feedback_logs = await prisma.feedbacklog.find_many(
            where={
                "org_id": org_id,
                "created_at": {"gte": since_date},
            },
        )
        
        if not feedback_logs:
            return FeedbackStats(
                total_feedback=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                accuracy_rate=0.0,
                by_section={},
                by_type={},
                top_issues=[],
                recommendations=[],
            )
        
        # Count by rating
        positive_count = sum(1 for f in feedback_logs if f.rating == "positive")
        negative_count = sum(1 for f in feedback_logs if f.rating == "negative")
        neutral_count = sum(1 for f in feedback_logs if f.rating == "neutral")
        
        # Accuracy rate
        total_rated = positive_count + negative_count
        accuracy_rate = positive_count / total_rated if total_rated > 0 else 0.0
        
        # Group by section
        by_section: Dict[str, Dict[str, int]] = {}
        for f in feedback_logs:
            if f.section_type not in by_section:
                by_section[f.section_type] = {"positive": 0, "negative": 0, "neutral": 0}
            by_section[f.section_type][f.rating] = by_section[f.section_type].get(f.rating, 0) + 1
        
        # Group by feedback type
        by_type: Dict[str, int] = {}
        for f in feedback_logs:
            by_type[f.feedback_type] = by_type.get(f.feedback_type, 0) + 1
        
        # Identify top issues
        top_issues = []
        for section, counts in by_section.items():
            if counts.get("negative", 0) > 0:
                total = sum(counts.values())
                error_rate = counts["negative"] / total if total > 0 else 0
                top_issues.append({
                    "section": section,
                    "negative_count": counts["negative"],
                    "total_count": total,
                    "error_rate": round(error_rate * 100, 1),
                })
        top_issues.sort(key=lambda x: x["error_rate"], reverse=True)
        
        # Generate recommendations
        recommendations = _generate_recommendations(by_section, by_type, accuracy_rate)
        
        return FeedbackStats(
            total_feedback=len(feedback_logs),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            accuracy_rate=round(accuracy_rate * 100, 1),
            by_section=by_section,
            by_type=by_type,
            top_issues=top_issues[:5],
            recommendations=recommendations,
        )
        
    except Exception as e:
        logger.error(f"Error computing feedback stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to compute feedback stats")


@router.get("/feedback/manager-insights", response_model=ManagerInsights)
async def get_manager_insights(
    org_id: str = Query(..., description="Organization ID"),
    days: int = Query(30, description="Number of days to analyze"),
):
    """
    Get manager-level insights from feedback data.
    
    Provides actionable recommendations based on feedback patterns.
    """
    if settings.dev_org_id and (not org_id or org_id == "default-org-id"):
        org_id = settings.dev_org_id
    
    try:
        prisma = get_prisma()
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Fetch feedback
        feedback_logs = await prisma.feedbacklog.find_many(
            where={
                "org_id": org_id,
                "created_at": {"gte": since_date},
            },
        )
        
        # Count meetings with feedback
        meeting_ids = set(f.meeting_id for f in feedback_logs)
        total_meetings = len(meeting_ids)
        
        if not feedback_logs:
            return ManagerInsights(
                period_days=days,
                total_meetings=0,
                total_feedback=0,
                accuracy_rate=0.0,
                section_accuracy={},
                common_issues=[],
                category_distribution={},
                recommendations=[],
                trend="stable",
            )
        
        # Calculate accuracy
        positive = sum(1 for f in feedback_logs if f.rating == "positive")
        negative = sum(1 for f in feedback_logs if f.rating == "negative")
        total_rated = positive + negative
        accuracy_rate = positive / total_rated if total_rated > 0 else 0.0
        
        # Section-level accuracy
        section_accuracy: Dict[str, float] = {}
        section_counts: Dict[str, Dict[str, int]] = {}
        
        for f in feedback_logs:
            if f.section_type not in section_counts:
                section_counts[f.section_type] = {"positive": 0, "negative": 0}
            if f.rating in ["positive", "negative"]:
                section_counts[f.section_type][f.rating] += 1
        
        for section, counts in section_counts.items():
            total = counts["positive"] + counts["negative"]
            section_accuracy[section] = round(
                (counts["positive"] / total * 100) if total > 0 else 0, 1
            )
        
        # Category distribution from tags
        category_distribution: Dict[str, int] = {}
        for f in feedback_logs:
            if f.category_tags:
                for tag in f.category_tags:
                    category_distribution[tag] = category_distribution.get(tag, 0) + 1
        
        # Identify common issues
        common_issues = []
        for f in feedback_logs:
            if f.rating == "negative" and f.feedback_note:
                common_issues.append({
                    "section": f.section_type,
                    "type": f.feedback_type,
                    "note": f.feedback_note,
                    "date": f.created_at.isoformat(),
                })
        
        # Generate smart recommendations
        recommendations = _generate_manager_recommendations(
            section_accuracy,
            category_distribution,
            common_issues,
            accuracy_rate,
        )
        
        # Calculate trend (simplified)
        trend = "stable"
        if len(feedback_logs) >= 10:
            mid_point = len(feedback_logs) // 2
            first_half = feedback_logs[mid_point:]
            second_half = feedback_logs[:mid_point]
            
            first_acc = sum(1 for f in first_half if f.rating == "positive") / len(first_half)
            second_acc = sum(1 for f in second_half if f.rating == "positive") / len(second_half)
            
            if second_acc - first_acc > 0.1:
                trend = "improving"
            elif first_acc - second_acc > 0.1:
                trend = "declining"
        
        return ManagerInsights(
            period_days=days,
            total_meetings=total_meetings,
            total_feedback=len(feedback_logs),
            accuracy_rate=round(accuracy_rate * 100, 1),
            section_accuracy=section_accuracy,
            common_issues=common_issues[:10],
            category_distribution=category_distribution,
            recommendations=recommendations,
            trend=trend,
        )
        
    except Exception as e:
        logger.error(f"Error computing manager insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to compute manager insights")


# ============================================
# Helper Functions
# ============================================

def _generate_recommendations(
    by_section: Dict[str, Dict[str, int]],
    by_type: Dict[str, int],
    accuracy_rate: float,
) -> List[str]:
    """Generate recommendations based on feedback patterns."""
    recommendations = []
    
    # Check for low accuracy sections
    for section, counts in by_section.items():
        total = sum(counts.values())
        if total >= 3 and counts.get("negative", 0) / total > 0.3:
            recommendations.append(
                f"High error rate in '{section}' section. "
                f"Consider adding specific instructions to Custom Brain Config."
            )
    
    # Check for hallucination issues
    if by_type.get("hallucination", 0) >= 3:
        recommendations.append(
            "Multiple hallucination reports detected. "
            "Add instruction: 'Only extract information explicitly stated in transcript.'"
        )
    
    # Check for missing information
    if by_type.get("missing", 0) >= 5:
        recommendations.append(
            "Users report missing information frequently. "
            "Review custom prompt to ensure all required fields are requested."
        )
    
    # General accuracy recommendation
    if accuracy_rate < 0.7:
        recommendations.append(
            "Overall accuracy below 70%. Consider reviewing recent negative feedback "
            "and updating AI instructions accordingly."
        )
    
    return recommendations


def _generate_manager_recommendations(
    section_accuracy: Dict[str, float],
    category_distribution: Dict[str, int],
    common_issues: List[Dict[str, Any]],
    overall_accuracy: float,
) -> List[Dict[str, Any]]:
    """Generate actionable recommendations for managers."""
    recommendations = []
    
    # Section-specific recommendations
    for section, accuracy in section_accuracy.items():
        if accuracy < 70:
            recommendations.append({
                "type": "section_improvement",
                "priority": "high" if accuracy < 50 else "medium",
                "section": section,
                "current_accuracy": accuracy,
                "suggestion": f"Update Custom Brain Instructions to improve {section} extraction.",
                "example_instruction": _get_example_instruction(section),
            })
    
    # Category-based recommendations
    if category_distribution:
        top_category = max(category_distribution.items(), key=lambda x: x[1])
        if top_category[1] >= 5:
            recommendations.append({
                "type": "category_focus",
                "priority": "medium",
                "category": top_category[0],
                "count": top_category[1],
                "suggestion": f"AI frequently misses '{top_category[0]}'. Add specific extraction rules.",
                "example_instruction": f"Always identify and extract {top_category[0]} mentions.",
            })
    
    # Overall accuracy recommendation
    if overall_accuracy < 70:
        recommendations.append({
            "type": "general_improvement",
            "priority": "high",
            "current_accuracy": overall_accuracy,
            "suggestion": "Schedule review of AI configuration and recent negative feedback.",
            "action": "Review negative feedback patterns and update Custom Brain Instructions.",
        })
    elif overall_accuracy >= 90:
        recommendations.append({
            "type": "positive_feedback",
            "priority": "low",
            "current_accuracy": overall_accuracy,
            "suggestion": "AI performing well. Consider expanding to additional use cases.",
        })
    
    return recommendations


def _get_example_instruction(section: str) -> str:
    """Get example instruction for a section."""
    examples = {
        "summary": "Write concise summaries focusing on key decisions and next steps.",
        "action_items": "Extract ALL action items mentioned, including implicit commitments.",
        "deal_value": "Look for price mentions, budgets, and investment amounts in both Hebrew and English.",
        "next_meeting": "Extract scheduling mentions like 'next week', 'tomorrow', or specific dates.",
        "objection": "Identify customer concerns, hesitations, and competitive comparisons.",
    }
    return examples.get(section, f"Improve extraction accuracy for {section}.")
