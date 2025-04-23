from supabase import create_client, Client

url = "https://fumjvitdvwsnrcjkitpm.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ1bWp2aXRkdndzbnJjamtpdHBtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDk1MjYxNiwiZXhwIjoyMDYwNTI4NjE2fQ.LOmTq5EbRE5mUDe7Cz9j2GEbCRZRLhzejpaKYbDs5q8"

supabase: Client = create_client(url, key)

def search_book_chunks(query: str, limit: int = 5) -> list:
    response = supabase.table("book_chunks") \
        .select("*") \
        .ilike("content", f"%{query}%") \
        .limit(limit) \
        .execute()

    if not response.data:
        return []

    return [r["content"] for r in response.data]
