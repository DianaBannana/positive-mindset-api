# SalesEcho AI - Ingestion Strategy

**Version:** 1.0  
**Date:** February 2025  
**Status:** Technical Specification

---

## Executive Summary

This document outlines the technical requirements and implementation strategy for SalesEcho AI's multi-channel audio ingestion infrastructure. The system is designed to capture sales conversations from various sources and process them through our AI analysis pipeline.

### Supported Ingestion Channels

| Channel | Priority | Status | Description |
|---------|----------|--------|-------------|
| **Manual Upload** | P0 | ✅ Implemented | Web UI drag-and-drop upload |
| **Generic Webhook** | P0 | ✅ Implemented | Universal API for any source |
| **WhatsApp Bot** | P1 | 🔵 Planned | Voice notes & call recordings |
| **PBX Webhooks** | P1 | 🔵 Planned | Direct PBX integration |
| **Meeting Bot** | P2 | 🔵 Planned | Zoom/Teams/Meet bots |
| **Mobile App** | P3 | 🔵 Planned | Native recording app |

---

## 0. Live Webhook API (✅ IMPLEMENTED)

### 0.1 Overview

The Generic Webhook API provides a universal endpoint for external systems to submit audio recordings. This is the primary integration point for PBX systems, CTI platforms, and custom automation.

### 0.2 Endpoint Specification

```
POST /api/v1/ingest/webhook
```

#### Headers (Required)

| Header | Description | Example |
|--------|-------------|---------|
| `X-API-Key` | Organization API key | `sk_live_abc123...` |
| `X-Org-ID` | Organization UUID | `4eda10d2-761b-...` |

#### Request Body (Multipart Form)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | *Either | Direct audio file upload |
| `recording_url` | String | *Either | URL to download recording from |
| `client_phone` | String | No | Client phone number |
| `client_name` | String | No | Client name |
| `user_id` | String | No | Sales rep user ID |
| `callback_url` | String | No | Webhook to POST results to |

*Must provide either `file` or `recording_url`

#### Response

```json
{
  "success": true,
  "meeting_id": "uuid-of-created-meeting",
  "status": "PENDING",
  "message": "Audio received and queued for processing",
  "processing_started": true
}
```

### 0.3 Example Usage

#### cURL - File Upload

```bash
curl -X POST https://api.salesecho.ai/api/v1/ingest/webhook \
  -H "X-API-Key: sk_live_your_key_here" \
  -H "X-Org-ID: your-org-uuid" \
  -F "file=@/path/to/recording.mp3" \
  -F "client_phone=+972501234567" \
  -F "client_name=Demo Client" \
  -F "callback_url=https://your-system.com/webhook/complete"
```

#### cURL - URL Download

```bash
curl -X POST https://api.salesecho.ai/api/v1/ingest/webhook \
  -H "X-API-Key: sk_live_your_key_here" \
  -H "X-Org-ID: your-org-uuid" \
  -F "recording_url=https://pbx.example.com/recordings/call_123.mp3" \
  -F "client_phone=+972501234567" \
  -F "callback_url=https://your-system.com/webhook/complete"
```

#### Python SDK

```python
import httpx

async def submit_recording(audio_path: str, org_id: str, api_key: str):
    async with httpx.AsyncClient() as client:
        with open(audio_path, "rb") as f:
            response = await client.post(
                "https://api.salesecho.ai/api/v1/ingest/webhook",
                headers={
                    "X-API-Key": api_key,
                    "X-Org-ID": org_id,
                },
                files={"file": f},
                data={
                    "client_phone": "+972501234567",
                    "callback_url": "https://your-system.com/webhook/complete",
                },
            )
    return response.json()
```

### 0.4 Processing Pipeline

When a recording is submitted via webhook, the following pipeline executes:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Webhook       │     │   Audio         │     │   Transcription │
│   Receive       │────▶│   Download      │────▶│   (Gemini)      │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Callback      │◀────│   Action        │◀────│   Summary       │
│   Notification  │     │   Dispatch      │     │   Generation    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Pipeline Steps:**

1. **Receive**: Validate API key, accept file or download from URL
2. **Store**: Save audio to temporary storage
3. **Transcribe**: Process audio with Gemini 1.5 Flash (Hebrew/English)
4. **Summarize**: Generate Tachles summary with action items, CRM entities
5. **Dispatch**: If org has `auto_dispatch_actions` enabled, trigger Email/Calendar/CRM
6. **Callback**: POST results to `callback_url` if provided

### 0.5 Callback Payload

When processing completes, SalesEcho POSTs to your `callback_url`:

**Success:**
```json
{
  "meeting_id": "uuid",
  "status": "COMPLETED",
  "summary": {
    "summary_id": "uuid",
    "content": {
      "summary_text": "...",
      "action_items": [...],
      "crm_entities": {...}
    },
    "governance": {
      "confidence_score": 0.85,
      "requires_review": false
    }
  },
  "transcript_length": 1523,
  "duration_seconds": 180,
  "processed_at": "2025-02-20T14:30:00Z"
}
```

**Failure:**
```json
{
  "meeting_id": "uuid",
  "status": "FAILED",
  "error": "Transcription failed: Audio too short",
  "processed_at": "2025-02-20T14:30:00Z"
}
```

### 0.6 Status Check Endpoint

Poll processing status:

```
GET /api/v1/ingest/status/{meeting_id}
```

**Response:**
```json
{
  "meeting_id": "uuid",
  "status": "COMPLETED",
  "transcript_ready": true,
  "summary_ready": true,
  "created_at": "2025-02-20T14:00:00Z",
  "completed_at": "2025-02-20T14:02:30Z"
}
```

### 0.7 Simulation Endpoint

For testing without real audio:

```
POST /api/v1/ingest/simulate
```

**Request:**
```bash
curl -X POST https://api.salesecho.ai/api/v1/ingest/simulate \
  -F "org_id=your-org-uuid" \
  -F "client_name=Demo Client - Test Call"
```

**Response:**
```json
{
  "success": true,
  "meeting_id": "uuid",
  "status": "COMPLETED",
  "message": "Simulation completed successfully",
  "summary_preview": "סיכום שיחת מכירה עם Demo Client..."
}
```

### 0.8 API Key Management

API keys are stored securely with SHA-256 hashing:

```python
# Generate API key
import secrets
import hashlib

def generate_api_key(org_id: str) -> tuple[str, str]:
    """Generate new API key and its hash."""
    key = f"sk_live_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:10]
    return key, key_hash, key_prefix
```

**Key Format:** `sk_live_` + 32 random characters

### 0.9 Organization Settings

Each organization can configure:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `custom_prompt_instructions` | Text | null | Custom AI analysis rules |
| `enabled_modules` | JSON | All enabled | Which actions to dispatch |
| `auto_dispatch_actions` | Boolean | false | Auto-execute detected actions |
| `require_approval` | Boolean | true | Human approval before CRM sync |
| `audio_retention_hours` | Integer | 24 | Hours to keep audio files |
| `callback_url` | String | null | Default callback URL |
| `webhook_secret` | String | null | HMAC secret for validation |

**Custom Prompt Example:**

```
Focus on identifying technical objections and concerns.
Always extract budget and timeline information.
Flag any mentions of competitor products.
For real estate deals, extract property addresses and sizes.
```

---

## 1. WhatsApp Bot Integration

### 1.1 Overview

WhatsApp Business API integration enables automatic capture of voice notes and forwarded call recordings from sales reps.

### 1.2 Technical Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   WhatsApp      │     │   Webhook       │     │   SalesEcho     │
│   Business API  │────▶│   Receiver      │────▶│   Pipeline      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Media         │
                        │   Download      │
                        └─────────────────┘
```

### 1.3 Implementation Requirements

#### 1.3.1 WhatsApp Business API Setup

```yaml
# Required Configuration
whatsapp:
  api_version: "v18.0"
  phone_number_id: "${WHATSAPP_PHONE_NUMBER_ID}"
  business_account_id: "${WHATSAPP_BUSINESS_ACCOUNT_ID}"
  access_token: "${WHATSAPP_ACCESS_TOKEN}"
  webhook_verify_token: "${WHATSAPP_WEBHOOK_VERIFY_TOKEN}"
```

#### 1.3.2 Webhook Endpoint

```python
# app/api/v1/webhooks/whatsapp.py

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import hmac
import hashlib

router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp Webhook"])

@router.get("")
async def verify_webhook(
    hub_mode: str,
    hub_verify_token: str,
    hub_challenge: str,
):
    """Verify webhook registration with WhatsApp."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("")
async def receive_message(request: Request):
    """
    Receive incoming WhatsApp messages.
    
    Handles:
    - Voice notes (audio/ogg)
    - Audio messages (audio/*)
    - Forwarded recordings
    """
    body = await request.json()
    
    # Validate signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(await request.body(), signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process messages
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") == "messages":
                messages = change.get("value", {}).get("messages", [])
                for message in messages:
                    if message.get("type") == "audio":
                        await process_audio_message(message)
    
    return {"status": "ok"}

async def process_audio_message(message: Dict[str, Any]):
    """Download and process audio from WhatsApp."""
    audio_id = message.get("audio", {}).get("id")
    sender = message.get("from")
    
    # Download media
    media_url = await get_media_url(audio_id)
    audio_data = await download_media(media_url)
    
    # Create meeting record and process
    meeting = await create_meeting_from_whatsapp(
        sender_phone=sender,
        audio_data=audio_data,
    )
    
    # Trigger processing pipeline
    await process_meeting_async(meeting.id)
```

#### 1.3.3 Supported Audio Formats

| Format | MIME Type | Support |
|--------|-----------|---------|
| Opus (Voice Notes) | audio/ogg; codecs=opus | ✅ Primary |
| AAC | audio/aac | ✅ |
| MP3 | audio/mpeg | ✅ |
| AMR | audio/amr | ✅ |

#### 1.3.4 User Mapping Strategy

```python
# Map WhatsApp numbers to SalesEcho users
async def resolve_user_from_phone(phone_number: str) -> Optional[User]:
    """
    Resolve SalesEcho user from WhatsApp phone number.
    
    Strategy:
    1. Exact match in users.phone_number
    2. Fuzzy match with country code normalization
    3. Create placeholder user if auto_create enabled
    """
    # Normalize phone number
    normalized = normalize_phone(phone_number, default_country="IL")
    
    # Lookup user
    user = await prisma.user.find_first(
        where={"phone_number": normalized}
    )
    
    if not user and settings.auto_create_whatsapp_users:
        user = await prisma.user.create(
            data={
                "phone_number": normalized,
                "source": "whatsapp_bot",
                "status": "pending_activation",
            }
        )
    
    return user
```

### 1.4 Security Considerations

- **Signature Verification**: All webhooks must verify `X-Hub-Signature-256`
- **Rate Limiting**: Implement per-sender rate limits (10 messages/minute)
- **Data Retention**: Audio files deleted after processing (configurable)
- **Encryption**: TLS 1.3 required for all webhook endpoints

---

## 2. PBX Webhooks Integration

### 2.1 Overview

Direct integration with PBX/VoIP systems enables automatic capture of all inbound and outbound sales calls.

### 2.2 Supported PBX Systems

| System | Integration Type | Status |
|--------|------------------|--------|
| **Asterisk** | AMI Events + Recording | 🔵 Planned |
| **FreePBX** | REST API + CDR | 🔵 Planned |
| **3CX** | Webhook + API | 🔵 Planned |
| **Voicenter** | REST API | 🔵 Planned |
| **Twilio** | Recording Webhook | 🔵 Planned |
| **Vonage** | Events API | 🔵 Planned |

### 2.3 Generic Webhook Specification

#### 2.3.1 Webhook Endpoint

```python
# app/api/v1/webhooks/pbx.py

from fastapi import APIRouter, Request, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/webhooks/pbx", tags=["PBX Webhook"])

class PBXCallEvent(BaseModel):
    """Standardized PBX call event."""
    event_type: str  # "call_started", "call_ended", "recording_ready"
    call_id: str
    caller_number: str
    callee_number: str
    direction: str  # "inbound", "outbound"
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    pbx_system: str  # "asterisk", "3cx", "twilio", etc.
    metadata: dict = {}

@router.post("/{org_id}")
async def receive_pbx_event(
    org_id: str,
    event: PBXCallEvent,
    x_pbx_signature: str = Header(...),
):
    """
    Receive PBX call events.
    
    Triggered when:
    1. Call starts (for real-time tracking)
    2. Call ends (for duration update)
    3. Recording ready (for processing)
    """
    # Validate signature
    if not verify_pbx_signature(org_id, event, x_pbx_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    if event.event_type == "recording_ready":
        # Download and process recording
        await process_pbx_recording(org_id, event)
    elif event.event_type == "call_ended":
        # Update call metadata
        await update_call_metadata(org_id, event)
    
    return {"status": "received", "call_id": event.call_id}

async def process_pbx_recording(org_id: str, event: PBXCallEvent):
    """Download PBX recording and create meeting."""
    # Download recording
    audio_data = await download_pbx_recording(
        event.recording_url,
        pbx_system=event.pbx_system,
    )
    
    # Resolve user from caller/callee
    user = await resolve_user_from_phone(
        event.caller_number if event.direction == "outbound" else event.callee_number
    )
    
    # Create meeting
    meeting = await prisma.meeting.create(
        data={
            "org_id": org_id,
            "user_id": user.id if user else None,
            "client_name": None,  # To be extracted from CRM
            "source": f"pbx_{event.pbx_system}",
            "status": "PENDING",
            "metadata": Json({
                "call_id": event.call_id,
                "direction": event.direction,
                "caller": event.caller_number,
                "callee": event.callee_number,
            }),
        }
    )
    
    # Trigger processing
    await enqueue_meeting_processing(meeting.id, audio_data)
```

#### 2.3.2 Asterisk Integration Example

```ini
# /etc/asterisk/extensions.conf

[recording-handler]
exten => h,1,NoOp(Call ended: ${CDR(uniqueid)})
exten => h,n,Set(RECORDING_FILE=/var/spool/asterisk/monitor/${CDR(uniqueid)}.wav)
exten => h,n,AGI(salesecho_upload.py,${RECORDING_FILE},${CALLERID(num)},${EXTEN})
```

```python
#!/usr/bin/env python3
# /var/lib/asterisk/agi-bin/salesecho_upload.py

import sys
import requests

def upload_recording(recording_path, caller, callee):
    with open(recording_path, 'rb') as f:
        response = requests.post(
            f"{SALESECHO_API}/webhooks/pbx/{ORG_ID}",
            files={"recording": f},
            data={
                "event_type": "recording_ready",
                "call_id": recording_path.split("/")[-1].replace(".wav", ""),
                "caller_number": caller,
                "callee_number": callee,
                "direction": "outbound",
                "pbx_system": "asterisk",
            },
            headers={"X-PBX-Signature": generate_signature(...)},
        )
    return response.status_code == 200

if __name__ == "__main__":
    upload_recording(sys.argv[1], sys.argv[2], sys.argv[3])
```

### 2.4 Data Flow

```
┌─────────────────┐
│   PBX System    │
│  (Call Ends)    │
└────────┬────────┘
         │ Webhook
         ▼
┌─────────────────┐     ┌─────────────────┐
│   SalesEcho     │     │   Recording     │
│   Webhook API   │────▶│   Storage       │
└────────┬────────┘     │   (S3/Supabase) │
         │              └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   User/Client   │     │   Transcription │
│   Resolution    │     │   Pipeline      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
             ┌─────────────────┐
             │   AI Summary    │
             │   Generation    │
             └─────────────────┘
```

---

## 3. Meeting Bot Integration (Zoom/Teams/Meet)

### 3.1 Overview

Meeting bots automatically join scheduled meetings, record audio, and process conversations.

### 3.2 Supported Platforms

| Platform | Bot Type | Status |
|----------|----------|--------|
| **Zoom** | Native Bot SDK | 🔵 Planned |
| **Microsoft Teams** | Graph API Bot | 🔵 Planned |
| **Google Meet** | Calendar Integration | 🔵 Planned |

### 3.3 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Calendar      │     │   Bot           │     │   Meeting       │
│   Integration   │────▶│   Scheduler     │────▶│   Platform      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               │                        │ Audio Stream
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Meeting       │◀────│   Recording     │
                        │   Record        │     │   Bot           │
                        └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   AI Pipeline   │
                        └─────────────────┘
```

### 3.4 Zoom Integration

#### 3.4.1 Bot Registration

```yaml
# Zoom App Configuration
zoom_bot:
  client_id: "${ZOOM_CLIENT_ID}"
  client_secret: "${ZOOM_CLIENT_SECRET}"
  bot_jid: "${ZOOM_BOT_JID}"
  verification_token: "${ZOOM_VERIFICATION_TOKEN}"
  
  permissions:
    - meeting:read
    - meeting:write
    - recording:read
    - user:read
```

#### 3.4.2 Meeting Join Flow

```python
# app/services/meeting_bot.py

from zoom_sdk import ZoomClient
from datetime import datetime, timedelta

class ZoomMeetingBot:
    """Zoom meeting bot for automatic recording."""
    
    def __init__(self):
        self.client = ZoomClient(
            client_id=settings.zoom_client_id,
            client_secret=settings.zoom_client_secret,
        )
    
    async def schedule_bot_join(
        self,
        meeting_id: str,
        join_time: datetime,
        org_id: str,
    ):
        """
        Schedule bot to join a Zoom meeting.
        
        Args:
            meeting_id: Zoom meeting ID
            join_time: When to join (usually meeting start - 1 min)
            org_id: Organization ID for the recording
        """
        # Create scheduled task
        await create_scheduled_task(
            task_type="zoom_bot_join",
            execute_at=join_time - timedelta(minutes=1),
            payload={
                "meeting_id": meeting_id,
                "org_id": org_id,
            },
        )
    
    async def join_meeting(self, meeting_id: str):
        """Join a Zoom meeting and start recording."""
        # Get meeting details
        meeting = await self.client.get_meeting(meeting_id)
        
        # Join as bot
        join_url = await self.client.get_bot_join_url(
            meeting_id=meeting_id,
            bot_name="SalesEcho Notetaker",
        )
        
        # Start recording
        await self.client.start_cloud_recording(meeting_id)
        
        return join_url
    
    async def handle_recording_completed(
        self,
        meeting_id: str,
        recording_url: str,
        org_id: str,
    ):
        """Process completed Zoom recording."""
        # Download recording
        audio_data = await self.client.download_recording(recording_url)
        
        # Create meeting record
        meeting = await prisma.meeting.create(
            data={
                "org_id": org_id,
                "source": "zoom_bot",
                "status": "PENDING",
                "metadata": Json({
                    "zoom_meeting_id": meeting_id,
                    "recording_url": recording_url,
                }),
            }
        )
        
        # Process
        await enqueue_meeting_processing(meeting.id, audio_data)
```

#### 3.4.3 Calendar Integration

```python
# app/services/calendar_sync.py

async def sync_calendar_meetings(user_id: str, calendar_provider: str):
    """
    Sync upcoming meetings from user's calendar.
    
    Automatically schedules bot joins for sales-related meetings.
    """
    if calendar_provider == "google":
        events = await get_google_calendar_events(user_id)
    elif calendar_provider == "outlook":
        events = await get_outlook_calendar_events(user_id)
    else:
        raise ValueError(f"Unsupported provider: {calendar_provider}")
    
    for event in events:
        # Check if it's a sales meeting (has video link)
        if is_sales_meeting(event):
            meeting_url = extract_meeting_url(event)
            
            if "zoom.us" in meeting_url:
                await schedule_zoom_bot_join(
                    meeting_url=meeting_url,
                    start_time=event.start_time,
                    user_id=user_id,
                )
            elif "teams.microsoft.com" in meeting_url:
                await schedule_teams_bot_join(
                    meeting_url=meeting_url,
                    start_time=event.start_time,
                    user_id=user_id,
                )
```

### 3.5 User Consent & Privacy

```python
# Consent management for meeting bots

class MeetingBotConsent:
    """Manage user consent for meeting bot recording."""
    
    CONSENT_LEVELS = {
        "none": "No recording allowed",
        "internal": "Record internal meetings only",
        "external": "Record all meetings with disclosure",
        "silent": "Record all meetings (requires legal review)",
    }
    
    async def check_consent(
        self,
        user_id: str,
        meeting_type: str,
    ) -> bool:
        """Check if user has consented to recording."""
        user = await prisma.user.find_unique(where={"id": user_id})
        consent_level = user.bot_consent_level or "none"
        
        if consent_level == "none":
            return False
        elif consent_level == "internal":
            return meeting_type == "internal"
        else:
            return True
    
    async def send_recording_notice(
        self,
        meeting_id: str,
        participants: List[str],
    ):
        """Send recording disclosure to all participants."""
        # Generate disclosure message
        message = (
            "📝 This meeting is being recorded by SalesEcho AI "
            "for note-taking purposes. The recording will be processed "
            "to generate meeting summaries and action items."
        )
        
        # Send via meeting chat
        await send_meeting_chat_message(meeting_id, message)
```

---

## 4. Processing Pipeline

### 4.1 Unified Processing Queue

All ingestion channels feed into a unified processing queue:

```python
# app/services/processing_queue.py

from celery import Celery
from enum import Enum

class AudioSource(Enum):
    MANUAL_UPLOAD = "manual_upload"
    WHATSAPP = "whatsapp"
    PBX = "pbx"
    ZOOM = "zoom"
    TEAMS = "teams"
    MEET = "meet"

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
async def process_meeting_audio(
    self,
    meeting_id: str,
    audio_source: str,
    audio_path: str,
):
    """
    Unified meeting audio processing task.
    
    Steps:
    1. Normalize audio (FFmpeg)
    2. Transcribe (Gemini 1.5 Flash)
    3. Generate summary (Gemini)
    4. Dispatch actions (if auto_dispatch enabled)
    5. Update meeting record
    """
    try:
        # 1. Normalize
        normalized_path = await normalize_audio(audio_path)
        
        # 2. Transcribe
        transcript = await transcribe_audio(normalized_path, meeting_id)
        
        # 3. Generate summary
        summary = await generate_summary(transcript, meeting_id)
        
        # 4. Dispatch actions
        meeting = await prisma.meeting.find_unique(where={"id": meeting_id})
        if meeting.org.auto_dispatch_enabled:
            await dispatch_meeting_actions(meeting_id, summary)
        
        # 5. Update record
        await prisma.meeting.update(
            where={"id": meeting_id},
            data={
                "status": "COMPLETED",
                "transcript_raw": Json(transcript),
                "summary": Json(summary),
            },
        )
        
    except Exception as e:
        # Log error and retry
        await log_processing_error(meeting_id, e)
        raise self.retry(exc=e)
```

### 4.2 Audio Format Handling

```python
# app/services/audio_handler.py

SUPPORTED_FORMATS = {
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
    "audio/amr": ".amr",
    "audio/aac": ".aac",
}

async def convert_to_processing_format(
    input_path: str,
    target_format: str = "wav",
) -> str:
    """
    Convert audio to processing-optimized format.
    
    Target: 16kHz mono WAV (optimal for STT)
    """
    output_path = input_path.rsplit(".", 1)[0] + f".{target_format}"
    
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-ar", "16000",  # 16kHz sample rate
        "-ac", "1",      # Mono
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-y",
        output_path,
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    await process.communicate()
    
    if process.returncode != 0:
        raise AudioConversionError(f"FFmpeg failed: {process.returncode}")
    
    return output_path
```

---

## 5. Monitoring & Observability

### 5.1 Metrics

```python
# Key metrics to track

INGESTION_METRICS = {
    # Volume
    "meetings_ingested_total": Counter("Total meetings ingested by source"),
    "audio_bytes_processed": Counter("Total audio bytes processed"),
    
    # Latency
    "ingestion_latency_seconds": Histogram("Time from upload to processing start"),
    "processing_latency_seconds": Histogram("Time from processing start to completion"),
    
    # Quality
    "transcription_confidence": Histogram("Average transcription confidence"),
    "summary_confidence": Histogram("Average summary confidence"),
    
    # Errors
    "ingestion_errors_total": Counter("Total ingestion errors by type"),
    "processing_errors_total": Counter("Total processing errors by stage"),
}
```

### 5.2 Alerting

```yaml
# Alert rules

alerts:
  - name: HighIngestionErrorRate
    condition: rate(ingestion_errors_total[5m]) > 0.1
    severity: warning
    
  - name: ProcessingQueueBacklog
    condition: queue_length > 100
    severity: critical
    
  - name: WebhookEndpointDown
    condition: up{job="webhooks"} == 0
    severity: critical
```

---

## 6. Security & Compliance

### 6.1 Data Handling

| Data Type | Retention | Encryption | Access |
|-----------|-----------|------------|--------|
| Raw Audio | 30 days | AES-256 at rest | Org admin only |
| Transcripts | Indefinite | AES-256 | Org members |
| Summaries | Indefinite | AES-256 | Org members |
| PII | Redacted after processing | AES-256 | Audit only |

### 6.2 Compliance Checklist

- [ ] GDPR: Right to erasure implemented
- [ ] SOC 2: Audit logging enabled
- [ ] HIPAA: BAA available for healthcare orgs
- [ ] CCPA: Data disclosure endpoint available
- [ ] Recording consent: Multi-party consent tracking

---

## 7. Implementation Roadmap

### Phase 1: Q2 2025 (POC → Beta)
- [ ] WhatsApp Bot basic integration
- [ ] Twilio PBX webhook support
- [ ] Manual upload optimization

### Phase 2: Q3 2025 (Beta → Production)
- [ ] Zoom Meeting Bot
- [ ] Asterisk/FreePBX integration
- [ ] Teams Meeting Bot

### Phase 3: Q4 2025 (Scale)
- [ ] Google Meet Bot
- [ ] Multi-region deployment
- [ ] Real-time transcription streaming

---

## Appendix: Environment Variables

```bash
# WhatsApp Integration
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_BUSINESS_ACCOUNT_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=

# PBX Integration
PBX_WEBHOOK_SECRET=
PBX_ALLOWED_IPS=

# Zoom Integration
ZOOM_CLIENT_ID=
ZOOM_CLIENT_SECRET=
ZOOM_BOT_JID=
ZOOM_VERIFICATION_TOKEN=

# Teams Integration
TEAMS_APP_ID=
TEAMS_APP_SECRET=
TEAMS_TENANT_ID=

# Processing
CELERY_BROKER_URL=redis://localhost:6379/0
AUDIO_STORAGE_BUCKET=salesecho-audio
AUDIO_RETENTION_DAYS=30
```
