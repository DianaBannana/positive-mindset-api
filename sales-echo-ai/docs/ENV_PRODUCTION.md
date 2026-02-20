# SalesEcho AI - Production Environment Configuration

## Required Environment Variables

### Database (Supabase)

```bash
# Get from Supabase Dashboard → Settings → Database → Connection string
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?pgbouncer=true
DIRECT_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
```

### Supabase Auth

```bash
# Get from Supabase Dashboard → Settings → API
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=eyJ...your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=eyJ...your_service_role_key_here
```

### AI Services

```bash
# Get from Google AI Studio: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIza...your_gemini_key_here
```

### Application Settings

```bash
# Set to empty in production to disable dev fallbacks
DEV_ORG_ID=
DEV_USER_ID=

# Environment mode
ENVIRONMENT=production
DEBUG=false

# Server configuration
HOST=0.0.0.0
PORT=8000
```

### Security

```bash
# Generate with: openssl rand -hex 32
JWT_SECRET=your_jwt_secret_here_32_chars_min
WEBHOOK_SECRET=your_webhook_secret_here

# CORS (comma-separated list of allowed origins)
CORS_ORIGINS=https://salesecho.ai,https://app.salesecho.ai
```

---

## Railway Deployment

### 1. Connect Repository

1. Go to [Railway](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect the Dockerfile

### 2. Add Environment Variables

In Railway dashboard → Variables:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Supabase connection string |
| `GEMINI_API_KEY` | Your Gemini API key |
| `SUPABASE_URL` | Your Supabase URL |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `ENVIRONMENT` | `production` |
| `DEV_ORG_ID` | (leave empty) |

### 3. Add PostgreSQL Service

If using Railway's PostgreSQL instead of Supabase:

1. Click "New Service" → "PostgreSQL"
2. Railway will auto-set `DATABASE_URL`

### 4. Deploy

Railway will auto-deploy on push to `main` branch.

---

## Vercel Deployment (Frontend)

### 1. Connect Repository

1. Go to [Vercel](https://vercel.com)
2. Click "Import Project"
3. Select your repository
4. Set root directory to `frontend`

### 2. Add Environment Variables

In Vercel dashboard → Settings → Environment Variables:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anon key |
| `NEXT_PUBLIC_API_URL` | Your Railway backend URL |

### 3. Configure Build

- Framework: Next.js
- Build Command: `npm run build`
- Output Directory: `.next`

---

## Security Checklist

- [ ] `DEV_ORG_ID` is empty in production
- [ ] `DEBUG=false` in production
- [ ] All secrets are in environment variables (not code)
- [ ] CORS is restricted to production domains
- [ ] API keys have appropriate scopes/permissions
- [ ] Database connection uses SSL (`?sslmode=require`)

---

## Health Check Endpoint

The backend exposes a health check at `/health`:

```bash
curl https://your-api.railway.app/health
# Response: {"status": "healthy", "version": "1.0.0"}
```

---

## Monitoring

### Recommended Services

| Service | Purpose |
|---------|---------|
| [Sentry](https://sentry.io) | Error tracking |
| [Logflare](https://logflare.app) | Log aggregation |
| [UptimeRobot](https://uptimerobot.com) | Uptime monitoring |

### Sentry Setup

```bash
# Add to environment variables
SENTRY_DSN=https://...@sentry.io/...
```

```python
# In main.py (already configured)
import sentry_sdk
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
```

---

*Last updated: February 2026*
