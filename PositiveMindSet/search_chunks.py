from supabase import create_client, Client
import os

# === Set up your Supabase connection ===
url = "https://fumjvitdvwsnrcjkitpm.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ1bWp2aXRkdndzbnJjamtpdHBtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDk1MjYxNiwiZXhwIjoyMDYwNTI4NjE2fQ.LOmTq5EbRE5mUDe7Cz9j2GEbCRZRLhzejpaKYbDs5q8"
supabase: Client = create_client(url, key)

# === Simple keyword search ===
def search_chunks(query, limit=5):
    response = supabase.table("book_chunks") \
        .select("*") \
        .ilike("content", f"%{query}%") \
        .limit(limit) \
        .execute()

    if not response.data:
        print("No matching chunks found.")
        return []

    return [r["content"] for r in response.data]

# === Example usage ===
results = search_chunks("growth mindset", limit=3)

for i, chunk in enumerate(results):
    print(f"\n--- Result {i+1} ---\n{chunk}\n")
