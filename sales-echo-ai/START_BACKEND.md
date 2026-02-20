# 🚀 Start Backend Server - Quick Guide

## ❌ Problem
The backend is **NOT running**. Port 8000 is free, which means the FastAPI server needs to be started.

## ✅ Solution: Start the Backend

### Step 1: Open a NEW Terminal Window
Keep your frontend terminal running, and open a **second terminal** for the backend.

### Step 2: Navigate to Project Root
```bash
cd /Users/diana/Documents/sales-echo-ai
```

### Step 3: Activate Virtual Environment (if you have one)
```bash
# If you created a venv:
source venv/bin/activate

# Or if using conda:
# conda activate sales-echo-ai
```

### Step 4: Install Dependencies (if not already installed)
```bash
pip install -r requirements.txt
```

### Step 5: Start the Backend Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Verify Backend is Running
You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 7: Test Backend Health
Open a browser and go to:
```
http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "service": "SalesEcho AI",
  "version": "1.0.0"
}
```

## 📋 Quick Start Command (One Line)

```bash
cd /Users/diana/Documents/sales-echo-ai && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔍 Troubleshooting

### Error: "Could not import module 'main'"
- Make sure you're in the project root directory (`/Users/diana/Documents/sales-echo-ai`)
- The `main.py` file should be in the root, not in `app/`

### Error: "FFmpeg is not installed"
- Install FFmpeg:
  ```bash
  # macOS
  brew install ffmpeg
  
  # Verify
  ffmpeg -version
  ```

### Error: "Module not found"
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### Error: "Port 8000 already in use"
- Kill the process using port 8000:
  ```bash
  lsof -ti:8000 | xargs kill -9
  ```
- Or use a different port:
  ```bash
  uvicorn main:app --reload --port 8001
  ```
- Then update `frontend/.env.local`:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8001
  ```

## ✅ Success Checklist

- [ ] Backend terminal shows "Uvicorn running on http://0.0.0.0:8000"
- [ ] `http://localhost:8000/health` returns JSON response
- [ ] `http://localhost:8000/docs` shows Swagger UI
- [ ] Frontend can now upload files without network error

## 🎯 Expected Result

Once the backend is running:
1. Go back to your frontend at `http://localhost:3000/dashboard`
2. Try uploading a file again
3. You should see progress bar and success message
4. The file will be processed and appear in the meetings table

---

**Note**: You need **TWO terminals running**:
- **Terminal 1**: Frontend (`cd frontend && npm run dev`)
- **Terminal 2**: Backend (`cd /Users/diana/Documents/sales-echo-ai && uvicorn main:app --reload`)
