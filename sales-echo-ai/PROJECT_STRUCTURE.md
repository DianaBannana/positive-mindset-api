# SalesEcho AI - Project Structure Documentation

> **Your GPS for navigating the SalesEcho AI codebase**

This document provides a comprehensive map of the entire project, including folder hierarchies, file descriptions, tech stack, and data flow.

---

## 📁 Project Tree

```
sales-echo-ai/
│
├── 📄 main.py                          # FastAPI application entry point
├── 📄 requirements.txt                 # Python dependencies
├── 📄 schema.prisma                    # Prisma database schema definition
├── 📄 .env                             # Environment variables (not in git)
├── 📄 README.md                        # Project overview and setup guide
├── 📄 PROJECT_STRUCTURE.md             # This file
│
├── 📂 app/                             # Backend Python package
│   ├── __init__.py                     # Package marker
│   │
│   ├── 📂 api/                         # API endpoints (REST routes)
│   │   ├── __init__.py                 # Package marker
│   │   └── 📂 v1/                      # API version 1
│   │       ├── __init__.py             # Package marker
│   │       └── meetings.py             # Meeting upload & CRUD endpoints
│   │
│   ├── 📂 core/                        # Core configuration & infrastructure
│   │   ├── __init__.py                 # Package marker
│   │   ├── config.py                   # Settings management (Pydantic) - includes STABLE_ORG_ID (DEV_ONLY)
│   │   ├── database.py                 # Prisma client connection & lifecycle
│   │   ├── auth.py                     # Authentication middleware (JWT validation placeholder for production)
│   │   ├── utils.py                    # Utility functions (slug generation, etc.)
│   │   └── prompts.py                  # Centralized registry for LLM prompts & business logic
│   │
│   ├── 📂 models/                      # Pydantic data models
│   │   ├── __init__.py                 # Package marker
│   │   └── meeting_models.py           # Tachles summary schemas & validation
│   │
│   ├── 📂 services/                    # Business logic layer
│   │   ├── __init__.py                 # Package marker
│   │   ├── ai_service.py               # Gemini 1.5 Flash integration (summary generation with fallback)
│   │   └── transcription_service.py    # Audio processing with FFmpeg & Gemini 1.5 Flash STT
│   │
│   └── 📂 static/                      # Static assets (currently empty)
│
├── 📂 frontend/                        # Next.js frontend application
│   ├── 📄 package.json                 # Node.js dependencies
│   ├── 📄 tsconfig.json                # TypeScript configuration
│   ├── 📄 next.config.js               # Next.js configuration
│   ├── 📄 tailwind.config.ts            # Tailwind CSS configuration
│   ├── 📄 .env.local                   # Frontend environment variables
│   │
│   ├── 📂 app/                         # Next.js App Router pages
│   │   ├── layout.tsx                  # Root layout (providers, metadata)
│   │   ├── page.tsx                    # Home page (redirects to login)
│   │   ├── globals.css                 # Global Tailwind styles
│   │   │
│   │   ├── 📂 login/                   # Authentication pages
│   │   │   └── page.tsx                # Login page component
│   │   │
│   │   └── 📂 dashboard/               # Protected dashboard routes
│   │       ├── layout.tsx              # Dashboard layout (sidebar, auth check)
│   │       ├── page.tsx                # Main dashboard (meetings list)
│   │       ├── 📂 organizations/       # Admin-only organizations page
│   │       │   └── page.tsx            # Organizations management
│   │       └── 📂 analytics/            # Analytics placeholder
│   │           └── page.tsx            # Analytics dashboard
│   │
│   ├── 📂 components/                  # React components
│   │   ├── AudioUpload.tsx             # Drag-and-drop audio upload component
│   │   ├── MeetingTable.tsx            # Meetings list table with status badges, error handling & org_id debugging
│   │   ├── Sidebar.tsx                 # Dashboard navigation sidebar
│   │   └── 📂 ui/                      # Shadcn/ui component library
│   │       ├── button.tsx              # Button component
│   │       ├── badge.tsx                # Badge component
│   │       ├── card.tsx                 # Card component (used in meeting details)
│   │       └── table.tsx                # Table components
│   │
│   ├── 📂 lib/                         # Frontend utilities & clients
│   │   ├── api.ts                      # FastAPI backend client functions
│   │   ├── supabase.ts                 # Supabase browser client (client components)
│   │   ├── supabase-server.ts         # Supabase server client (server components)
│   │   └── utils.ts                    # Utility functions (cn helper, etc.)
│   │
│   ├── 📄 middleware.ts                # Next.js middleware (auth protection)
│   ├── 📄 README.md                    # Frontend setup instructions
│   └── 📄 QUICK_START.md               # Quick start guide
│
├── 📂 docs/                            # Project documentation
│   ├── master_spec.md                  # Master product specification
│   ├── PRD.md                          # Product Requirements Document
│   ├── TECH_SPEC.md                    # Technical specification
│   ├── USER_STORIES.md                 # User stories & acceptance criteria
│   ├── ARCHITECTURE.md                 # System architecture & Mermaid diagrams
│   ├── IDD.md                          # Interface Design Document (API specs)
│   ├── IMPLEMENTATION_LOG.md           # Implementation history & decisions
│   ├── DATABASE_MODELS.md              # Database schema documentation
│   ├── DOCUMENTATION_ALIGNMENT.md      # Documentation consistency check
│   ├── POC_SUMMARY.md                  # Proof of Concept Summary
│   └── SECURITY_MANIFEST.md            # Production security standards & multi-tenancy architecture
│
├── 📂 migrations/                      # Prisma database migrations
│   ├── 20260207174011_init_sales_echo_final/
│   │   └── migration.sql               # Initial schema migration
│   ├── 20260212220000_add_usage_tracking_subscription_plan/
│   │   └── migration.sql               # Usage tracking migration
│   └── migration_lock.toml             # Migration lock file
│
├── 📂 tests/                            # Test suite
│   ├── __init__.py                     # Package marker
│   ├── mock_ai_test.py                 # Mock AI service tests
│   └── test_ai_pipeline.py             # AI pipeline integration tests
│
├── 📂 recordings/                      # Sample audio files (not in git)
│   └── *.m4a                           # Test recordings
│
└── 📄 supabase_security_setup.sql      # RLS policies & security setup script
```

---

## 🔧 Tech Stack Breakdown

### Backend (`app/` directory)
- **Framework**: FastAPI (Python 3.9+)
- **Database ORM**: Prisma Client Python
- **Database**: PostgreSQL (via Supabase)
- **AI Services**:
  - Google Gemini 1.5 Flash (Speech-to-Text & Summary generation - Gemini-only pipeline, using 1.5 Flash for higher dev quotas)
  - Fallback summary mechanism for short transcripts or API failures
- **Audio Processing**: FFmpeg (via subprocess)
- **Validation**: Pydantic v2
- **HTTP Client**: httpx
- **Environment**: python-dotenv, pydantic-settings

### Frontend (`frontend/` directory)
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/ui
- **Icons**: Lucide React
- **Authentication**: Supabase Auth Helpers
- **HTTP Client**: Native Fetch API
- **State Management**: React Hooks (useState, useEffect)

### Database & Infrastructure
- **Database**: Supabase (PostgreSQL)
- **ORM**: Prisma
- **Migrations**: Prisma Migrate
- **Security**: Row Level Security (RLS) policies
- **Storage**: Supabase Storage (for future audio file storage)

---

## 📝 Major File Descriptions

### Backend Files

| File | Responsibility |
|------|----------------|
| `main.py` | FastAPI application entry point; initializes app, CORS, routes, and lifespan events (FFmpeg check, DB connection) |
| `app/api/v1/meetings.py` | REST API endpoints for meeting upload (`POST /api/v1/meetings/upload`) and retrieval |
| `app/core/config.py` | Loads environment variables and provides app-wide settings via Pydantic |
| `app/core/database.py` | Prisma client initialization and database connection lifecycle management |
| `app/core/utils.py` | Utility functions including slug generation for organization names |
| `app/core/prompts.py` | Prompts registry centralizing all LLM/business prompts (sales insights, Tachles, etc.) |
| `app/models/meeting_models.py` | Pydantic schemas for Tachles summary structure (main_goals, action_items, sentiment, etc.) |
| `app/services/ai_service.py` | Gemini 1.5 Flash summary generation with regex-based JSON extraction (handles markdown, UTF-8 safe), explicit JSON safety prompts, and resilient fallback mechanism |
| `app/services/transcription_service.py` | Audio normalization (FFmpeg), Gemini 1.5 Flash STT with dynamic model discovery, usage tracking, and status updates |
| `app/core/prompts.py` | Centralized prompts registry (SALES_INSIGHTS_PROMPT_HE) - single source of truth for LLM business logic |

### Frontend Files

| File | Responsibility |
|------|----------------|
| `frontend/app/layout.tsx` | Root layout component providing global providers and metadata |
| `frontend/app/login/page.tsx` | Login page with Supabase authentication form |
| `frontend/app/dashboard/page.tsx` | Main dashboard displaying meetings table and upload component |
| `frontend/app/dashboard/layout.tsx` | Dashboard layout with sidebar navigation and session protection |
| `frontend/components/AudioUpload.tsx` | Drag-and-drop audio upload component with progress bar and error handling |
| `frontend/components/MeetingTable.tsx` | Meetings list table with status badges and refresh capability |
| `frontend/components/Sidebar.tsx` | Dashboard navigation sidebar with logout functionality |
| `frontend/lib/api.ts` | API client functions for communicating with FastAPI backend |
| `frontend/lib/supabase.ts` | Supabase browser client creation (for client components) |
| `frontend/lib/supabase-server.ts` | Supabase server client creation (for server components) |
| `frontend/middleware.ts` | Next.js middleware for route protection and session refresh |

### Configuration Files

| File | Responsibility |
|------|----------------|
| `schema.prisma` | Prisma schema defining database models (Organization, User, Meeting, etc.) |
| `requirements.txt` | Python package dependencies |
| `frontend/package.json` | Node.js package dependencies |
| `.env` | Backend environment variables (API keys, database URL) |
| `frontend/.env.local` | Frontend environment variables (Supabase URL, API URL) |

---

## 🔄 Data Flow: Upload → AI Processing → Database

### Step-by-Step Flow

```
1. USER UPLOADS AUDIO
   └─> frontend/components/AudioUpload.tsx
       ├─> Validates file type & size
       ├─> Gets Supabase session token
       └─> POST /api/v1/meetings/upload (FormData + Authorization header)

2. BACKEND RECEIVES REQUEST
   └─> app/api/v1/meetings.py (upload_meeting_audio)
       ├─> Validates file type
       ├─> Saves file to temp directory
       └─> Creates Meeting record (status: "PENDING")

3. AUDIO PRE-PROCESSING
   └─> app/services/transcription_service.py (transcribe_audio_with_fallback)
       └─> normalize_audio()
           ├─> Uses FFmpeg to convert to MP3, Mono, 16kHz, 64kbps
           └─> Returns normalized file path

4. TRANSCRIPTION (Gemini 1.5 Flash - Gemini-only pipeline)
   └─> app/services/transcription_service.py (_transcribe_with_gemini)
       ├─> Dynamic model discovery (client.models.list())
       ├─> Uploads audio to Google Gemini
       ├─> Calls Gemini 1.5 Flash with diarization prompt
       ├─> Extracts transcript with speaker diarization
       └─> Returns transcript JSON

5. SUMMARY GENERATION (Gemini 1.5 Flash with fallback)
   └─> app/services/ai_service.py (generate_summary)
       ├─> Short transcript check (< 20 chars) → returns fallback summary
       ├─> Combines SALES_INSIGHTS_PROMPT_HE + TACHLES_SYSTEM_PROMPT_V2
       ├─> Calls Gemini 1.5 Flash with explicit JSON safety instructions:
       │   * "Return only valid JSON object, no markdown, no code blocks"
       │   * "Ensure all strings are properly escaped for JSON compliance"
       │   * "Use \\\" for quotes, \\n for newlines"
       ├─> Regex-based JSON extraction (_extract_json_from_response):
       │   * Strips markdown code blocks (```json ... ```)
       │   * Finds content between first { and last } (handles embedded text)
       │   * Validates balanced braces
       │   * UTF-8 safe encoding
       ├─> Parses extracted JSON with json.loads(strict=False)
       ├─> Validates against TachlesSummary Pydantic model
       ├─> Extracts: summary_text, action_items, crm_entities, governance
       └─> Fallback summary on JSON/validation errors (ensures COMPLETED status)

7. DATABASE UPDATE
   └─> app/services/transcription_service.py
       ├─> Updates Meeting record:
       │   ├─> transcript: JSON transcript
       │   ├─> summary: TachlesSummary JSON
       │   ├─> status: "COMPLETED"
       │   ├─> duration_seconds: calculated from audio
       │   └─> language_mix: detected language
       ├─> Updates Organization.usage_minutes
       └─> Cleans up temporary audio file

8. FRONTEND REFRESH
   └─> frontend/components/AudioUpload.tsx (onUploadSuccess callback)
       └─> Triggers MeetingTable refresh
           └─> frontend/components/MeetingTable.tsx
               └─> Fetches updated meetings list from backend
```

### Visual Flow Diagram

```
┌─────────────────┐
│   User Browser  │
│  (Next.js App)  │
└────────┬────────┘
         │
         │ 1. POST /api/v1/meetings/upload
         │    (FormData + Bearer Token)
         ▼
┌─────────────────┐
│  FastAPI Backend │
│   (main.py)      │
└────────┬────────┘
         │
         │ 2. Save temp file
         │    Create Meeting (PENDING)
         ▼
┌─────────────────┐
│ Transcription   │
│   Service       │
└────────┬────────┘
         │
         ├─> 3. FFmpeg Normalization
         │    (MP3, Mono, 16kHz)
         │
         ├─> 4. Gemini 1.5 Flash STT
         │    └─> Success? ──┐
         │                   │
         │                   ▼
         │         ┌─────────────────┐
         │         │  AI Service      │
         │         │  (Gemini 1.5     │
         │         │   Flash Summary) │
         │         └────────┬────────┘
         │                  │
         │                  ▼
         │         ┌─────────────────┐
         │         │  Fallback        │
         │         │  Summary         │
         │         │  (if needed)     │
         │         └────────┬────────┘
         │                  │
         └──────────────────┘
                  │
                  │ 6. Generate Tachles Summary
                  │    (main_goals, action_items, etc.)
                  ▼
         ┌─────────────────┐
         │   Supabase DB    │
         │   (PostgreSQL)   │
         └────────┬────────┘
                  │
                  │ 7. Update Meeting:
                  │    - transcript
                  │    - summary
                  │    - status: COMPLETED
                  │    - usage_minutes
                  │
                  ▼
         ┌─────────────────┐
         │  Frontend Table  │
         │  (Auto-refresh)  │
         └──────────────────┘
```

---

## 🗂️ Key Directories Explained

### `app/` - Backend Package
The core Python backend following FastAPI best practices:
- **`api/`**: REST endpoints organized by version
- **`core/`**: Infrastructure (config, database, utilities)
- **`models/`**: Data validation schemas (Pydantic)
- **`services/`**: Business logic (AI processing, transcription)

### `frontend/` - Next.js Application
Modern React application using App Router:
- **`app/`**: Pages and routes (file-based routing)
- **`components/`**: Reusable React components
- **`lib/`**: Client-side utilities and API clients

### `docs/` - Documentation
Comprehensive project documentation:
- Specifications (PRD, Tech Spec, User Stories)
- Architecture diagrams (Mermaid)
- Implementation logs and decisions
- API documentation (IDD)

### `migrations/` - Database Migrations
Prisma-generated SQL migrations for schema changes.

### `tests/` - Test Suite
Unit and integration tests for AI pipeline and services.

---

## 🚀 Quick Navigation Guide

**Want to...**

- **Upload a file?** → `frontend/components/AudioUpload.tsx`
- **Process audio?** → `app/services/transcription_service.py`
- **Generate summary?** → `app/services/ai_service.py`
- **Add API endpoint?** → `app/api/v1/meetings.py`
- **Change database schema?** → `schema.prisma`
- **Update UI?** → `frontend/components/` or `frontend/app/`
- **Configure environment?** → `.env` (backend) or `frontend/.env.local` (frontend)
- **Understand architecture?** → `docs/ARCHITECTURE.md`
- **See API specs?** → `docs/IDD.md`

---

## 📚 Additional Resources

- **Setup Guide**: See `README.md` for installation instructions
- **Frontend Setup**: See `frontend/README.md` for Next.js setup
- **Architecture**: See `docs/ARCHITECTURE.md` for system diagrams
- **API Docs**: See `docs/IDD.md` for endpoint specifications
- **Tech Spec**: See `docs/TECH_SPEC.md` for technical details

---

**Last Updated**: 2026-02-12  
**Maintained By**: SalesEcho AI Development Team
