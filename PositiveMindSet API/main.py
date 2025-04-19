from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import os

# === Setup Supabase connection ===
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://fumjvitdvwsnrcjkitpm.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ1bWp2aXRkdndzbnJjamtpdHBtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDk1MjYxNiwiZXhwIjoyMDYwNTI4NjE2fQ.LOmTq5EbRE5mUDe7Cz9j2GEbCRZRLhzejpaKYbDs5q8")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === FastAPI setup ===
app = FastAPI()

# Allow requests from anywhere (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
def search_chunks(query: str, limit: int = 5):
    response = supabase.table("book_chunks") \
        .select("*") \
        .ilike("content", f"%{query}%") \
        .limit(limit) \
        .execute()

    if not response.data:
        return {"results": []}

    return {
        "results": [{"chunk": r["content"], "source": r["source"]} for r in response.data]
    }
