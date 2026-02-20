# SalesEcho AI

Enterprise-ready Call-to-CRM automation engine with Hebrew/English support.

## 🚀 Tech Stack

- **Backend**: FastAPI (Python) - Async-first, modular architecture
- **Database**: PostgreSQL via Supabase with Prisma ORM
- **AI Services**: OpenAI Whisper v3 (STT) + GPT-4o (LLM)
- **Language Support**: Hebrew/English bilingual with UTF-8 encoding

## 📁 Project Structure

```
sales-echo-ai/
├── app/
│   ├── api/
│   │   └── v1/              # API endpoints (meetings, etc.)
│   ├── core/                 # Configuration, database, security
│   │   ├── config.py         # Settings management
│   │   └── database.py       # Prisma client connection
│   ├── services/             # Business logic
│   │   └── ai_service.py     # AI transcription & summary generation
│   ├── models/               # Pydantic schemas
│   │   └── meeting_models.py # Tachles summary models
│   └── static/               # Static assets
├── docs/                     # Documentation
│   ├── master_spec.md         # Master specification
│   └── IMPLEMENTATION_LOG.md # Implementation history
├── migrations/               # Prisma database migrations
├── main.py                   # FastAPI application entry point
├── schema.prisma             # Prisma database schema
└── requirements.txt          # Python dependencies
```

## 🛠️ Setup Instructions

### 1. Prerequisites

- Python 3.9+
- Node.js 18+ (for Prisma CLI)
- PostgreSQL database (Supabase recommended)
- **FFmpeg** (required for audio pre-processing)

#### System Requirements

**FFmpeg Installation:**

FFmpeg is required for audio normalization and pre-processing. The server will not start without it.

**macOS:**
```bash
# Using Homebrew (recommended)
brew install ffmpeg

# Verify installation
ffmpeg -version
```

**Linux (Ubuntu/Debian):**
```bash
# Update package list
sudo apt update

# Install FFmpeg
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

**Linux (CentOS/RHEL/Fedora):**
```bash
# Fedora
sudo dnf install ffmpeg

# CentOS/RHEL (requires EPEL repository)
sudo yum install epel-release
sudo yum install ffmpeg

# Verify installation
ffmpeg -version
```

**Windows:**
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract the ZIP file to a folder (e.g., `C:\ffmpeg`)
3. Add FFmpeg to your system PATH:
   - Open "System Properties" → "Environment Variables"
   - Edit "Path" variable
   - Add the `bin` folder path (e.g., `C:\ffmpeg\bin`)
4. Restart your terminal/command prompt
5. Verify installation:
   ```cmd
   ffmpeg -version
   ```

**Alternative: Using Chocolatey (Windows):**
```cmd
choco install ffmpeg
```

**Verify FFmpeg is in PATH:**
```bash
# Should output FFmpeg version information
ffmpeg -version
```

**Note:** If FFmpeg is not found, the server will fail to start with a CRITICAL error message.

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Install Prisma CLI (if not already installed)
npm install -g prisma
# OR use npx (no global install needed)
npx prisma
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
# Database Configuration
# IMPORTANT: Use Direct Connection (port 5432) for migrations
DATABASE_URL=postgresql://user:password@host:5432/database?connect_timeout=300

# AI Provider API Keys
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here  # Optional

# CRM Integration
HUBSPOT_ACCESS_TOKEN=your_hubspot_access_token_here  # Optional

# Application Settings
ENVIRONMENT=development
DEBUG=true
```

**⚠️ Database Connection Notes:**
- **For Migrations**: Use Direct Connection (port 5432) - required for schema changes
- **For Application**: Can use Pooler Connection (port 6543) for better performance
- Supabase provides both connection strings in the dashboard

### 4. Database Setup

```bash
# Generate Prisma Client
npx prisma generate

# Create and apply database migration
npx prisma migrate dev --name init_sales_echo_final

# Verify database connection
npx prisma studio  # Opens database browser (optional)
```

**Migration Status:**
- ✅ Initial migration applied: `20260207174011_init_sales_echo_final`
- All tables created with multi-tenancy support
- Indexes and foreign keys configured

### 5. Run the Application

```bash
# Development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access:
# - API docs: http://localhost:8000/docs
# - Health check: http://localhost:8000/health
# - API base: http://localhost:8000/api/v1
```

## ✅ Implementation Status

### Module 0: Boilerplate ✅ [DONE]
- FastAPI application structure
- CORS middleware configuration
- Health check endpoint
- Modular directory structure
- Database connection lifecycle management

### Module 1: Database Schema ✅ [DONE]
- Prisma schema with PostgreSQL
- Multi-tenancy support (org_id on all core tables)
- 6 core models: Organization, User, Meeting, Correction, CRMIntegration, CRMAuditLog
- Hebrew/English UTF-8 support
- JSON fields for structured data
- Audit trail for CRM operations
- Human-in-the-loop approval flags
- Audio deletion tracking (zero retention policy)

### Module 2: AI Pipeline ✅ [DONE]
- Audio transcription (Whisper API)
- Tachles summary generation (GPT-4o)
- Pydantic models for Data Contract
- API endpoints for meeting upload
- Error handling and logging

## 🤖 AI Capabilities

### Speech-to-Text (STT)
- **Provider**: OpenAI Whisper v3
- **Language Support**: Hebrew (primary), English, bilingual code-switching
- **Output**: Full transcript with timestamps and speaker diarization
- **Encoding**: UTF-8 (preserves Hebrew characters)

### Summary Generation
- **Provider**: OpenAI GPT-4o
- **Style**: "Tachles" - Direct, concise, action-oriented Hebrew summaries
- **Output**: Structured JSON matching Data Contract v3.0
- **Features**:
  - Extracts action items with assignees and due dates
  - Identifies CRM entities (deal values, dates, emails)
  - Provides confidence scores (0-1) for all extracted items
  - Includes source snippets for explainability
  - Handles Hebrew/English code-switching ("Heblish")
  - Recognizes Israeli date formats and ILS currency (₪)

### Processing Pipeline
1. **Audio Upload** → Temporary file storage
2. **Transcription** → Whisper API (async)
3. **Language Detection** → Automatic Hebrew/English mix detection
4. **Summary Generation** → GPT-4o with Tachles system prompt (async)
5. **Validation** → Pydantic model validation
6. **Storage** → Database with full error logging

### API Endpoint

**POST `/api/v1/meetings/upload`**

Upload audio file for processing:

```bash
curl -X POST "http://localhost:8000/api/v1/meetings/upload" \
  -F "org_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "user_id=789e0123-e45b-67c8-d901-234567890abc" \
  -F "client_name=לקוח דוגמה" \
  -F "file=@meeting_audio.mp3"
```

**Response**:
- `meeting_id`: UUID of created meeting
- `status`: "success" or "partial"
- `transcript`: Full transcribed text
- `summary`: Structured TachlesSummary object

**Error Handling**:
- Errors logged to `processing_errors` field in database
- Partial success: Transcription can succeed even if summary fails
- Temporary files automatically cleaned up

### Next Modules
- Module 3: Review Card UI (React frontend)
- Module 4: CRM Integration (HubSpot/Salesforce)
- Module 5: Feedback Loop Engine
- Module 6: API Gateway + Auth
- Module 7: Admin Dashboard

## 🗄️ Database Models

### Core Models

**Organization**
- Multi-tenant root entity
- Stores org settings (JSON)
- Relations: users, meetings, corrections, crm_integrations, crm_audit_logs

**User**
- Sales reps and admins
- Auth0/Clerk ready (supports both)
- Role-based access (sales_rep, admin, manager)
- Relations: organization, meetings, corrections, crm_audit_logs

**Meeting**
- Core meeting entity
- Stores: audio_url, transcript, summary (JSON), status
- Tracks: review status, sync status, processing errors
- Relations: organization, user, corrections, crm_audit_logs

**Correction**
- Feedback loop for AI improvement
- Tracks: field_name, old_value, new_value, source_snippet
- Relations: organization, user, meeting

**CRMIntegration**
- CRM provider connections (HubSpot, Salesforce)
- OAuth token storage
- Status tracking
- Relations: organization

**CRMAuditLog**
- Immutable audit trail for CRM operations
- Tracks: operation_type, payload, response, status
- Relations: organization, meeting, user

### Key Features

- **Multi-tenancy**: All tables include `org_id` for strict data isolation
- **Hebrew Support**: All string fields support UTF-8 encoding
- **Structured Data**: Meeting summaries stored as JSON following Data Contract
- **Audit Trail**: Complete logging of CRM operations
- **Error Tracking**: Processing errors stored in JSON format

## 📚 Documentation

- **Master Specification**: `docs/master_spec.md`
- **Implementation Log**: `docs/IMPLEMENTATION_LOG.md`
- **QA Audit Report**: `QA_AUDIT_REPORT.md`
- **Module 2 Details**: `MODULE_2_IMPLEMENTATION.md`

## 🏗️ Architecture Notes

- **Multi-tenancy**: Row-level isolation via `org_id`
- **Async-First**: All operations use async/await patterns
- **Type Safety**: Pydantic models for validation
- **Error Handling**: Comprehensive logging to database
- **Data Contract**: Strict JSON schema compliance

## 🔒 Security & Compliance

- Zero Retention Policy: Audio files deleted after 24 hours (configurable)
- Audit Trail: Immutable logs of all CRM operations
- Data Isolation: Strict multi-tenant architecture
- Human-in-the-Loop: Approval required before CRM sync

## 📝 License

[Add your license here]
