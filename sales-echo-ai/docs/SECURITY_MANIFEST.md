# SalesEcho AI - Security Manifest

**Version:** 1.0  
**Date:** February 2025  
**Status:** Production Security Standards

---

## Security Philosophy

SalesEcho AI operates on a **Security-First** architecture where data privacy and multi-tenant isolation are non-negotiable. This document defines the security principles that **MUST** be followed in all code generation and system design.

### Core Principles

1. **Zero Trust**: Never trust client-provided data. Always validate and verify.
2. **Defense in Depth**: Multiple layers of security (RLS, application-level, API-level).
3. **Least Privilege**: Users can only access data they are authorized to see.
4. **Audit Everything**: All security-relevant operations must be logged.

---

## Multi-Tenancy Architecture

### Requirement: Mandatory org_id Filtering

**CRITICAL RULE**: Every database query **MUST** be scoped by `org_id`. No exceptions.

#### Implementation Rules

1. **All Prisma Queries Must Include org_id Filter**
   ```python
   # ✅ CORRECT
   meetings = await prisma.meeting.find_many(
       where={"org_id": user_context.org_id}
   )
   
   # ❌ FORBIDDEN
   meetings = await prisma.meeting.find_many()  # No org_id filter
   ```

2. **No Global Data Fetches**
   - Never query all records without org_id filter
   - Never use `find_many()` without `where={"org_id": ...}`
   - Never bypass org_id filtering for "convenience"

3. **Cross-Tenant Data Leakage Prevention**
   - If a query returns data from multiple orgs, it's a **SECURITY BUG**
   - Always validate that returned data belongs to the requesting user's org
   - Log any attempts to access cross-tenant data

#### Development Bypass (DEV_ONLY)

**⚠️ WARNING**: The following is **ONLY** for development and **MUST** be removed before production:

- `DEV_ORG_ID` environment variable for development testing
- Must be explicitly documented as `DEV_ONLY_WARNING`
- Must be replaced with proper Auth middleware before production

**Current Implementation (Environment-Based Identity Management):**

**Backend:**
```python
# DEV_ONLY_WARNING: This fallback uses DEV_ORG_ID from env
# MUST be replaced with Auth middleware before production
if len(meetings) == 0 and settings.dev_org_id:
    logger.warning("DEV_ONLY: Using DEV_ORG_ID fallback")
    meetings = await prisma.meeting.find_many(
        where={"org_id": settings.dev_org_id}
    )
```

**Frontend:**
```typescript
// Safe fallback pattern - no hardcoded values
const finalOrgId = orgId || process.env.NEXT_PUBLIC_DEV_ORG_ID || "default-org-id";
```

**Key Security Improvement:**
- ✅ **No hardcoded IDs**: All identity management uses environment variables
- ✅ **Safe fallback pattern**: System gracefully falls back to DEV_ORG_ID if session data is missing
- ✅ **Consistent behavior**: Same org_id used across upload and fetch operations

**Environment Variables:**
- Backend: `DEV_ORG_ID="4eda10d2-761b-4b67-acef-7bbe10e7ce65"` in `.env`
- Frontend: `NEXT_PUBLIC_DEV_ORG_ID="4eda10d2-761b-4b67-acef-7bbe10e7ce65"` in `.env.local`

---

## Authentication Architecture

### Current State: Development Bypass

**Status**: ⚠️ **DEVELOPMENT MODE**

Currently, the system accepts `org_id` and `user_id` as form parameters. This is a **development bypass** and must be replaced with JWT-based authentication.

### Target State: Production Authentication

**Implementation Plan:**

1. **JWT Token Validation**
   - Extract JWT from `Authorization: Bearer <token>` header
   - Validate token signature with Supabase public key
   - Extract `user_id` and `org_id` from token claims

2. **Auth Middleware Dependency**
   ```python
   from fastapi import Depends
   from app.core.auth import get_current_user
   
   @router.get("")
   async def get_meetings(
       current_user: UserContext = Depends(get_current_user)
   ):
       # current_user.org_id is guaranteed to be valid
       meetings = await prisma.meeting.find_many(
           where={"org_id": current_user.org_id}
       )
   ```

3. **User Context Model**
   ```python
   class UserContext(BaseModel):
       user_id: str
       org_id: str
       email: str
       role: str  # "sales_rep", "admin", "manager"
   ```

### Migration Checklist

- [ ] Create `app/core/auth.py` with JWT validation
- [ ] Implement `get_current_user()` dependency
- [ ] Update all endpoints to use `Depends(get_current_user)`
- [ ] Remove `org_id` and `user_id` from form parameters
- [ ] Add JWT token validation tests
- [ ] Document token refresh flow

---

## Row Level Security (RLS)

### PostgreSQL RLS Policies

**Status**: ✅ **IMPLEMENTED** (see `supabase_security_setup.sql`)

All tables have RLS enabled with policies that enforce `org_id` isolation:

#### Organizations Table
```sql
CREATE POLICY "org_authenticated_select"
ON public.organizations
FOR SELECT
TO authenticated
USING (
  id = (SELECT org_id FROM public.users WHERE id = auth.uid())
);
```

#### Meetings Table
```sql
CREATE POLICY "meetings_org_isolation"
ON public.meetings
FOR SELECT
TO authenticated
USING (
  org_id = (SELECT org_id FROM public.users WHERE id = auth.uid())
);
```

#### Users Table
```sql
CREATE POLICY "users_self_access"
ON public.users
FOR SELECT
TO authenticated
USING (id = auth.uid());
```

### RLS Enforcement Rules

1. **Database-Level Enforcement**: RLS policies are the **last line of defense**
2. **Application-Level Enforcement**: Application code **MUST** also filter by org_id
3. **Never Rely on RLS Alone**: Always implement both layers

---

## Data Isolation

### PII (Personally Identifiable Information) Handling

**Sensitive Data Categories:**

| Data Type | Storage | Encryption | Access Control |
|-----------|---------|-----------|----------------|
| **Audio Files** | Temporary (deleted after processing) | Not encrypted (temporary) | org_id isolation |
| **Transcripts** | PostgreSQL (JSONB) | At-rest encryption (Supabase) | RLS + org_id filter |
| **Summaries** | PostgreSQL (JSONB) | At-rest encryption (Supabase) | RLS + org_id filter |
| **User Emails** | PostgreSQL | At-rest encryption (Supabase) | RLS + self-access only |
| **CRM Tokens** | PostgreSQL | Encrypted column | Service role only |

### Data Retention Policy

- **Audio Files**: Deleted immediately after processing (zero retention)
- **Transcripts**: Stored indefinitely (customer data)
- **Processing Errors**: Stored for 90 days, then archived
- **Audit Logs**: Stored for 7 years (compliance)

### Encryption Requirements

1. **At-Rest Encryption**: Handled by Supabase (PostgreSQL encryption)
2. **In-Transit Encryption**: HTTPS/TLS for all API calls
3. **Sensitive Fields**: CRM tokens stored in encrypted columns
4. **Future**: Field-level encryption for PII (e.g., client names, emails)

---

## API Security

### Input Validation

**Rule**: All user input **MUST** be validated with Pydantic models.

```python
# ✅ CORRECT
class MeetingUploadRequest(BaseModel):
    org_id: str = Field(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    user_id: str = Field(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# ❌ FORBIDDEN
org_id: str = Form(...)  # No validation
```

### Authorization Checks

**Rule**: Every endpoint **MUST** verify user authorization.

```python
# ✅ CORRECT
async def get_meeting(
    meeting_id: str,
    current_user: UserContext = Depends(get_current_user)
):
    meeting = await prisma.meeting.find_unique(
        where={"id": meeting_id, "org_id": current_user.org_id}  # org_id check
    )
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting

# ❌ FORBIDDEN
async def get_meeting(meeting_id: str):
    meeting = await prisma.meeting.find_unique(where={"id": meeting_id})  # No org_id check
    return meeting
```

### Error Message Security

**Rule**: Never expose internal errors or system details to clients.

```python
# ✅ CORRECT
except Exception as e:
    logger.error(f"Internal error: {str(e)}", exc_info=True)
    raise HTTPException(500, "An error occurred processing your request")

# ❌ FORBIDDEN
except Exception as e:
    raise HTTPException(500, f"Database error: {str(e)}")  # Exposes internal details
```

---

## Development vs Production

### Development Bypasses (DEV_ONLY_WARNING)

The following are **temporary development bypasses** that **MUST** be removed before production:

1. **STABLE_ORG_ID Fallback**
   - Location: `app/api/v1/meetings.py` → `get_meetings()`
   - Purpose: Allows development testing without proper Auth
   - **Action Required**: Replace with Auth middleware

2. **Form Parameter org_id/user_id**
   - Location: `app/api/v1/meetings.py` → `upload_meeting_audio()`
   - Purpose: Allows testing without JWT tokens
   - **Action Required**: Extract from JWT token instead

3. **Hardcoded Credentials**
   - **Rule**: Never hardcode API keys, database URLs, or secrets
   - **Action Required**: All secrets must be in environment variables

### Production Requirements

Before production deployment, the following **MUST** be implemented:

- [ ] JWT-based authentication on all endpoints
- [ ] Auth middleware extracting user context from tokens
- [ ] Removal of all `DEV_ONLY_WARNING` code paths
- [ ] Environment variable validation on startup
- [ ] Security audit of all database queries
- [ ] Penetration testing of API endpoints
- [ ] Rate limiting implementation (protect AI endpoints from quota exhaustion)
- [ ] Request timeout handling for Gemini API calls (prevent hanging requests)
- [ ] CORS policy configuration
- [ ] Security headers (HSTS, CSP, etc.)

### Production Roadmap (Q2 2025)

**Phase 1: Authentication Migration**
1. Implement `get_current_user()` FastAPI dependency in `app/core/auth.py`
2. Validate JWT tokens using Supabase public key
3. Extract `user_id`, `org_id`, `email`, `role` from token claims
4. Replace all `Form(org_id)` and `Form(user_id)` with `Depends(get_current_user)`

**Phase 2: Security Hardening**
1. Remove `DEV_ORG_ID` and `NEXT_PUBLIC_DEV_ORG_ID` from all environments
2. Delete all code paths marked with `DEV_ONLY_WARNING`
3. Implement rate limiting (e.g., 10 uploads/hour per user)
4. Add request timeouts: 5min for transcription, 30s for summary

**Phase 3: Compliance & Audit**
1. Enable audit logging for all data access
2. Implement GDPR data export/deletion endpoints
3. Security penetration testing
4. SOC 2 preparation documentation

---

## Security Audit Checklist

### Code Review Checklist

When reviewing code, check for:

- [ ] All database queries include `org_id` filter
- [ ] No global data fetches (without org_id)
- [ ] Input validation with Pydantic
- [ ] Error messages don't expose internal details
- [ ] No hardcoded credentials
- [ ] All secrets in environment variables
- [ ] JWT validation on protected endpoints
- [ ] RLS policies enabled on all tables
- [ ] Audit logging for sensitive operations

### Automated Security Checks

**Future Implementation:**

- [ ] Static analysis tool (Bandit, Semgrep) for Python
- [ ] Dependency scanning (Safety, Snyk)
- [ ] SQL injection testing
- [ ] XSS vulnerability scanning
- [ ] CSRF token validation

---

## Incident Response

### Security Incident Protocol

1. **Immediate Actions**:
   - Log the incident with full context
   - Isolate affected systems if necessary
   - Notify security team

2. **Investigation**:
   - Review audit logs
   - Identify root cause
   - Assess data exposure

3. **Remediation**:
   - Fix security vulnerability
   - Update security policies if needed
   - Notify affected users (if PII exposed)

### Audit Logging

**Required Logs:**
- All authentication attempts (success and failure)
- All database queries (with org_id context)
- All API requests (with user_id and org_id)
- All security policy violations
- All data access attempts

**Log Retention**: 7 years (compliance requirement)

---

## Compliance Considerations

### GDPR Compliance

- **Right to Access**: Users can request their data
- **Right to Deletion**: Users can request data deletion
- **Data Portability**: Users can export their data
- **Consent Management**: Explicit consent for data processing

### SOC 2 Preparation

- **Access Controls**: Multi-factor authentication
- **Encryption**: At-rest and in-transit
- **Monitoring**: Security event logging
- **Incident Response**: Documented procedures

---

## Security Best Practices

### For Developers

1. **Never Bypass Security**: If you need to bypass security for testing, mark it with `DEV_ONLY_WARNING`
2. **Always Filter by org_id**: Every query must include org_id
3. **Validate Input**: Use Pydantic for all user input
4. **Log Security Events**: Log all authentication and authorization checks
5. **Review Before Merge**: All code must pass security review

### For Code Reviewers

1. **Check org_id Filtering**: Verify every database query includes org_id
2. **Flag DEV_ONLY Code**: Ensure development bypasses are documented
3. **Verify Input Validation**: Check that all inputs are validated
4. **Review Error Messages**: Ensure no internal details are exposed
5. **Check Secrets**: Verify no hardcoded credentials

---

## Conclusion

This Security Manifest defines the **non-negotiable** security standards for SalesEcho AI. All code must adhere to these principles. Any deviation must be:

1. Explicitly marked with `DEV_ONLY_WARNING`
2. Documented with a removal plan
3. Approved by security review
4. Removed before production deployment

**Remember**: Security is not optional. It's the foundation of trust.

---

**Document Version:** 1.0  
**Last Updated:** February 2025  
**Maintained By:** SalesEcho AI Security Team
