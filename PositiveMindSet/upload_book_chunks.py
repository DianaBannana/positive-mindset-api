import os
import fitz  # PyMuPDF

import fitz  # PyMuPDF
from supabase import create_client, Client
import uuid
from datetime import datetime


url = "https://fumjvitdvwsnrcjkitpm.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ1bWp2aXRkdndzbnJjamtpdHBtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDk1MjYxNiwiZXhwIjoyMDYwNTI4NjE2fQ.LOmTq5EbRE5mUDe7Cz9j2GEbCRZRLhzejpaKYbDs5q8"

# Supabase setup
supabase: Client = create_client(url, key)

def extract_chunks_from_pdf(pdf_path, chunk_size=500):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    words = full_text.split()
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

def upload_chunks(pdf_path, source_name):
    chunks = extract_chunks_from_pdf(pdf_path)
    for chunk in chunks:
        supabase.table("book_chunks").insert({
            "id": str(uuid.uuid4()),
            "source": source_name,
            "content": chunk,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    print(f"✅ Uploaded {len(chunks)} chunks from {source_name}")

# === Example Usage ===
upload_chunks("/Users/diana/Documents/PositiveMindSet/books/Mindset-The-New-Psychology-Bill-Gates-Success-Dweck.pdf", "Mindset-The-New-Psychology-Bill-Gates-Success-Dweck")
