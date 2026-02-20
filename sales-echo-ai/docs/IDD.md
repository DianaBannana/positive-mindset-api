# SalesEcho AI - Interface Design Document (IDD)

This document defines the primary ingestion endpoint and API interfaces for SalesEcho AI.

## Primary Ingestion Endpoint

### POST `/api/v1/meetings/upload`

**Purpose:** Upload audio file for meeting transcription and summary generation.

#### Request Specification

| Attribute | Technical Detail |
|-----------|------------------|
| **Method** | `POST` |
| **Endpoint** | `/api/v1/meetings/upload` |
| **Content-Type** | `multipart/form-data` |
| **Authentication** | Required (future: Bearer token) |

#### Request Payload

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `UploadFile` | Yes | Audio file (MP3, M4A, WAV, WEBM, etc.) |
| `org_id` | `UUID` (string) | Yes | Organization UUID for multi-tenancy |
| `user_id` | `UUID` (string) | Yes | User/sales rep UUID |
| `client_name` | `string` | No | Client/contact name (Hebrew/English) |
| `client_id` | `UUID` (string) | No | Existing client UUID (if known) |

**File Constraints:**
- **Max File Size**: 50MB (before normalization)
- **Supported Formats**: Any audio format supported by FFmpeg
  - MP3, M4A, WAV, FLAC, WEBM, OGG, AAC, etc.
- **Content-Type Validation**: Must start with `audio/`
- **Automatic Normalization**: All files converted to MP3, Mono, 16kHz, 64kbps

#### Response Specification

**Success Response (202 Accepted):**

```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING",
  "message": "Meeting uploaded successfully. Processing in progress.",
  "transcript": null,
  "summary": null
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `meeting_id` | `UUID` (string) | Unique identifier for the meeting record |
| `status` | `string` | Current processing status: `"PENDING"`, `"PROCESSING"`, `"COMPLETED"`, `"FAILED"` |
| `message` | `string` | Human-readable status message |
| `transcript` | `string` \| `null` | Full transcribed text (available after transcription completes) |
| `summary` | `TachlesSummary` \| `null` | Structured summary object (available after summary generation) |

**Error Responses:**

**400 Bad Request:**
```json
{
  "detail": "File must be an audio file"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Transcription failed: [error message]"
}
```

#### Processing Flow

1. **File Validation**
   - Content-Type must be `audio/*`
   - File size checked (max 50MB)
   - File saved to temporary storage

2. **Database Record Creation**
   - Meeting record created with `status: "PENDING"`
   - Metadata stored (org_id, user_id, client_name, etc.)
   - Temporary file path stored in `audio_url`

3. **Audio Pre-processing**
   - FFmpeg normalization (MP3, Mono, 16kHz, 64kbps)
   - File size reduction (typically 50-70%)
   - Normalized file replaces original for API calls

4. **Transcription**
   - Primary: OpenAI Whisper v3
   - Fallback: Gemini 1.5 Pro (on errors)
   - Status updated to `"PROCESSING"` during transcription
   - Status updated to `"COMPLETED"` on success, `"FAILED"` on error

5. **Summary Generation**
   - GPT-4o generates structured "Tachles" summary
   - Pydantic validation ensures data contract compliance
   - Summary stored in `meeting.summary` (JSON field)

6. **Usage Tracking**
   - `organization.usage_minutes` incremented by duration
   - Duration calculated from audio file (seconds → minutes)

7. **Cleanup**
   - Temporary files removed (normalized + original)
   - Error logs stored in `meeting.processing_errors` if failures occur

#### Rate Limiting

**Current Implementation:**
- No rate limiting (future enhancement)

**Planned Implementation:**
- Rate limiting per user: 10 uploads per minute
- Rate limiting per organization: 100 uploads per hour
- Rate limit headers in response:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in window
  - `X-RateLimit-Reset`: Time when limit resets

#### Constraints

**File Size:**
- Maximum upload size: 50MB (before normalization)
- After normalization: Typically 25MB or less
- API limit: 25MB (OpenAI/Gemini)

**Processing Time:**
- Normalization: ~5-10 seconds
- Transcription: ~30-60 seconds per minute of audio
- Summary generation: ~10-20 seconds
- Total: ~1-2 minutes for 30-minute meeting

**Concurrent Requests:**
- No limit on concurrent uploads (future: queue system)
- Each request processed independently
- Database handles concurrent writes via Prisma

#### Error Handling

**Error Categories:**

1. **Validation Errors (400)**
   - Invalid file type
   - Missing required fields
   - Invalid UUID format

2. **Processing Errors (500)**
   - Transcription failures
   - Summary generation failures
   - Database errors

3. **System Errors (500)**
   - FFmpeg unavailable
   - API provider failures
   - Storage errors

**Error Logging:**
- All errors logged to `meeting.processing_errors` JSON field
- Error structure:
  ```json
  {
    "errors": [
      {
        "stage": "transcription",
        "error_type": "RateLimitError",
        "error": "OpenAI API rate limit exceeded",
        "provider": "openai",
        "fallback_triggered": true,
        "timestamp": "2026-02-14T10:00:00Z"
      }
    ]
  }
  ```

#### Example Requests

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/meetings/upload" \
  -F "org_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "user_id=789e0123-e45b-67c8-d901-234567890abc" \
  -F "client_name=לקוח דוגמה" \
  -F "file=@meeting_audio.m4a"
```

**Python (httpx):**
```python
import httpx

with open("meeting_audio.m4a", "rb") as f:
    files = {"file": ("meeting_audio.m4a", f, "audio/m4a")}
    data = {
        "org_id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "789e0123-e45b-67c8-d901-234567890abc",
        "client_name": "לקוח דוגמה"
    }
    response = httpx.post(
        "http://localhost:8000/api/v1/meetings/upload",
        files=files,
        data=data
    )
    print(response.json())
```

**JavaScript (fetch):**
```javascript
const formData = new FormData();
formData.append('file', audioFile);
formData.append('org_id', '123e4567-e89b-12d3-a456-426614174000');
formData.append('user_id', '789e0123-e45b-67c8-d901-234567890abc');
formData.append('client_name', 'לקוח דוגמה');

fetch('http://localhost:8000/api/v1/meetings/upload', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => console.log(data));
```

## Data Models

### MeetingUploadResponse

```python
class MeetingUploadResponse(BaseModel):
    meeting_id: str  # UUID
    status: str  # "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED"
    message: str
    transcript: Optional[str] = None
    summary: Optional[TachlesSummary] = None
```

### TachlesSummary

See `app/models/meeting_models.py` for complete schema.

**Key Fields:**
- `summary_id`: UUID of meeting
- `metadata`: Organization, user, client IDs, language mix, duration
- `content`: Summary text, action items, CRM entities
- `governance`: Confidence scores, review flags, hallucination checks

## Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 202 | Accepted | Request accepted, processing started |
| 400 | Bad Request | Invalid file type or missing required fields |
| 401 | Unauthorized | Authentication required (future) |
| 403 | Forbidden | Insufficient permissions (future) |
| 429 | Too Many Requests | Rate limit exceeded (future) |
| 500 | Internal Server Error | Processing failure |

## Future Endpoints

**Planned Endpoints:**
- `GET /api/v1/meetings/{meeting_id}` - Retrieve meeting details
- `PATCH /api/v1/meetings/{meeting_id}` - Update meeting metadata
- `POST /api/v1/meetings/{meeting_id}/corrections` - Submit feedback corrections
- `POST /api/v1/meetings/{meeting_id}/sync` - Trigger CRM sync
- `GET /api/v1/organizations/{org_id}/usage` - Get usage statistics

---

**Last Updated**: February 14, 2025  
**Version**: 1.0.0  
**Maintained By**: Technical Team
