# Development ORG_ID Standardization

**Status:** ✅ Implemented  
**Date:** February 2025

## Overview

To ensure consistent `org_id` usage across upload and fetch operations during development, the system now uses standardized environment variables.

## Required Environment Variables

### Backend (`.env` in project root)

```bash
# Development Only: Standardized org_id for testing
# MUST be removed before production - replace with Auth middleware
DEV_ORG_ID="4eda10d2-761b-4b67-acef-7bbe10e7ce65"
```

### Frontend (`frontend/.env.local`)

```bash
# Development Only: Standardized org_id for testing
# MUST be removed before production - replace with Auth middleware
NEXT_PUBLIC_DEV_ORG_ID="4eda10d2-761b-4b67-acef-7bbe10e7ce65"
```

## How It Works

### Backend

1. **Upload Endpoint** (`/api/v1/meetings/upload`):
   - If `org_id` is invalid or "default-org-id", uses `DEV_ORG_ID` from environment
   - Ensures all uploaded meetings use the standardized org_id

2. **Get Meetings Endpoint** (`/api/v1/meetings`):
   - Strictly filters by provided `org_id`
   - If no meetings found and `DEV_ORG_ID` is set, uses it as fallback (DEV_ONLY)
   - **Security**: Never returns meetings from multiple orgs

### Frontend

1. **Dashboard Page** (`app/dashboard/page.tsx`):
   - Uses `NEXT_PUBLIC_DEV_ORG_ID` if session metadata doesn't have org_id
   - Ensures consistent org_id across all components

2. **MeetingTable** (`components/MeetingTable.tsx`):
   - Uses `NEXT_PUBLIC_DEV_ORG_ID` if orgId is invalid
   - Passes standardized org_id to `fetchMeetings()`

3. **AudioUpload** (`components/AudioUpload.tsx`):
   - Uses `NEXT_PUBLIC_DEV_ORG_ID` if orgId is invalid before upload
   - Ensures uploaded meetings use the standardized org_id

## Security Notes

⚠️ **DEV_ONLY_WARNING**: This is a development bypass for testing convenience.

**Before Production:**
- [ ] Remove `DEV_ORG_ID` and `NEXT_PUBLIC_DEV_ORG_ID` from environment variables
- [ ] Implement JWT-based authentication middleware
- [ ] Extract `org_id` from JWT token claims
- [ ] Remove all `DEV_ONLY_WARNING` code paths

## Verification

After setting the environment variables:

1. **Backend**: Restart the FastAPI server
2. **Frontend**: Restart the Next.js dev server
3. **Test**: Upload a meeting and verify it appears in the dashboard table
4. **Check Logs**: Look for `DEV_ONLY` warnings in console/logs

## Current Database Records

- **Standardized Org ID**: `4eda10d2-761b-4b67-acef-7bbe10e7ce65`
- **Previous Org ID (mismatch)**: `aee81c7c-de21-4b66-bfb7-912063aee86e` (should not be used)

All new uploads and fetches will use the standardized `DEV_ORG_ID`.
