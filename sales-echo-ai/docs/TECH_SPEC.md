# SalesEcho AI - Technical Specification

## Version: 2.0
**Last Updated**: 2026-02-12  
**Status**: Active Development

---

## 1. Architecture Overview

### 1.1 System Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Mobile App  │────▶│  FastAPI     │────▶│  Supabase   │
│ (React      │     │  Backend     │     │  PostgreSQL │
│  Native)    │     │              │     │  + RLS      │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  OpenAI API  │
                    │  (Whisper +  │
                    │   GPT-4o)    │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  HubSpot API │
                    │  (OAuth2)    │
                    └──────────────┘
```

### 1.2 Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.9+)
- **ORM**: Prisma (Python client)
- **Validation**: Pydantic v2
- **Async**: asyncio, httpx

#### Database
- **Provider**: PostgreSQL (Supabase)
- **Security**: Row Level Security (RLS)
- **Migrations**: Prisma Migrate

#### AI Services
- **STT**: Gemini 1.5 Flash (primary)
- **LLM**: Gemini 1.5 Flash (Tachles summary generation)
- **Diarization**: Prompt-based speaker labeling within Gemini

#### Frontend
- **Web**: React + Tailwind CSS
- **Mobile**: React Native (Expo)

#### Infrastructure
- **Hosting**: TBD (Vercel/Railway/AWS)
- **Storage**: S3-compatible (audio files)
- **Queue**: Redis (background jobs)

---

## 2. AI Pipeline Specification

### 2.1 Speech-to-Text (STT)

#### Provider: Gemini 1.5 Flash
```python
# Configuration (resolved at runtime)
model = "gemini-1.5-flash"  # or discovered via client.models.list()
language = "he"  # Hebrew primary
```

#### Input Requirements
- **Supported Formats**: MP3, M4A, WAV, FLAC, WEBM, OGG, AAC (any format supported by FFmpeg)
- **Max Size**: 25 MB (after normalization)
- **Duration**: Up to 25 minutes
- **Channels**: Any (automatically converted to Mono during pre-processing)

#### Audio Pre-processing Layer
All incoming audio files are automatically normalized before transcription:

**Normalization Process**:
1. **Format Conversion**: Any input format → MP3
2. **Channel Conversion**: Any channels → Mono (1 channel)
3. **Sample Rate**: Any sample rate → 16kHz
4. **Bitrate**: Variable → 64kbps

**Implementation**:
- Uses FFmpeg via subprocess (no Python audio library dependency)
- Automatic cleanup of normalized files after processing
- Falls back to original file if FFmpeg unavailable
- File size optimization: Reduces file size while maintaining STT accuracy

**Benefits**:
- Ensures files stay under 25MB API limit
- Improves STT accuracy with consistent format
- Faster uploads with optimized file size
- Better compatibility across different audio sources (mobile, PBX, Zoom)

#### Output Structure
```json
{
  "text": "Full transcript",
  "language": "he",
  "duration": 3600.5,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "Segment text",
      "speaker": "Speaker 1"  // If diarization enabled
    }
  ]
}
```

#### Diarization Logic (Mono Files)
```python
# Implementation in transcription_service.py
def _extract_speakers_from_transcript(transcript: str, segments: list) -> list:
    """
    Extract speaker information from transcript using pattern matching.
    
    Looks for patterns:
    - [Speaker A], [Speaker B], [Rep], [Client]
    - Speaker A:, Speaker B:, etc.
    """
    # Pattern matching for speaker labels
    # Returns list of unique speakers found
```

**Diarization Approach**:
1. **Prompt-Based**: Both OpenAI and Gemini are prompted to identify speakers
2. **Pattern Extraction**: Regex patterns extract speaker labels from transcript
3. **Context Clues**: For mono recordings, uses content/tone/language patterns
4. **Format**: `[Speaker A]: text` or `[Rep]: text` format in transcript

**Current Implementation**:
- No external diarization service required
- Uses AI model's understanding of conversation context
- Extracts speaker labels from transcript text
- Stores in `transcript_raw.speakers` array

**Future Enhancement**:
- Consider AssemblyAI or pyannote.audio for more accurate speaker separation
- Would require additional API calls and cost

---

### 2.2 Summary Generation (LLM)

#### Provider: Gemini 1.5 Flash
```python
# Configuration (resolved at runtime)
model = "gemini-1.5-flash"  # text generation
temperature = 0.2  # Lower for fact-based extraction (enforced via prompt)
```

#### System Prompt: v2.0
- **Version**: TACHLES_SYSTEM_PROMPT_V2
- **Key Features**:
  - Fact-based extraction (no inference)
  - Confidence scores (0.0-1.0)
  - Source quotes (exact transcript snippets)
  - Heblish optimization (ILS currency, Israeli dates)
  - Review flag (requires_review if confidence < 0.7)

#### Input Processing
```python
# User prompt construction
user_prompt = f"""
Analyze this sales meeting transcript and extract ONLY facts explicitly stated:

{transcript}

CRITICAL REQUIREMENTS:
- Extract ONLY facts directly mentioned in the transcript (no inference)
- Provide confidence scores (0.0-1.0) and exact source quotes for every item
- Handle Heblish: Recognize ILS (₪/שקל), Israeli dates (יום ראשון הבא = next Sunday), mixed language
- If confidence < 0.7 for any item, set requires_review: true
- Use Tachles style: concise, bulleted, action-oriented Hebrew
- Calculate actual dates for relative dates (e.g., 'יום ראשון הבא' → ISO date)
"""
```

#### Output Validation
- **Pydantic Models**: `TachlesSummary` (from `app/models/meeting_models.py`)
- **Validation Rules**:
  - All confidence scores: `ge=0.0, le=1.0`
  - All dates: ISO 8601 format
  - All sources: Non-empty string
  - All UUIDs: Valid UUID4 format

#### Error Handling
- **JSON Parse Errors**: Log to `processing_errors`, retry once
- **Invalid Schema**: Reject, log error, return partial summary
- **API Failures**: Fallback to Gemini 1.5 Pro (if configured)

---

## 3. Database Schema

### 3.1 OAuth2 Token Storage

#### Table: `crm_integrations`
```prisma
model CRMIntegration {
  id              String   @id @default(uuid()) @db.Uuid
  org_id          String   @db.Uuid
  
  provider        String   @db.VarChar(50)  // "hubspot", "salesforce"
  status          String   @default("active") @db.VarChar(50)
  
  // OAuth2 Tokens (encrypted in production)
  access_token    String?  @db.Text
  refresh_token   String?  @db.Text
  expires_at      DateTime? @db.Timestamptz(6)  // Token expiration
  
  // Configuration
  config          Json?    // Provider-specific settings
  webhook_url     String?  @db.Text
  last_sync_at    DateTime? @db.Timestamptz(6)
  
  created_at      DateTime @default(now()) @db.Timestamptz(6)
  updated_at      DateTime @updatedAt @db.Timestamptz(6)
  
  organization    Organization @relation(fields: [org_id], references: [id], onDelete: Cascade)
  
  @@unique([org_id, provider])
  @@index([org_id])
  @@index([status])
  @@map("crm_integrations")
}
```

#### OAuth2 Flow (HubSpot)
1. **Authorization**: User clicks "Connect HubSpot" → redirects to HubSpot OAuth
2. **Callback**: HubSpot redirects with `code`
3. **Token Exchange**: Backend exchanges `code` for `access_token` and `refresh_token`
4. **Storage**: Tokens stored in `crm_integrations` table (encrypted)
5. **Refresh**: Automatic token refresh before expiration

#### Token Security
- **Encryption**: Use Supabase Vault or AWS KMS for production
- **RLS**: `crm_integrations` table locked to `service_role` only
- **Rotation**: Refresh tokens rotated on each use
- **Expiration**: Check `expires_at` before API calls

---

### 3.2 Usage Tracking

#### Table: `organizations`
```prisma
model Organization {
  id            String   @id @default(uuid()) @db.Uuid
  name          String   @db.VarChar(255)
  slug          String?  @unique @db.VarChar(255)
  settings      Json?    // Org-specific config
  
  // Usage Tracking
  usage_minutes Float    @default(0.0) @db.DoublePrecision  // Total audio minutes processed
  
  created_at    DateTime @default(now()) @db.Timestamptz(6)
  updated_at    DateTime @updatedAt @db.Timestamptz(6)
  
  // Relations
  users            User[]
  meetings         Meeting[]
  corrections      Correction[]
  crm_integrations CRMIntegration[]
  crm_audit_logs   CRMAuditLog[]
  
  @@map("organizations")
}
```

#### Usage Calculation
```python
# After successful transcription
audio_duration_seconds = transcript_response.duration
audio_duration_minutes = audio_duration_seconds / 60

# Update organization usage
await prisma.organization.update(
    where={"id": org_id},
    data={
        "usage_minutes": {
            "increment": audio_duration_minutes
        }
    }
)
```

#### Billing Integration
- **Monthly Reset**: Cron job resets `usage_minutes` on 1st of month
- **Caps**: Check `settings.token_caps` before processing
- **Alerts**: Notify at 80%, 90%, 100% of monthly cap

---

## 4. Pydantic Validation

### 4.1 AI Output Validation

#### Model: `TachlesSummary`
```python
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List
from datetime import date

class TachlesSummary(BaseModel):
    summary_id: UUID4
    metadata: SummaryMetadata
    content: SummaryContent
    governance: SummaryGovernance
```

#### Validation Rules
- **UUIDs**: Must be valid UUID4 format
- **Confidence Scores**: `Field(..., ge=0.0, le=1.0)`
- **Dates**: ISO 8601 format (YYYY-MM-DD)
- **Emails**: Email validation via Pydantic `EmailStr`
- **Sources**: Non-empty string, max 1000 characters

#### Error Handling
```python
try:
    summary = TachlesSummary(**ai_response)
except ValidationError as e:
    # Log validation errors
    processing_errors.append({
        "step": "validation",
        "errors": e.errors(),
        "timestamp": datetime.now().isoformat()
    })
    # Return partial summary or raise
```

---

## 5. API Endpoints

### 5.1 Meeting Upload
```
POST /api/v1/meetings/upload
Content-Type: multipart/form-data

Form Data:
- org_id: UUID (required)
- user_id: UUID (required)
- client_name: string (optional)
- client_id: UUID (optional)
- file: audio file (required)

Response: MeetingUploadResponse
```

### 5.2 Get Meeting
```
GET /api/v1/meetings/{meeting_id}

Response: MeetingDetailsResponse
```

### 5.3 Update Meeting
```
PATCH /api/v1/meetings/{meeting_id}

Body: {
  "summary": {...},  // Updated summary
  "approved_for_sync": true
}

Response: MeetingDetailsResponse
```

---

## 6. Security Specifications

### 6.1 Row Level Security (RLS)
- **Enabled**: All tables
- **Policies**: Multi-tenancy (org_id-based)
- **Service Role**: Bypasses RLS for backend operations
- **Authenticated**: Restricted to own org_id

### 6.2 Data Encryption
- **At Rest**: Supabase encryption (PostgreSQL)
- **In Transit**: TLS 1.3
- **Sensitive Fields**: OAuth tokens encrypted with KMS

### 6.3 Zero-Retention Policy
- **Default**: 24 hours
- **Configurable**: Per org in `settings.retention_policy_hours`
- **Implementation**: Background job deletes audio files
- **Audit**: `audio_deleted_at` timestamp logged

---

## 7. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Transcription Speed | < 2x audio duration | End-to-end timing |
| Summary Generation | < 30 seconds | API response time |
| API Latency | < 500ms (non-AI) | P95 percentile |
| Mobile Sync | < 5 seconds/recording | Background job timing |
| Database Queries | < 100ms | Prisma query timing |

---

## 8. Monitoring & Observability

### 8.1 Logging
- **Structured Logging**: JSON format
- **Levels**: DEBUG, INFO, WARNING, ERROR
- **Fields**: timestamp, level, message, context (org_id, user_id)

### 8.2 Metrics
- **Processing Errors**: Tracked in `processing_errors` JSON field
- **API Usage**: Tracked in `usage_minutes`
- **Sync Success Rate**: Calculated from `crm_audit_logs`

### 8.3 Alerts
- **High Error Rate**: >5% processing failures
- **API Downtime**: OpenAI/HubSpot API failures
- **Storage Quota**: >90% S3 bucket usage

---

## 9. Deployment & Infrastructure

### 10.1 CI/CD Pipeline (GitHub Actions)

#### Workflow: `deploy-backend.yml`
```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - 'app/**'
      - 'main.py'
      - 'requirements.txt'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python3 -m prisma generate
      - name: Run tests
        run: pytest tests/unit/
      - name: Deploy to Railway/Render
        uses: railway-app/railway-action@v1
        with:
          service: backend
          environment: production
```

#### Workflow: `deploy-frontend.yml`
```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

### 10.2 Infrastructure Components

#### Backend Hosting: Railway or Render
- **Platform**: Railway (preferred) or Render
- **Runtime**: Python 3.11
- **Build Command**: `pip install -r requirements.txt && python3 -m prisma generate`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: All secrets from `.env` (managed in platform dashboard)
- **Auto-Deploy**: Enabled on `main` branch push

#### Frontend Hosting: Vercel
- **Framework**: React (Next.js recommended for SSR)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment Variables**: `VITE_API_URL` or `NEXT_PUBLIC_API_URL`
- **Auto-Deploy**: Enabled on `main` branch push

#### Database: Supabase
- **Provider**: Supabase PostgreSQL (managed)
- **Connection**: Direct connection (port 5432) for migrations
- **Pooler**: Connection pooler (port 6543) for application runtime
- **Backups**: Automatic daily backups (retention: 7 days)
- **RLS**: Enabled via `supabase_security_setup.sql`

#### Storage: S3-Compatible
- **Provider**: AWS S3, Supabase Storage, or Cloudflare R2
- **Bucket**: `salesecho-audio-{environment}` (dev/staging/prod)
- **Lifecycle**: Auto-delete after 24 hours (configurable per org)
- **Access**: Private bucket, signed URLs for temporary access

### 10.3 Environment Configuration

#### Production Environment Variables
```bash
# Database
DATABASE_URL=postgresql://...@supabase:5432/postgres

# AI Services
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=...  # Fallback

# CRM
HUBSPOT_CLIENT_ID=...
HUBSPOT_CLIENT_SECRET=...

# Storage
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=salesecho-audio-prod
AWS_REGION=us-east-1

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production

# Application
ENVIRONMENT=production
DEBUG=false
```

---

## 10. Cost Estimation

### 11.1 Per 30-Minute Meeting Breakdown

#### OpenAI Whisper (STT)
- **Model**: `whisper-1`
- **Pricing**: $0.006 per minute
- **Cost for 30 minutes**: $0.18

#### GPT-4o (Summary Generation)
- **Model**: `gpt-4o`
- **Input Tokens**: ~4,000 tokens (30-min transcript ≈ 4,500 words)
- **Output Tokens**: ~1,500 tokens (structured JSON summary)
- **Pricing**: 
  - Input: $2.50 per 1M tokens
  - Output: $10.00 per 1M tokens
- **Cost Calculation**:
  - Input: (4,000 / 1,000,000) × $2.50 = $0.01
  - Output: (1,500 / 1,000,000) × $10.00 = $0.015
  - **Total GPT-4o**: $0.025

#### Total AI Cost per 30-Minute Meeting
- **Whisper STT**: $0.18
- **GPT-4o Summary**: $0.025
- **Total**: **$0.205 per meeting**

#### Monthly Cost Projections
| Meetings/Month | AI Cost | Infrastructure* | Total |
|----------------|---------|-----------------|-------|
| 100 | $20.50 | $50 | $70.50 |
| 500 | $102.50 | $100 | $202.50 |
| 1,000 | $205.00 | $150 | $355.00 |
| 5,000 | $1,025.00 | $300 | $1,325.00 |

*Infrastructure: Railway/Render ($20-50), Vercel ($0-20), Supabase ($25-100), S3 ($5-30)

### 11.2 Cost Optimization Strategies
- **Token Caps**: Per-org limits in `settings.token_caps`
- **Caching**: Cache common transcript patterns
- **Batch Processing**: Process multiple meetings in single API call (if supported)
- **Fallback to Gemini**: Use Gemini 1.5 Pro for lower-cost option (50% cheaper)

---

## 11. Monitoring & Error Handling

### 12.1 Error Tracking: Sentry

#### Integration
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,
)
```

#### Error Context
```python
# Add context to errors
sentry_sdk.set_context("meeting", {
    "meeting_id": meeting_id,
    "org_id": org_id,
    "user_id": user_id,
    "audio_duration": duration_seconds,
})

# Capture exceptions
try:
    summary = await generate_summary(...)
except Exception as e:
    sentry_sdk.capture_exception(e)
    # Log to processing_errors
    await log_processing_error(meeting_id, e, "summary_generation")
```

#### Alert Rules
- **Error Rate**: Alert if >5% of requests fail
- **API Failures**: Alert on OpenAI/HubSpot API errors
- **Processing Time**: Alert if >2x audio duration
- **Database Errors**: Alert on connection failures

### 12.2 Structured Logging (JSON Format)

#### Log Format
```json
{
  "timestamp": "2026-02-12T21:28:46.378476Z",
  "level": "INFO",
  "service": "salesecho-ai",
  "module": "ai_service",
  "function": "transcribe_audio",
  "context": {
    "meeting_id": "uuid",
    "org_id": "uuid",
    "user_id": "uuid",
    "audio_duration": 1800.5,
    "file_size_mb": 12.3
  },
  "message": "Transcription completed successfully",
  "metrics": {
    "processing_time_seconds": 45.2,
    "transcript_length": 1250
  }
}
```

#### Implementation
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": "salesecho-ai",
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        
        # Add context if available
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add metrics if available
        if hasattr(record, "metrics"):
            log_data["metrics"] = record.metrics
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

# Configure logger
logger = logging.getLogger("salesecho")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

#### Log Levels
- **DEBUG**: Detailed diagnostic information (development only)
- **INFO**: General informational messages (processing steps, API calls)
- **WARNING**: Warning messages (low confidence scores, retries)
- **ERROR**: Error messages (API failures, validation errors)
- **CRITICAL**: Critical errors (database failures, security breaches)

---

## 12. Testing Strategy

### 13.1 Unit Tests (Pytest)

#### Test Structure
```
tests/
├── unit/
│   ├── test_models.py          # Pydantic validation
│   ├── test_ai_service.py      # AI functions (mocked)
│   ├── test_database.py        # Prisma operations
│   └── test_api_endpoints.py   # FastAPI routes
```

#### Example: Pydantic Model Test
```python
import pytest
from app.models.meeting_models import TachlesSummary, ActionItem

def test_action_item_confidence_validation():
    # Valid confidence
    item = ActionItem(
        task="Test task",
        confidence=0.85,
        source="transcript snippet"
    )
    assert item.confidence == 0.85
    
    # Invalid confidence (>1.0)
    with pytest.raises(ValueError):
        ActionItem(task="Test", confidence=1.5, source="snippet")
    
    # Invalid confidence (<0.0)
    with pytest.raises(ValueError):
        ActionItem(task="Test", confidence=-0.1, source="snippet")
```

#### Example: AI Service Test (Mocked)
```python
from unittest.mock import AsyncMock, patch
from app.services.ai_service import transcribe_audio

@pytest.mark.asyncio
async def test_transcribe_audio_success():
    mock_response = {
        "text": "Test transcript",
        "language": "he",
        "duration": 60.0,
        "segments": []
    }
    
    with patch("app.services.ai_service.get_openai_client") as mock_client:
        mock_client.return_value.audio.transcriptions.create = AsyncMock(
            return_value=type('obj', (object,), mock_response)()
        )
        
        result = await transcribe_audio("/path/to/audio.mp3")
        assert result["transcript"] == "Test transcript"
        assert result["language"] == "he"
```

### 13.2 Integration Tests (AI Pipeline Logic)

#### Test Structure
```
tests/
├── integration/
│   ├── test_meeting_pipeline.py    # End-to-end upload flow
│   ├── test_crm_sync.py            # HubSpot sync (test account)
│   └── test_rls_policies.py        # Database security
```

#### Example: Meeting Pipeline Test
```python
@pytest.mark.asyncio
async def test_meeting_upload_pipeline():
    # Create test org and user
    org = await prisma.organization.create(...)
    user = await prisma.user.create(...)
    
    # Upload audio file
    response = await client.post(
        "/api/v1/meetings/upload",
        files={"file": ("test.m4a", audio_bytes, "audio/m4a")},
        data={"org_id": org.id, "user_id": user.id}
    )
    
    assert response.status_code == 200
    meeting_id = response.json()["meeting_id"]
    
    # Verify meeting created
    meeting = await prisma.meeting.find_unique(where={"id": meeting_id})
    assert meeting.status == "processed"
    assert meeting.transcript is not None
    assert meeting.summary is not None
```

### 13.3 E2E Tests (Playwright for UI)

#### Test Structure
```
tests/
├── e2e/
│   ├── test_review_card_ui.py      # Review workflow
│   ├── test_crm_matching.py        # CRM entity matching
│   └── test_mobile_sync.py         # Offline queue → sync
```

#### Example: Review Card UI Test
```python
from playwright.async_api import async_playwright

async def test_review_card_edit_flow():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Navigate to review page
        await page.goto(f"http://localhost:3000/meetings/{meeting_id}/review")
        
        # Click on deal value field
        await page.click('[data-field="deal_value"]')
        
        # Edit value
        await page.fill('[data-field="deal_value"] input', "75000")
        
        # Save
        await page.click('[data-action="save"]')
        
        # Verify save
        await page.wait_for_selector('.success-message')
        assert "Saved" in await page.text_content('.success-message')
        
        await browser.close()
```

#### Test Coverage Targets
- **Unit Tests**: >80% code coverage
- **Integration Tests**: All critical paths
- **E2E Tests**: All user journeys from USER_STORIES.md

---

## 13. Resilience & Rate Limits

### 14.1 Exponential Backoff Strategy

#### Implementation
```python
import asyncio
from typing import Callable, Any
from openai import RateLimitError, APIError

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Any:
    """
    Retry function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
    
    Returns:
        Function result or raises last exception
    """
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return await func()
        except (RateLimitError, APIError) as e:
            if attempt == max_retries - 1:
                raise  # Last attempt, raise exception
            
            # Calculate delay with exponential backoff
            delay = min(delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter to prevent thundering herd
            jitter = delay * 0.1 * (0.5 - random.random())
            delay += jitter
            
            logger.warning(
                f"API error (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                f"Retrying in {delay:.2f} seconds...",
                extra={
                    "context": {
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "delay": delay,
                        "error": str(e)
                    }
                }
            )
            
            await asyncio.sleep(delay)
    
    raise Exception("Max retries exceeded")
```

#### Usage in AI Service
```python
async def transcribe_audio(file_path: str, language: str = "he") -> Dict[str, Any]:
    client = get_openai_client()
    
    async def _transcribe():
        with open(file_path, "rb") as audio_file:
            return client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json",
            )
    
    try:
        transcript_response = await retry_with_backoff(
            _transcribe,
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0
        )
        # Process response...
    except RateLimitError as e:
        # Log to processing_errors, don't lose user data
        await log_processing_error(meeting_id, e, "transcription")
        raise HTTPException(
            status_code=429,
            detail="OpenAI API rate limit exceeded. Please try again later."
        )
```

### 14.2 Handling 429 Errors (Rate Limits)

#### Strategy: Queue with Retry
```python
from datetime import datetime, timedelta

async def handle_rate_limit_error(
    meeting_id: str,
    error: RateLimitError,
    stage: str
):
    """
    Handle rate limit errors without losing user data.
    
    Strategy:
    1. Log error to processing_errors
    2. Set meeting status to 'pending_retry'
    3. Schedule retry for later (exponential backoff)
    4. Notify user of delay
    """
    # Log error
    await log_processing_error(meeting_id, error, stage)
    
    # Calculate retry time (exponential backoff)
    meeting = await prisma.meeting.find_unique(where={"id": meeting_id})
    retry_count = getattr(meeting, "retry_count", 0) + 1
    retry_delay = min(60 * (2 ** retry_count), 3600)  # Max 1 hour
    retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
    
    # Update meeting status
    await prisma.meeting.update(
        where={"id": meeting_id},
        data={
            "status": "pending_retry",
            "retry_count": retry_count,
            "sync_scheduled_at": retry_at,  # Reuse field for retry scheduling
            "sync_error_message": f"Rate limit exceeded. Retrying at {retry_at.isoformat()}"
        }
    )
    
    # Schedule background job (Celery, RQ, or similar)
    schedule_retry_job(meeting_id, retry_at)
    
    # Notify user (push notification or email)
    await notify_user_rate_limit(meeting_id, retry_at)
```

#### Background Retry Job
```python
async def process_pending_retries():
    """
    Background job to retry failed meetings.
    Runs every 5 minutes.
    """
    now = datetime.utcnow()
    
    pending_meetings = await prisma.meeting.find_many(
        where={
            "status": "pending_retry",
            "sync_scheduled_at": {"lte": now}
        },
        take=10  # Process 10 at a time
    )
    
    for meeting in pending_meetings:
        try:
            # Retry the failed operation
            if "transcription" in meeting.processing_errors[-1]["stage"]:
                await retry_transcription(meeting.id)
            elif "summary" in meeting.processing_errors[-1]["stage"]:
                await retry_summary_generation(meeting.id)
        except Exception as e:
            # If still failing, increment retry count
            if meeting.retry_count >= 5:
                # Max retries exceeded, mark as failed
                await prisma.meeting.update(
                    where={"id": meeting.id},
                    data={"status": "failed"}
                )
            else:
                # Schedule another retry
                await handle_rate_limit_error(meeting.id, e, "retry")
```

### 14.3 Data Preservation

#### Never Lose User Data
- **Audio Files**: Stored in S3 before processing
- **Meeting Records**: Created immediately on upload
- **Processing Errors**: Logged to `processing_errors` JSON field
- **Retry Queue**: Failed operations queued for retry
- **User Notification**: Users notified of delays/retries

#### Idempotency
- **Meeting ID**: UUID generated client-side or server-side
- **Duplicate Prevention**: Check for existing meeting before creating
- **API Calls**: Idempotent operations where possible

---

## 14. Future Enhancements

- **Salesforce Integration**: OAuth2 flow similar to HubSpot
- **Custom Entities**: Org-specific field extraction
- **Voice Cloning**: Rep voice verification
- **Multi-Meeting Context**: Cross-meeting analysis
- **Predictive Scoring**: Deal probability based on history
