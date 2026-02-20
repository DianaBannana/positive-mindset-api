# Login Fix - Supabase Configuration

## ✅ Fixed: .env.local File Required

The `.env.local` file must be created with your Supabase credentials:

```env
NEXT_PUBLIC_SUPABASE_URL=https://<your-project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **Security Note**: Get these values from your Supabase dashboard. Never commit actual credentials to the repository.

## 🔄 Next Steps

### 1. Restart the Next.js Dev Server

**IMPORTANT**: Environment variables are only loaded when the server starts. You MUST restart:

```bash
# Stop the current dev server (Ctrl+C)
# Then restart:
cd frontend
npm run dev
```

### 2. Test Login

1. Open `http://localhost:3000/login`
2. Open browser console (F12)
3. You should see:
   ```
   [Login Page] NEXT_PUBLIC_SUPABASE_URL: ✅ DEFINED
   [Login Page] NEXT_PUBLIC_SUPABASE_ANON_KEY: ✅ DEFINED
   ```
4. Enter your credentials
5. Click "Sign In"

### 3. Expected Behavior

- ✅ No "Supabase is not configured" error
- ✅ Form doesn't clear on submit
- ✅ Error messages show in red banner if credentials are wrong
- ✅ Redirects to `/dashboard` on success

## 🐛 If Still Not Working

### Check Console Logs

Open browser console (F12) and look for:
- `[Login Page] NEXT_PUBLIC_SUPABASE_URL: ✅ DEFINED` or `❌ UNDEFINED`
- `[Login] Form submitted`
- `[Login] Full response: {...}`

### Verify .env.local File

```bash
cd frontend
cat .env.local
```

Should show:
- `NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>`
- `NEXT_PUBLIC_API_URL=http://localhost:8000`

### Common Issues

1. **"Still showing undefined"**
   - Make sure you restarted the dev server
   - Check file is in `frontend/.env.local` (not root)
   - No quotes around values
   - No spaces around `=`

2. **"Invalid credentials"**
   - Verify user exists in Supabase dashboard
   - Reset password in Supabase if needed

3. **"Network error"**
   - Check Supabase URL is correct
   - Verify internet connection
   - Check Supabase dashboard is accessible

## 📝 Getting Credentials

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings → API
4. Copy:
   - **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
   - **anon/public key** → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

---

**Last Updated**: 2026-02-20
