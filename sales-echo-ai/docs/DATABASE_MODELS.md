# Database Models Reference

This document provides a comprehensive reference for all database models in SalesEcho AI. Use this as a reference for other agents working on the codebase.

**Database**: PostgreSQL (via Supabase)  
**ORM**: Prisma  
**Schema File**: `schema.prisma`

---

## Model Overview

The database consists of 6 core models, all designed with multi-tenancy in mind:

1. **Organization** - Root tenant entity
2. **User** - Sales reps and administrators
3. **Meeting** - Core meeting entity with transcripts and summaries
4. **Correction** - Feedback loop for AI improvement
5. **CRMIntegration** - CRM provider connections
6. **CRMAuditLog** - Immutable audit trail

---

## Organization

**Table**: `organizations`  
**Purpose**: Root entity for multi-tenancy. All other entities belong to an organization.

**Fields**:
- `id` (UUID, Primary Key)
- `name` (String, 255 chars)
- `settings` (JSON, nullable) - Org-specific config: data_residency, token_caps, feature_flags
- `created_at` (Timestamp with timezone)
- `updated_at` (Timestamp with timezone)

**Relations**:
- `users` - One-to-Many
- `meetings` - One-to-Many
- `corrections` - One-to-Many
- `crm_integrations` - One-to-Many
- `crm_audit_logs` - One-to-Many

**Indexes**: None (UUID primary key is indexed by default)

**Usage Notes**:
- Every query should filter by `org_id` for data isolation
- Settings JSON can store org-specific configurations

---

## User

**Table**: `users`  
**Purpose**: Sales representatives and administrators. Auth0/Clerk ready.

**Fields**:
- `id` (UUID, Primary Key)
- `org_id` (UUID, Foreign Key → Organization)
- `auth0_id` (String, 255, nullable, unique) - Auth0 user ID
- `clerk_id` (String, 255, nullable, unique) - Clerk user ID (alternative)
- `email` (String, 255)
- `name` (String, 255)
- `role` (String, 50, default: "sales_rep") - Values: sales_rep, admin, manager
- `created_at` (Timestamp with timezone)
- `updated_at` (Timestamp with timezone)

**Relations**:
- `organization` - Many-to-One
- `meetings` - One-to-Many
- `corrections` - One-to-Many
- `crm_audit_logs` - One-to-Many

**Indexes**:
- `org_id` - For multi-tenant queries
- `auth0_id` - For Auth0 lookups
- `clerk_id` - For Clerk lookups

**Usage Notes**:
- Supports both Auth0 and Clerk authentication
- Role-based access control (RBAC) via `role` field
- Always filter by `org_id` for multi-tenant queries

---

## Meeting

**Table**: `meetings`  
**Purpose**: Core entity storing meeting transcripts, audio, and AI-generated summaries.

**Fields**:

**Identifiers**:
- `id` (UUID, Primary Key)
- `org_id` (UUID, Foreign Key → Organization)
- `user_id` (UUID, Foreign Key → User)
- `client_name` (String, 255, nullable)
- `client_id` (UUID, nullable) - Optional CRM contact ID

**Audio & Transcript**:
- `audio_url` (Text, nullable) - S3 or storage URL
- `transcript` (Text, nullable) - Full transcript (UTF-8 for Hebrew/English)
- `transcript_raw` (JSON, nullable) - Raw STT output with timestamps, speaker diarization

**Audio Deletion (Zero Retention Policy)**:
- `audio_deleted_at` (Timestamp, nullable)
- `audio_deletion_scheduled_at` (Timestamp, nullable)
- `retention_policy_hours` (Integer, nullable) - Default 24, configurable per org

**AI Summary**:
- `summary` (JSON, nullable) - Structured Tachles summary (Data Contract format)
- `summary_text` (Text, nullable) - Human-readable summary text (Hebrew/English)

**Processing**:
- `processing_errors` (JSON, nullable) - Array of errors during STT/LLM processing

**Status & Metadata**:
- `status` (String, 50, default: "pending") - Values: pending, processed, reviewed, synced, error
- `language_mix` (String, 20, nullable) - e.g., "he-IL/en-US"
- `duration_seconds` (Integer, nullable)
- `confidence_score` (Double Precision, nullable) - Overall confidence 0-1

**Review & Sync (Human-in-the-Loop)**:
- `reviewed_at` (Timestamp, nullable)
- `reviewed_by` (UUID, nullable, Foreign Key → User)
- `approved_for_sync` (Boolean, default: false) - **Required before CRM sync**
- `synced_to_crm` (Boolean, default: false)
- `synced_at` (Timestamp, nullable)
- `sync_status` (String, 50, nullable) - Values: pending, success, failed, retrying

**CRM Sync Retry**:
- `sync_retry_count` (Integer, default: 0)
- `sync_error_message` (Text, nullable)
- `sync_scheduled_at` (Timestamp, nullable)

**Timestamps**:
- `created_at` (Timestamp with timezone)
- `updated_at` (Timestamp with timezone)

**Relations**:
- `organization` - Many-to-One
- `user` - Many-to-One
- `corrections` - One-to-Many
- `crm_audit_logs` - One-to-Many

**Indexes**:
- `org_id` - Multi-tenant queries
- `user_id` - User's meetings
- `status` - Status filtering
- `created_at` - Time-based queries
- `[org_id, client_id, created_at]` - Context retention ("last 3 meetings with client")

**Usage Notes**:
- `summary` JSON must conform to Data Contract (see `app/models/meeting_models.py`)
- `processing_errors` is an array of error objects: `[{"stage": "...", "error_type": "...", "error_message": "...", "timestamp": "..."}]`
- Always check `approved_for_sync` before syncing to CRM
- Audio files should be deleted per retention policy

---

## Correction

**Table**: `corrections`  
**Purpose**: Feedback loop for AI improvement. Tracks manual corrections made by users.

**Fields**:
- `id` (UUID, Primary Key)
- `org_id` (UUID, Foreign Key → Organization)
- `user_id` (UUID, Foreign Key → User) - User who made the correction
- `meeting_id` (UUID, Foreign Key → Meeting)

**Correction Data**:
- `field_name` (String, 100) - e.g., "deal_value", "action_item", "summary_text"
- `old_value` (JSON, nullable) - Original AI-generated value
- `new_value` (JSON, nullable) - User-corrected value
- `field_path` (String, 255, nullable) - JSON path for nested fields

**Context**:
- `source_snippet` (Text, nullable) - Relevant transcript snippet
- `confidence_before` (Double Precision, nullable) - AI confidence before correction
- `reason` (Text, nullable) - Optional: why the correction was made

**Timestamps**:
- `created_at` (Timestamp with timezone)

**Relations**:
- `organization` - Many-to-One
- `user` - Many-to-One
- `meeting` - Many-to-One

**Indexes**:
- `org_id` - Multi-tenant queries
- `meeting_id` - Meeting's corrections
- `field_name` - Field-based analysis

**Usage Notes**:
- Used to improve AI prompts in future iterations
- Can track corrections at any level of the summary structure
- `field_path` supports nested JSON paths (e.g., "content.crm_entities.deal_value")

---

## CRMIntegration

**Table**: `crm_integrations`  
**Purpose**: Stores CRM provider connections and OAuth tokens.

**Fields**:
- `id` (UUID, Primary Key)
- `org_id` (UUID, Foreign Key → Organization)
- `provider` (String, 50) - Values: "hubspot", "salesforce"
- `status` (String, 50, default: "active") - Values: active, inactive, error

**OAuth Tokens** (encrypted in production):
- `access_token` (Text, nullable)
- `refresh_token` (Text, nullable)
- `token_expires_at` (Timestamp, nullable)

**Configuration**:
- `config` (JSON, nullable) - Provider-specific settings
- `webhook_url` (Text, nullable)
- `last_sync_at` (Timestamp, nullable)

**Timestamps**:
- `created_at` (Timestamp with timezone)
- `updated_at` (Timestamp with timezone)

**Relations**:
- `organization` - Many-to-One

**Constraints**:
- `@@unique([org_id, provider])` - One integration per provider per org

**Indexes**:
- `org_id` - Multi-tenant queries
- `status` - Status filtering

**Usage Notes**:
- Each organization can have one integration per provider
- Tokens should be encrypted at rest in production
- `config` JSON can store provider-specific settings

---

## CRMAuditLog

**Table**: `crm_audit_logs`  
**Purpose**: Immutable audit trail for all CRM operations. Compliance requirement.

**Fields**:
- `id` (UUID, Primary Key)
- `org_id` (UUID, Foreign Key → Organization)
- `meeting_id` (UUID, Foreign Key → Meeting)
- `created_by` (UUID, Foreign Key → User) - User who triggered the sync

**Operation Details**:
- `crm_provider` (String, 50) - Values: "hubspot", "salesforce"
- `operation_type` (String, 50) - Values: "create_note", "update_deal", "create_contact", etc.
- `crm_entity_id` (String, 255, nullable) - ID in CRM system
- `crm_entity_type` (String, 50) - Values: "note", "deal", "contact", "timeline_event"

**Request/Response**:
- `payload` (JSON, nullable) - What was sent to CRM
- `response` (JSON, nullable) - Response from CRM

**Status**:
- `status` (String, 20) - Values: "success", "failed", "pending"
- `error_message` (Text, nullable)

**Traceability**:
- `transcript_source` (Text, nullable) - Link/reference to transcript for explainability

**Timestamps**:
- `created_at` (Timestamp with timezone)

**Relations**:
- `organization` - Many-to-One
- `meeting` - Many-to-One
- `user` - Many-to-One (SetNull on delete)

**Indexes**:
- `org_id` - Multi-tenant queries
- `meeting_id` - Meeting's audit logs
- `crm_provider` - Provider filtering
- `status` - Status filtering
- `created_at` - Time-based queries

**Usage Notes**:
- **Immutable**: Never update or delete audit logs
- Used for compliance and debugging
- Links back to original transcript for explainability
- `created_by` uses SetNull on delete (preserves audit trail even if user is deleted)

---

## Multi-Tenancy Pattern

**All models follow strict multi-tenancy**:

1. Every table includes `org_id` (UUID, Foreign Key → Organization)
2. All queries must filter by `org_id` for data isolation
3. Cascade deletes: Deleting an organization deletes all related data
4. Indexes on `org_id` for performance

**Query Pattern**:
```python
# Always filter by org_id
meetings = await prisma.meeting.find_many(
    where={"org_id": current_org_id}
)
```

---

## Data Types Reference

**UUID**: PostgreSQL UUID type (36 chars)  
**String**: VARCHAR with specified length  
**Text**: TEXT (unlimited length, UTF-8)  
**Integer**: INTEGER  
**Double Precision**: FLOAT/DOUBLE PRECISION (for confidence scores)  
**Boolean**: BOOLEAN  
**JSON**: JSONB (PostgreSQL JSON with indexing)  
**Timestamp**: TIMESTAMP WITH TIME ZONE (6 decimal places)

---

## Foreign Key Behavior

- **Cascade Delete**: Organization → User, Meeting, Correction, CRMIntegration, CRMAuditLog
- **Cascade Delete**: User → Meeting, Correction
- **Cascade Delete**: Meeting → Correction, CRMAuditLog
- **SetNull**: User → CRMAuditLog (preserves audit trail)

---

## Indexing Strategy

**Primary Keys**: All models use UUID primary keys (auto-indexed)  
**Foreign Keys**: All foreign keys are indexed  
**Query Patterns**: Indexes on frequently queried fields:
- `org_id` (all tables) - Multi-tenant filtering
- `status` (Meeting, CRMIntegration, CRMAuditLog) - Status filtering
- `created_at` (Meeting, CRMAuditLog) - Time-based queries
- Composite indexes for complex queries (e.g., context retention)

---

**Last Updated**: February 7, 2025  
**Schema Version**: 1.0 (Initial migration: `20260207174011_init_sales_echo_final`)
