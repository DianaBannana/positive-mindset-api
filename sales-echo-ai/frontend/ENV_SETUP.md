# Frontend Environment Setup

## Quick Setup

Create a `.env.local` file in the `frontend/` directory with the following content:

```env
# Supabase Configuration
# Copy these values from your root .env file and prefix with NEXT_PUBLIC_
NEXT_PUBLIC_SUPABASE_URL=<your-supabase-project-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>

# FastAPI Backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Manual Setup Instructions

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Create the `.env.local` file**:
   ```bash
   touch .env.local
   ```

3. **Add the following content** (replace placeholders with actual values from your Supabase dashboard):
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://<your-project-ref>.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key-from-supabase>
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Get Supabase values from your root `.env` file**:
   - If your root `.env` has `SUPABASE_URL`, use that value for `NEXT_PUBLIC_SUPABASE_URL`
   - If your root `.env` has `SUPABASE_ANON_KEY`, use that value for `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **Important**: All frontend variables must be prefixed with `NEXT_PUBLIC_` to be accessible in the browser

## Using the Setup Script

Alternatively, you can use the provided setup script:

```bash
cd frontend
chmod +x setup-env.sh
./setup-env.sh
```

The script will attempt to read Supabase variables from the root `.env` file and create `.env.local` automatically.

## Verification

After creating `.env.local`, verify it contains:

- ✅ `NEXT_PUBLIC_SUPABASE_URL` (with your Supabase project URL)
- ✅ `NEXT_PUBLIC_SUPABASE_ANON_KEY` (with your Supabase anonymous key)
- ✅ `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Notes

- The `.env.local` file is gitignored and will not be committed to the repository
- All Next.js environment variables that need to be accessible in the browser must be prefixed with `NEXT_PUBLIC_`
- The API URL points to the FastAPI backend running on port 8000
