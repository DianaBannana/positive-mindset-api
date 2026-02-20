"""
Pydantic Models for Meeting Data Contract (Tachles Summary)
Based on Master Specification v3.0 Data Contract
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================
# CRM Entities Models
# ============================================

class DealValueEntity(BaseModel):
    """Deal value entity extracted from transcript"""
    value: Optional[float] = Field(None, description="Deal value amount")
    currency: Optional[str] = Field(None, description="Currency code: ILS, USD, etc.")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0-1")
    source: Optional[str] = Field(None, description="Exact transcript snippet source")


class NextMeetingDateEntity(BaseModel):
    """Next meeting date entity"""
    value: Optional[str] = Field(None, description="ISO date string")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0-1")
    source: Optional[str] = Field(None, description="Exact transcript snippet source")


class ContactEmailEntity(BaseModel):
    """Contact email entity"""
    value: Optional[str] = Field(None, description="Email address")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0-1")
    source: Optional[str] = Field(None, description="Exact transcript snippet source")


class CRMEntities(BaseModel):
    """CRM entities extracted from transcript"""
    deal_value: Optional[DealValueEntity] = None
    next_meeting_date: Optional[NextMeetingDateEntity] = None
    contact_email: Optional[ContactEmailEntity] = None
    # Additional entities can be added here
    additional_entities: Optional[Dict[str, Any]] = None


# ============================================
# Action Items Model
# ============================================

class ActionItem(BaseModel):
    """Action item extracted from meeting"""
    task: str = Field(..., description="Task description (Hebrew/English)")
    due: Optional[str] = Field(None, description="ISO date string for due date")
    assignee: Optional[str] = Field(None, description="Person assigned (if mentioned)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    source: Optional[str] = Field(None, description="Transcript snippet source")


# ============================================
# Summary Content Model
# ============================================

class SummaryContent(BaseModel):
    """Content section of the Tachles summary"""
    summary_text: str = Field(..., description="Direct, bulleted Hebrew/English text (Tachles style)")
    action_items: List[ActionItem] = Field(default_factory=list)
    crm_entities: CRMEntities = Field(default_factory=CRMEntities)


# ============================================
# Metadata Model
# ============================================

class SummaryMetadata(BaseModel):
    """Metadata section of the summary"""
    org_id: str = Field(..., description="Organization UUID")
    rep_id: str = Field(..., description="Sales rep UUID")
    client_id: Optional[str] = Field(None, description="Client/contact UUID")
    language_mix: str = Field(..., description="Language mix: 'he-IL/en-US', 'he-IL', etc.")
    duration: Optional[int] = Field(None, description="Meeting duration in seconds")


# ============================================
# Governance Model
# ============================================

class SummaryGovernance(BaseModel):
    """Governance section for quality control"""
    feedback_loop_applied: bool = Field(default=False, description="Whether feedback loop was applied")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    hallucination_check: Optional[str] = Field(None, description="'passed', 'failed', 'pending'")
    requires_review: bool = Field(default=False, description="True if confidence < 0.7, requires human review")


# ============================================
# Complete Tachles Summary Model
# ============================================

class TachlesSummary(BaseModel):
    """
    Complete Tachles summary following the Data Contract from Master Spec v3.0
    This is the structured JSON output from the AI pipeline.
    """
    summary_id: str = Field(..., description="UUID of the meeting/summary")
    metadata: SummaryMetadata
    content: SummaryContent
    governance: SummaryGovernance

    class Config:
        json_schema_extra = {
            "example": {
                "summary_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {
                    "org_id": "123e4567-e89b-12d3-a456-426614174000",
                    "rep_id": "789e0123-e45b-67c8-d901-234567890abc",
                    "client_id": "abc12345-e67b-89c0-d123-4567890def01",
                    "language_mix": "he-IL/en-US",
                    "duration": 1200
                },
                "content": {
                    "summary_text": "• הלקוח מעוניין במוצר X\n• דדליין: סוף החודש\n• תקציב: 50,000 ₪",
                    "action_items": [
                        {
                            "task": "שלח הצעת מחיר עד יום רביעי",
                            "due": "2024-02-14",
                            "assignee": "דני",
                            "confidence": 0.95,
                            "source": "לקוח: 'אני צריך את זה עד יום רביעי'"
                        }
                    ],
                    "crm_entities": {
                        "deal_value": {
                            "value": 50000,
                            "currency": "ILS",
                            "confidence": 0.9,
                            "source": "לקוח: 'התקציב שלנו הוא 50 אלף שקל'"
                        }
                    }
                },
                "governance": {
                    "feedback_loop_applied": False,
                    "confidence_score": 0.92,
                    "hallucination_check": "passed"
                }
            }
        }


# ============================================
# Request/Response Models for API
# ============================================

class MeetingUploadRequest(BaseModel):
    """Request model for meeting upload (metadata only, file is multipart)"""
    org_id: str
    user_id: str
    client_name: Optional[str] = None
    client_id: Optional[str] = None


class MeetingUploadResponse(BaseModel):
    """Response model for meeting upload"""
    meeting_id: str
    status: str
    message: str
    transcript: Optional[str] = None
    summary: Optional[TachlesSummary] = None


class MeetingResponse(BaseModel):
    """Response model for meeting GET endpoints (flexible JSON fields)"""
    id: str
    org_id: str
    user_id: str
    client_name: Optional[str] = None
    client_id: Optional[str] = None
    title: Optional[str] = None
    status: str
    transcript: Optional[str] = None
    transcript_raw: Optional[Dict[str, Any]] = None  # Flexible JSON
    summary: Optional[Dict[str, Any]] = None  # Flexible JSON - TachlesSummary structure
    summary_text: Optional[str] = None
    processing_errors: Optional[Dict[str, Any]] = None  # Flexible JSON
    language_mix: Optional[str] = None
    duration_seconds: Optional[int] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    audio_url: Optional[str] = None
    audio_deleted_at: Optional[datetime] = None
    audio_deletion_scheduled_at: Optional[datetime] = None
    retention_policy_hours: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    approved_for_sync: Optional[bool] = None

    class Config:
        from_attributes = True  # Allow ORM mode for Prisma models
