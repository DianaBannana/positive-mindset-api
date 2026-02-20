"""
Meeting Utilities - Shared logic for meeting data extraction

Consolidates duplicate code for parsing meeting summaries across:
- analytics.py
- manager_analytics.py
- users.py
- client_service.py

DRY Principle: All meeting summary parsing should use these utilities.
"""

from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DealMetrics:
    """Extracted deal metrics from a meeting."""
    value: float
    currency: str
    heat: str  # "hot", "warm", "cold"
    confidence: float


@dataclass
class SentimentMetrics:
    """Extracted sentiment metrics from a meeting."""
    score: float
    label: str  # "positive", "negative", "neutral"
    confidence: float


def extract_deal_value(summary: Optional[Dict[str, Any]]) -> Optional[DealMetrics]:
    """
    Extract deal value information from a meeting summary.
    
    Args:
        summary: The meeting.summary JSON object
        
    Returns:
        DealMetrics if found, None otherwise
    """
    if not summary or not isinstance(summary, dict):
        return None
    
    # Try content.crm_entities.deal_value (new structure)
    content = summary.get("content", {})
    if isinstance(content, dict):
        crm_entities = content.get("crm_entities", {})
        if isinstance(crm_entities, dict):
            deal_value = crm_entities.get("deal_value", {})
            if isinstance(deal_value, dict) and deal_value.get("value"):
                # Determine heat from deal_heat or confidence
                deal_heat = content.get("deal_heat", "cold")
                governance = summary.get("governance", {})
                confidence = governance.get("confidence_score", 0.5) if isinstance(governance, dict) else 0.5
                
                return DealMetrics(
                    value=float(deal_value.get("value", 0)),
                    currency=deal_value.get("currency", "ILS"),
                    heat=deal_heat,
                    confidence=confidence,
                )
    
    # Try legacy crm_entities at root level
    crm_entities = summary.get("crm_entities", {})
    if isinstance(crm_entities, dict):
        deal_value = crm_entities.get("deal_value", {})
        if isinstance(deal_value, dict) and deal_value.get("value"):
            governance = summary.get("governance", {})
            confidence = governance.get("confidence_score", 0.5) if isinstance(governance, dict) else 0.5
            
            # Calculate heat from confidence
            if confidence >= 0.75:
                heat = "hot"
            elif confidence >= 0.5:
                heat = "warm"
            else:
                heat = "cold"
            
            return DealMetrics(
                value=float(deal_value.get("value", 0)),
                currency=deal_value.get("currency", "ILS"),
                heat=heat,
                confidence=confidence,
            )
    
    return None


def extract_deal_heat(summary: Optional[Dict[str, Any]]) -> str:
    """
    Extract deal heat classification from a meeting summary.
    
    Args:
        summary: The meeting.summary JSON object
        
    Returns:
        "hot", "warm", or "cold"
    """
    if not summary or not isinstance(summary, dict):
        return "cold"
    
    # Try content.deal_heat (explicit field)
    content = summary.get("content", {})
    if isinstance(content, dict):
        deal_heat = content.get("deal_heat")
        if deal_heat in ("hot", "warm", "cold"):
            return deal_heat
    
    # Fallback to confidence-based heat
    governance = summary.get("governance", {})
    if isinstance(governance, dict):
        confidence = governance.get("confidence_score", 0.5)
        if confidence >= 0.75:
            return "hot"
        elif confidence >= 0.5:
            return "warm"
    
    return "cold"


def extract_sentiment(summary: Optional[Dict[str, Any]]) -> Optional[SentimentMetrics]:
    """
    Extract sentiment information from a meeting summary.
    
    Args:
        summary: The meeting.summary JSON object
        
    Returns:
        SentimentMetrics if found, None otherwise
    """
    if not summary or not isinstance(summary, dict):
        return None
    
    # Try content.overall_sentiment
    content = summary.get("content", {})
    if isinstance(content, dict):
        sentiment = content.get("overall_sentiment", {})
        if isinstance(sentiment, dict) and sentiment.get("score") is not None:
            return SentimentMetrics(
                score=float(sentiment.get("score", 0)),
                label=sentiment.get("label", "neutral"),
                confidence=sentiment.get("confidence", 0.5),
            )
    
    # Try governance.sentiment_score
    governance = summary.get("governance", {})
    if isinstance(governance, dict):
        sentiment_score = governance.get("sentiment_score")
        if sentiment_score is not None:
            label = "positive" if sentiment_score > 0.3 else ("negative" if sentiment_score < -0.3 else "neutral")
            return SentimentMetrics(
                score=float(sentiment_score),
                label=label,
                confidence=governance.get("confidence_score", 0.5),
            )
    
    return None


def extract_action_items(summary: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract action items from a meeting summary.
    
    Args:
        summary: The meeting.summary JSON object
        
    Returns:
        List of action item dicts
    """
    if not summary or not isinstance(summary, dict):
        return []
    
    content = summary.get("content", {})
    if isinstance(content, dict):
        action_items = content.get("action_items", [])
        if isinstance(action_items, list):
            return action_items
    
    return []


def extract_summary_text(summary: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Extract the main summary text from a meeting summary.
    
    Args:
        summary: The meeting.summary JSON object
        
    Returns:
        Summary text string or None
    """
    if not summary or not isinstance(summary, dict):
        return None
    
    content = summary.get("content", {})
    if isinstance(content, dict):
        return content.get("summary_text")
    
    return None


def extract_next_meeting(summary: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Extract next meeting date information from a meeting summary.
    
    Args:
        summary: The meeting.summary JSON object
        
    Returns:
        Dict with date/time info or None
    """
    if not summary or not isinstance(summary, dict):
        return None
    
    content = summary.get("content", {})
    if isinstance(content, dict):
        crm_entities = content.get("crm_entities", {})
        if isinstance(crm_entities, dict):
            next_meeting = crm_entities.get("next_meeting_date", {})
            if isinstance(next_meeting, dict) and next_meeting.get("value"):
                return next_meeting
    
    return None


def has_deal_value(summary: Optional[Dict[str, Any]]) -> bool:
    """Check if meeting has a deal value extracted."""
    return extract_deal_value(summary) is not None


def aggregate_meeting_metrics(meetings: List[Any]) -> Dict[str, Any]:
    """
    Aggregate metrics from a list of meetings.
    
    Args:
        meetings: List of meeting objects with .summary attribute
        
    Returns:
        Dict with aggregated metrics
    """
    total_pipeline = 0.0
    hot_deals = 0
    warm_deals = 0
    cold_deals = 0
    sentiments: List[float] = []
    action_items_count = 0
    
    for meeting in meetings:
        summary = getattr(meeting, 'summary', None)
        
        # Deal metrics
        deal = extract_deal_value(summary)
        if deal:
            total_pipeline += deal.value
        
        # Heat classification
        heat = extract_deal_heat(summary)
        if heat == "hot":
            hot_deals += 1
        elif heat == "warm":
            warm_deals += 1
        else:
            cold_deals += 1
        
        # Sentiment
        sentiment = extract_sentiment(summary)
        if sentiment:
            sentiments.append(sentiment.score)
        
        # Action items
        action_items = extract_action_items(summary)
        action_items_count += len(action_items)
    
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None
    
    return {
        "total_meetings": len(meetings),
        "total_pipeline": total_pipeline,
        "hot_deals": hot_deals,
        "warm_deals": warm_deals,
        "cold_deals": cold_deals,
        "avg_sentiment": round(avg_sentiment, 3) if avg_sentiment is not None else None,
        "action_items_count": action_items_count,
    }
