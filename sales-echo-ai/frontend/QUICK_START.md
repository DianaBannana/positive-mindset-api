# Quick Start Guide - Frontend Setup

## ✅ Fixed Issues

1. **Middleware Simplified**: Temporarily disabled Supabase auth checks to allow app to load
2. **Error Handling**: Added graceful fallbacks for missing Supabase configuration
3. **CORS Enabled**: Backend is configured to allow requests from `http://localhost:3000`
4. **Login Page**: Now shows helpful error messages if Supabase is not configured

## 🚀 Getting Started

### Step 1: Create `.env.local` File

Create a file named `.env.local` in the `frontend/` directory with this content:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# FastAPI Backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**To get your Supabase values:**
1. Check your root `.env` file for `SUPABASE_URL` and `SUPABASE_ANON_KEY`
2. Copy those values to `.env.local` with the `NEXT_PUBLIC_` prefix
3. Or get them from your Supabase project dashboard:
   - Project URL: Settings → API → Project URL
   - Anon Key: Settings → API → Project API keys → `anon` `public`

### Step 2: Install Dependencies

```bash
cd frontend
npm install
```

### Step 3: Start the Backend

In a separate terminal:

```bash
# From project root
uvicorn main:app --reload
```

The backend should start on `http://localhost:8000` with CORS enabled for `http://localhost:3000`.

### Step 4: Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend should start on `http://localhost:3000`.

### Step 5: Access the Login Page

Open your browser and navigate to:
```
http://localhost:3000/login
```

## 🐛 Troubleshooting

### "Supabase is not configured" Error

This means your `.env.local` file is missing or has placeholder values. 

**Fix:**
1. Create `frontend/.env.local` if it doesn't exist
2. Add your actual Supabase URL and key (not the placeholders)
3. Restart the Next.js dev server

### 404 on Login Page

**Fix:**
1. Make sure you're running `npm run dev` from the `frontend/` directory
2. Check that `frontend/app/login/page.tsx` exists
3. Clear Next.js cache: `rm -rf frontend/.next` and restart

### CORS Errors

**Fix:**
1. Verify backend is running on port 8000
2. Check `main.py` has CORS middleware configured (already done)
3. Restart the backend server

### Cannot Read Root .env File

The root `.env` file is protected. You'll need to manually copy the Supabase values:

1. Open your root `.env` file
2. Find `SUPABASE_URL` and `SUPABASE_ANON_KEY`
3. Copy them to `frontend/.env.local` with `NEXT_PUBLIC_` prefix

## 📝 Current Status

- ✅ Middleware simplified (no auth blocking)
- ✅ Login page works without Supabase errors
- ✅ Error handling for missing Supabase config
- ✅ CORS configured in backend
- ⚠️ `.env.local` needs to be created manually (see Step 1)

## 🔄 Next Steps

Once you can see the login page:

1. **Configure Supabase**: Add your actual Supabase credentials to `.env.local`
2. **Re-enable Auth**: Update `middleware.ts` to restore auth checks
3. **Test Login**: Try logging in with a Supabase user

## 📞 Need Help?

- Check `frontend/README.md` for detailed documentation
- Check `frontend/ENV_SETUP.md` for environment setup details
