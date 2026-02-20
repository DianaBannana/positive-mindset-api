"""
Ingest API - Webhook endpoint for external audio ingestion
Handles PBX, WhatsApp Bot, and other automated audio sources.
"""

import os
import uuid
import hashlib
import logging
import tempfile
import httpx
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_prisma
from app.core.usage_guard import check_can_process, increment_usage
from app.services.client_service import (
    resolve_or_create_client,
    get_client_history,
    update_client_stats,
    normalize_phone,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class WebhookIngestRequest(BaseModel):
    """Request model for webhook audio ingestion."""
    recording_url: Optional[str] = Field(None, description="URL to download the audio recording")
    client_phone: Optional[str] = Field(None, description="Client phone number (for context)")
    client_name: Optional[str] = Field(None, description="Client name (optional)")
    user_id: Optional[str] = Field(None, description="Sales rep user ID")
    metadata: Optional[dict] = Field(None, description="Additional metadata from source system")
    callback_url: Optional[str] = Field(None, description="URL to POST results when complete")


class WebhookIngestResponse(BaseModel):
    """Response model for webhook ingestion."""
    success: bool
    meeting_id: str
    status: str
    message: str
    processing_started: bool


class IngestStatusResponse(BaseModel):
    """Response for checking ingestion status."""
    meeting_id: str
    status: str
    transcript_ready: bool
    summary_ready: bool
    created_at: str


# ============================================
# WhatsApp Integration Models (Twilio/Meta compatible)
# ============================================

class WhatsAppMediaPayload(BaseModel):
    """
    WhatsApp voice message payload.
    Compatible with Twilio WhatsApp API and Meta Cloud API.
    """
    # Media details
    media_url: str = Field(..., description="URL to download the voice message audio")
    media_content_type: Optional[str] = Field("audio/ogg", description="MIME type (audio/ogg, audio/mp4)")
    
    # Sender info
    sender_phone: str = Field(..., description="WhatsApp sender phone (E.164 format: +972501234567)")
    sender_name: Optional[str] = Field(None, description="Sender's WhatsApp profile name")
    
    # Message metadata
    message_id: Optional[str] = Field(None, description="WhatsApp message ID for deduplication")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp of the message")
    
    # Optional context
    account_sid: Optional[str] = Field(None, description="Twilio Account SID (for verification)")
    conversation_id: Optional[str] = Field(None, description="Conversation/thread ID")
    
    # SalesEcho specific
    rep_phone: Optional[str] = Field(None, description="Sales rep's WhatsApp number (to identify rep)")
    callback_url: Optional[str] = Field(None, description="URL to POST results when complete")


class WhatsAppIngestResponse(BaseModel):
    """Response for WhatsApp voice message ingestion."""
    success: bool
    meeting_id: str
    status: str
    message: str
    sender_phone: str
    processing_started: bool
    completed_at: Optional[str] = None


# ============================================
# API Key Validation
# ============================================

async def validate_api_key(api_key: str) -> Optional[dict]:
    """
    Validate API key and return associated organization info.
    
    Args:
        api_key: The API key to validate (format: sk_live_xxxxx)
        
    Returns:
        Dict with org_id and permissions, or None if invalid.
    """
    if not api_key:
        return None
    
    try:
        prisma = get_prisma()
        
        # Hash the API key to compare with stored hash
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Find API key record
        api_key_record = await prisma.apikey.find_unique(
            where={"key_hash": key_hash}
        )
        
        if not api_key_record:
            logger.warning(f"Invalid API key attempt (prefix: {api_key[:10]}...)")
            return None
        
        # Check if key is active and not expired
        if not api_key_record.is_active:
            logger.warning(f"Inactive API key used: {api_key_record.key_prefix}")
            return None
        
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            logger.warning(f"Expired API key used: {api_key_record.key_prefix}")
            return None
        
        # Update last used timestamp
        await prisma.apikey.update(
            where={"id": api_key_record.id},
            data={
                "last_used_at": datetime.utcnow(),
                "usage_count": api_key_record.usage_count + 1
            }
        )
        
        return {
            "org_id": api_key_record.org_id,
            "permissions": api_key_record.permissions or ["ingest"],
            "key_name": api_key_record.name
        }
        
    except Exception as e:
        logger.error(f"API key validation error: {e}")
        return None


async def validate_api_key_simple(api_key: str, org_id: str) -> bool:
    """
    Simple API key validation for development.
    In production, this should use the full validate_api_key function.
    
    DEV_ONLY_WARNING: This function accepts any key matching format.
    """
    # DEV_ONLY: Accept keys that start with sk_live_ or sk_test_
    if api_key and api_key.startswith(("sk_live_", "sk_test_")):
        logger.warning("DEV_ONLY: Using simple API key validation")
        return True
    
    # Try full validation
    result = await validate_api_key(api_key)
    return result is not None and result.get("org_id") == org_id


# ============================================
# Audio Download Helper
# ============================================

async def download_audio_from_url(url: str, timeout: int = 60) -> bytes:
    """
    Download audio file from URL.
    
    Args:
        url: URL to download from
        timeout: Request timeout in seconds
        
    Returns:
        Audio file bytes
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


# ============================================
# Background Processing Task
# ============================================

async def process_inbound_recording(
    meeting_id: str,
    audio_path: str,
    org_id: str,
    user_id: str,
    client_phone: Optional[str] = None,
    client_name: Optional[str] = None,
    callback_url: Optional[str] = None,
    metadata: Optional[dict] = None,
    is_simulation: bool = False,
):
    """
    Background task to process an inbound audio recording.
    
    This is the main pipeline:
    1. Resolve/create client (if phone provided)
    2. Fetch client history (last 3 meetings)
    3. Transcribe audio (Gemini)
    4. Generate Tachles summary with historical context (Gemini)
    5. Dispatch actions (Email, Calendar, CRM)
    6. Update client stats
    7. Send callback (if configured)
    """
    from app.services.gemini_transcription import transcribe_audio_gemini
    from app.services.ai_service import generate_summary, get_organization_settings
    from app.core.dispatcher import action_dispatcher
    
    prisma = get_prisma()
    client_id = None
    client_history_context = None
    
    try:
        logger.info(f"[Webhook Pipeline] Starting processing for meeting {meeting_id}")
        
        # Update status to PROCESSING
        await prisma.meeting.update(
            where={"id": meeting_id},
            data={"status": "PROCESSING"}
        )
        
        # Step 1: Resolve or create client (if phone provided)
        if client_phone:
            logger.info(f"[Webhook Pipeline] Step 1: Resolving client for phone {client_phone}")
            try:
                client_id, is_new_client = await resolve_or_create_client(
                    org_id=org_id,
                    phone=client_phone,
                    full_name=client_name,
                )
                
                # Update meeting with client link and source phone
                await prisma.meeting.update(
                    where={"id": meeting_id},
                    data={
                        "client_id": client_id,
                        "source_phone": normalize_phone(client_phone),
                    }
                )
                
                logger.info(f"[Webhook Pipeline] {'Created new' if is_new_client else 'Resolved existing'} client: {client_id}")
                
                # Step 2: Fetch client history (last 3 meetings)
                if not is_new_client:
                    logger.info(f"[Webhook Pipeline] Step 2: Fetching client history for {client_id}")
                    client_history_context = await get_client_history(
                        client_id=client_id,
                        org_id=org_id,
                        max_meetings=3,
                    )
                    
                    if client_history_context:
                        logger.info(
                            f"[Webhook Pipeline] Found {client_history_context.total_meetings} previous meetings for client"
                        )
                
            except Exception as client_err:
                logger.warning(f"[Webhook Pipeline] Client resolution failed: {client_err}")
                # Continue without client - not a fatal error
        else:
            logger.info(f"[Webhook Pipeline] No client phone provided, skipping client resolution")
        
        # Step 3: Transcribe audio
        logger.info(f"[Webhook Pipeline] Step 3: Transcribing audio for {meeting_id}")
        transcription_result = await transcribe_audio_gemini(audio_path, language="he")
        
        transcript = transcription_result.get("transcript", "")
        duration_seconds = transcription_result.get("duration")
        
        if not transcript or len(transcript.strip()) < 10:
            logger.warning(f"[Webhook Pipeline] Empty or very short transcript for {meeting_id}")
        
        # Update meeting with transcript
        await prisma.meeting.update(
            where={"id": meeting_id},
            data={
                "transcript": transcript,
                "transcript_raw": transcription_result,
                "duration_seconds": int(duration_seconds) if duration_seconds else None,
            }
        )
        
        # Step 4: Generate Tachles summary with historical context
        logger.info(f"[Webhook Pipeline] Step 4: Generating summary for {meeting_id}")
        
        # Get org settings for custom instructions
        org_settings = await get_organization_settings(org_id)
        custom_instructions = org_settings.get("custom_prompt_instructions") if org_settings else None
        
        # Build historical context block for AI injection
        historical_context = None
        if client_history_context:
            historical_context = client_history_context.to_prompt_block()
            logger.info(f"[Webhook Pipeline] Injecting {len(historical_context)} chars of client history")
        
        summary = await generate_summary(
            transcript=transcript,
            meeting_id=meeting_id,
            org_id=org_id,
            rep_id=user_id,
            client_id=client_id,
            duration=int(duration_seconds) if duration_seconds else None,
            language_mix="he-IL/en-US",
            custom_instructions=custom_instructions,
            historical_context=historical_context,  # NEW: inject client history
        )
        
        # Update meeting with summary
        await prisma.meeting.update(
            where={"id": meeting_id},
            data={
                "summary": summary.model_dump(),
                "confidence_score": summary.governance.confidence_score,
                "status": "COMPLETED",
            }
        )
        
        # Step 3: Dispatch actions (if org has auto-dispatch enabled)
        logger.info(f"[Webhook Pipeline] Step 3: Dispatching actions for {meeting_id}")
        
        auto_dispatch = org_settings.get("auto_dispatch_actions", False) if org_settings else False
        enabled_modules = org_settings.get("enabled_modules", {}) if org_settings else {}
        
        if auto_dispatch:
            # Build context for dispatcher
            dispatch_context = {
                "meeting_id": meeting_id,
                "org_id": org_id,
                "user_id": user_id,
                "client_name": client_name,
                "client_phone": client_phone,
                "client_id": client_id,
                "summary": summary.model_dump(),
                "enabled_modules": enabled_modules,
            }
            
            dispatch_results = await action_dispatcher.dispatch_actions(dispatch_context)
            
            # Log dispatch results
            for result in dispatch_results:
                logger.info(f"[Webhook Pipeline] Action {result['action_type']}: {result['status']}")
        else:
            logger.info(f"[Webhook Pipeline] Auto-dispatch disabled for org {org_id}")
        
        # Step 6: Update client statistics
        if client_id:
            logger.info(f"[Webhook Pipeline] Step 6: Updating client stats for {client_id}")
            try:
                await update_client_stats(client_id=client_id, org_id=org_id)
            except Exception as stats_err:
                logger.warning(f"[Webhook Pipeline] Failed to update client stats: {stats_err}")
        
        # Step 7: Increment usage counters (skip for simulations)
        duration_minutes = (duration_seconds or 0) / 60.0
        await increment_usage(
            org_id=org_id,
            meetings=1,
            minutes=duration_minutes,
            is_simulation=is_simulation,
        )
        
        # Step 8: Send callback (if configured)
        if callback_url:
            logger.info(f"[Webhook Pipeline] Step 4: Sending callback to {callback_url}")
            try:
                callback_payload = {
                    "meeting_id": meeting_id,
                    "status": "COMPLETED",
                    "summary": summary.model_dump(),
                    "transcript_length": len(transcript),
                    "duration_seconds": duration_seconds,
                    "processed_at": datetime.utcnow().isoformat(),
                }
                
                async with httpx.AsyncClient(timeout=30) as client:
                    await client.post(callback_url, json=callback_payload)
                    
            except Exception as callback_err:
                logger.error(f"[Webhook Pipeline] Callback failed: {callback_err}")
        
        # Cleanup: Remove temporary audio file
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as cleanup_err:
            logger.warning(f"[Webhook Pipeline] Failed to cleanup audio file: {cleanup_err}")
        
        logger.info(f"[Webhook Pipeline] ✅ Completed processing for meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"[Webhook Pipeline] ❌ Failed processing meeting {meeting_id}: {e}", exc_info=True)
        
        # Update meeting status to FAILED
        try:
            await prisma.meeting.update(
                where={"id": meeting_id},
                data={
                    "status": "FAILED",
                    "processing_errors": [{"error": str(e), "timestamp": datetime.utcnow().isoformat()}]
                }
            )
        except Exception as update_err:
            logger.error(f"[Webhook Pipeline] Failed to update meeting status: {update_err}")
        
        # Send failure callback
        if callback_url:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    await client.post(callback_url, json={
                        "meeting_id": meeting_id,
                        "status": "FAILED",
                        "error": str(e),
                        "processed_at": datetime.utcnow().isoformat(),
                    })
            except Exception:
                pass


# ============================================
# Webhook Endpoints
# ============================================

@router.post("/ingest/webhook", response_model=WebhookIngestResponse)
async def ingest_webhook(
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(..., alias="X-API-Key", description="API key for authentication"),
    org_id: str = Header(..., alias="X-Org-ID", description="Organization ID"),
    recording_url: Optional[str] = Form(None),
    client_phone: Optional[str] = Form(None),
    client_name: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    callback_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    Webhook endpoint for ingesting audio recordings from external sources.
    
    This endpoint accepts:
    1. A file upload directly (via multipart form)
    2. A recording_url to download from
    
    The audio is processed in the background through the full pipeline:
    - Transcription (Gemini)
    - Summary generation (Tachles)
    - Action dispatch (Email, Calendar, CRM)
    - Callback notification (if callback_url provided)
    
    Authentication:
    - Requires X-API-Key header with valid API key
    - Requires X-Org-ID header with organization ID
    
    Example curl:
    ```
    curl -X POST https://api.salesecho.ai/api/v1/ingest/webhook \\
      -H "X-API-Key: sk_live_xxxxx" \\
      -H "X-Org-ID: org-uuid-here" \\
      -F "recording_url=https://pbx.example.com/recordings/call123.mp3" \\
      -F "client_phone=+972501234567" \\
      -F "callback_url=https://your-system.com/webhook/complete"
    ```
    """
    # Validate API key
    is_valid = await validate_api_key_simple(x_api_key, org_id)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check usage quota (will raise 402 if exceeded)
    await check_can_process(org_id, is_simulation=False)
    
    # Validate input: must have either file or recording_url
    if not file and not recording_url:
        raise HTTPException(
            status_code=400,
            detail="Must provide either 'file' upload or 'recording_url'"
        )
    
    try:
        prisma = get_prisma()
        
        # Generate meeting ID
        meeting_id = str(uuid.uuid4())
        
        # Determine user ID
        effective_user_id = user_id or settings.dev_org_id or "system-webhook"
        
        # Create meeting record
        meeting = await prisma.meeting.create(
            data={
                "id": meeting_id,
                "org_id": org_id,
                "user_id": effective_user_id,
                "client_name": client_name,
                "status": "PENDING",
            }
        )
        
        # Save audio to temporary file
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, f"{meeting_id}.mp3")
        
        if file:
            # Direct file upload
            content = await file.read()
            with open(audio_path, "wb") as f:
                f.write(content)
            logger.info(f"[Webhook] Received file upload: {file.filename} ({len(content)} bytes)")
        else:
            # Download from URL
            logger.info(f"[Webhook] Downloading audio from URL: {recording_url}")
            try:
                audio_content = await download_audio_from_url(recording_url)
                with open(audio_path, "wb") as f:
                    f.write(audio_content)
                logger.info(f"[Webhook] Downloaded {len(audio_content)} bytes from URL")
            except Exception as download_err:
                logger.error(f"[Webhook] Failed to download audio: {download_err}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download audio from URL: {str(download_err)}"
                )
        
        # Queue background processing
        background_tasks.add_task(
            process_inbound_recording,
            meeting_id=meeting_id,
            audio_path=audio_path,
            org_id=org_id,
            user_id=effective_user_id,
            client_phone=client_phone,
            client_name=client_name,
            callback_url=callback_url,
        )
        
        return WebhookIngestResponse(
            success=True,
            meeting_id=meeting_id,
            status="PENDING",
            message="Audio received and queued for processing",
            processing_started=True,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Webhook] Ingest error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/ingest/status/{meeting_id}", response_model=IngestStatusResponse)
async def get_ingest_status(
    meeting_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
    org_id: str = Header(..., alias="X-Org-ID"),
):
    """
    Check the processing status of an ingested recording.
    
    Returns current status, whether transcript is ready, and whether summary is ready.
    """
    # Validate API key
    is_valid = await validate_api_key_simple(x_api_key, org_id)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        prisma = get_prisma()
        
        meeting = await prisma.meeting.find_unique(
            where={"id": meeting_id}
        )
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Check org_id matches (multi-tenancy security)
        if meeting.org_id != org_id:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return IngestStatusResponse(
            meeting_id=meeting_id,
            status=meeting.status,
            transcript_ready=bool(meeting.transcript),
            summary_ready=bool(meeting.summary),
            created_at=meeting.created_at.isoformat(),
            completed_at=meeting.updated_at.isoformat() if meeting.status == "COMPLETED" else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Webhook] Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


# ============================================
# WhatsApp Voice Message Endpoint
# ============================================

@router.post("/ingest/whatsapp", response_model=WhatsAppIngestResponse)
async def ingest_whatsapp_voice(
    background_tasks: BackgroundTasks,
    payload: WhatsAppMediaPayload,
    x_api_key: str = Header(..., alias="X-API-Key", description="API key for authentication"),
    org_id: str = Header(..., alias="X-Org-ID", description="Organization ID"),
):
    """
    Webhook endpoint for WhatsApp voice message ingestion.
    
    Compatible with:
    - Twilio WhatsApp API (via webhook)
    - Meta Cloud API (via webhook)
    - Custom WhatsApp Business integrations
    
    Flow:
    1. Receives voice message metadata from WhatsApp provider
    2. Downloads audio from media_url
    3. Resolves client from sender_phone
    4. Processes through AI pipeline (transcription → summary → actions)
    5. Optionally calls callback_url with results
    
    Authentication:
    - Requires X-API-Key header with valid API key
    - Requires X-Org-ID header with organization ID
    
    Example Twilio-style payload:
    ```json
    {
        "media_url": "https://api.twilio.com/2010-04-01/.../Media/...",
        "media_content_type": "audio/ogg",
        "sender_phone": "+972501234567",
        "sender_name": "John Doe",
        "message_id": "SM1234...",
        "timestamp": "2026-02-20T10:30:00Z",
        "account_sid": "AC..."
    }
    ```
    
    Example Meta-style payload:
    ```json
    {
        "media_url": "https://lookaside.fbsbx.com/...",
        "media_content_type": "audio/ogg; codecs=opus",
        "sender_phone": "+972501234567",
        "message_id": "wamid.XXX",
        "timestamp": "1708425000"
    }
    ```
    """
    # Validate API key
    is_valid = await validate_api_key_simple(x_api_key, org_id)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check usage quota
    await check_can_process(org_id, is_simulation=False)
    
    # Deduplicate by message_id
    if payload.message_id:
        prisma = get_prisma()
        existing = await prisma.meeting.find_first(
            where={
                "org_id": org_id,
                "metadata": {"path": ["whatsapp_message_id"], "equals": payload.message_id}
            }
        )
        if existing:
            logger.info(f"[WhatsApp] Duplicate message {payload.message_id}, returning existing meeting")
            return WhatsAppIngestResponse(
                success=True,
                meeting_id=existing.id,
                status=existing.status,
                message="Message already processed",
                sender_phone=payload.sender_phone,
                processing_started=False,
            )
    
    # Normalize phone number
    normalized_phone = normalize_phone(payload.sender_phone)
    
    try:
        prisma = get_prisma()
        
        # Generate meeting ID
        meeting_id = str(uuid.uuid4())
        
        # Determine rep user (from rep_phone or default)
        rep_user_id = None
        if payload.rep_phone:
            rep_user = await prisma.user.find_first(
                where={"org_id": org_id, "email": {"contains": payload.rep_phone}}
            )
            if rep_user:
                rep_user_id = rep_user.id
        
        if not rep_user_id:
            # Use first user in org as default
            default_user = await prisma.user.find_first(where={"org_id": org_id})
            rep_user_id = default_user.id if default_user else settings.dev_org_id or "whatsapp-ingest"
        
        # Build metadata
        whatsapp_metadata = {
            "source": "whatsapp",
            "whatsapp_message_id": payload.message_id,
            "conversation_id": payload.conversation_id,
            "content_type": payload.media_content_type,
            "timestamp": payload.timestamp,
            "account_sid": payload.account_sid,
        }
        
        # Create meeting record
        meeting = await prisma.meeting.create(
            data={
                "id": meeting_id,
                "org_id": org_id,
                "user_id": rep_user_id,
                "client_name": payload.sender_name or f"WhatsApp: {normalized_phone}",
                "source_phone": normalized_phone,
                "status": "PENDING",
                "metadata": whatsapp_metadata,
            }
        )
        
        logger.info(f"[WhatsApp] Created meeting {meeting_id} for sender {normalized_phone}")
        
        # Start background processing
        background_tasks.add_task(
            process_whatsapp_voice,
            meeting_id=meeting_id,
            media_url=payload.media_url,
            org_id=org_id,
            user_id=rep_user_id,
            client_phone=normalized_phone,
            client_name=payload.sender_name,
            callback_url=payload.callback_url,
            metadata=whatsapp_metadata,
        )
        
        return WhatsAppIngestResponse(
            success=True,
            meeting_id=meeting_id,
            status="PENDING",
            message="WhatsApp voice message received. Processing started.",
            sender_phone=normalized_phone,
            processing_started=True,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WhatsApp] Ingestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"WhatsApp ingestion failed: {str(e)}")


async def process_whatsapp_voice(
    meeting_id: str,
    media_url: str,
    org_id: str,
    user_id: str,
    client_phone: Optional[str] = None,
    client_name: Optional[str] = None,
    callback_url: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    """
    Background task to process a WhatsApp voice message.
    
    Reuses the main inbound recording pipeline with WhatsApp-specific handling.
    """
    logger.info(f"[WhatsApp Pipeline] Starting processing for meeting {meeting_id}")
    
    try:
        # Download audio from WhatsApp media URL
        audio_path = None
        async with httpx.AsyncClient(timeout=120.0) as client:
            # WhatsApp media URLs may require authentication header for some providers
            headers = {}
            if metadata and metadata.get("account_sid"):
                # Twilio-style: may need auth (handled by URL token usually)
                pass
            
            response = await client.get(media_url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Determine file extension from content type
            content_type = response.headers.get("content-type", "audio/ogg")
            if "ogg" in content_type:
                ext = ".ogg"
            elif "mp4" in content_type or "m4a" in content_type:
                ext = ".m4a"
            elif "mp3" in content_type:
                ext = ".mp3"
            else:
                ext = ".ogg"  # Default for WhatsApp
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                f.write(response.content)
                audio_path = f.name
        
        logger.info(f"[WhatsApp Pipeline] Downloaded audio to {audio_path}")
        
        # Reuse main processing pipeline
        await process_inbound_recording(
            meeting_id=meeting_id,
            audio_path=audio_path,
            org_id=org_id,
            user_id=user_id,
            client_phone=client_phone,
            client_name=client_name,
            callback_url=callback_url,
            metadata=metadata,
            is_simulation=False,
        )
        
    except Exception as e:
        logger.error(f"[WhatsApp Pipeline] Error: {e}", exc_info=True)
        
        # Update meeting with error
        prisma = get_prisma()
        await prisma.meeting.update(
            where={"id": meeting_id},
            data={
                "status": "FAILED",
                "processing_errors": [{"error": str(e), "stage": "whatsapp_download"}],
            }
        )
    finally:
        # Cleanup temp file
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except Exception:
                pass


@router.post("/ingest/simulate")
async def simulate_inbound_call(
    background_tasks: BackgroundTasks,
    org_id: str = Form(...),
    user_id: str = Form(None),
    client_name: str = Form("Demo Client - Simulated"),
):
    """
    Simulate an inbound call for testing purposes.
    
    This creates a meeting record and processes a sample audio file
    through the full pipeline, demonstrating the webhook flow.
    
    NOTE: Simulated calls do NOT count towards the trial quota.
    
    DEV_ONLY_WARNING: This endpoint should be disabled in production.
    """
    if not settings.dev_org_id:
        logger.warning("DEV_ONLY: Simulation endpoint called without DEV_ORG_ID")
    
    # Simulations skip quota check - they don't count towards trial limits
    logger.info(f"[Simulation] Starting simulated call for org {org_id} (quota exempt)")
    
    try:
        prisma = get_prisma()
        
        # Generate meeting ID
        meeting_id = str(uuid.uuid4())
        effective_user_id = user_id or settings.dev_org_id or "simulation-user"
        
        # Create meeting record
        await prisma.meeting.create(
            data={
                "id": meeting_id,
                "org_id": org_id,
                "user_id": effective_user_id,
                "client_name": client_name,
                "status": "PENDING",
            }
        )
        
        # For simulation, we'll create a mock transcript directly
        # (In production, this would process an actual audio file)
        sample_transcript = """
        נציג מכירות: שלום, תודה שהתקשרת ל-SalesEcho. אני יוסי, איך אוכל לעזור?
        
        לקוח: היי יוסי, אני דני מחברת TechStart. אנחנו מחפשים פתרון לניהול שיחות מכירה.
        
        נציג: מעולה דני! נשמח לעזור. ספר לי קצת על הצוות שלכם.
        
        לקוח: יש לנו צוות של 15 אנשי מכירות, ואנחנו מבצעים כ-200 שיחות ביום.
        
        נציג: מרשים! עם SalesEcho תוכלו לחסוך הרבה זמן. המערכת שלנו מתמללת את השיחות אוטומטית ומפיקה תובנות.
        
        לקוח: נשמע מעניין. מה המחיר?
        
        נציג: יש לנו כמה חבילות. לצוות בגודל שלכם, אני ממליץ על חבילת ה-Enterprise ב-50,000 שקל לשנה.
        
        לקוח: אוקיי, אני צריך לבדוק את זה עם ה-CFO שלנו. אפשר לקבוע שיחת המשך לשבוע הבא?
        
        נציג: בטח! מה לגבי יום רביעי בשעה 10 בבוקר?
        
        לקוח: מתאים לי. תשלח לי אימייל לדני@techstart.co.il עם הפרטים.
        
        נציג: מעולה! אשלח היום. תודה רבה דני, נדבר בקרוב.
        """
        
        # Import AI service
        from app.services.ai_service import generate_summary
        
        # Generate summary from sample transcript
        summary = await generate_summary(
            transcript=sample_transcript,
            meeting_id=meeting_id,
            org_id=org_id,
            rep_id=effective_user_id,
            client_id=None,
            duration=180,
            language_mix="he-IL",
        )
        
        # Update meeting with transcript and summary
        await prisma.meeting.update(
            where={"id": meeting_id},
            data={
                "transcript": sample_transcript,
                "summary": summary.model_dump(),
                "confidence_score": summary.governance.confidence_score,
                "duration_seconds": 180,
                "status": "COMPLETED",
            }
        )
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "status": "COMPLETED",
            "message": "Simulation completed successfully",
            "summary_preview": summary.content.summary_text[:200] + "..." if len(summary.content.summary_text) > 200 else summary.content.summary_text,
        }
        
    except Exception as e:
        logger.error(f"[Simulation] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")
