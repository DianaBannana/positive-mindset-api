# Environment Variable Verification

## Required: NEXT_PUBLIC_DEV_ORG_ID

**File:** `frontend/.env.local`

**Required Content:**
```bash
NEXT_PUBLIC_DEV_ORG_ID="4eda10d2-761b-4b67-acef-7bbe10e7ce65"
```

## Verification Steps

1. **Check if file exists:**
   ```bash
   ls -la frontend/.env.local
   ```

2. **Verify the variable is set:**
   ```bash
   grep NEXT_PUBLIC_DEV_ORG_ID frontend/.env.local
   ```

3. **Restart Next.js dev server** after adding/updating the variable:
   ```bash
   cd frontend
   npm run dev
   ```

## Expected Console Output

When the dashboard loads, you should see in the browser console:
```
[fetchMeetings] FINAL ORG ID USED: 4eda10d2-761b-4b67-acef-7bbe10e7ce65
[fetchMeetings] ✅ Using DEV_ORG_ID from environment (original orgId was: aee81c7c-de21-4b66-bfb7-912063aee86e)
[fetchMeetings] Request URL: http://localhost:8000/api/v1/meetings?org_id=4eda10d2-761b-4b67-acef-7bbe10e7ce65
```

If you see a different org_id, the environment variable is not being loaded correctly.
