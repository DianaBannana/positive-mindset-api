#!/usr/bin/env python3
"""
Script to create frontend/.env.local from root .env file
Reads Supabase variables and adds NEXT_PUBLIC_ prefix
"""

import os
from pathlib import Path

# Get paths
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
ENV_LOCAL_PATH = FRONTEND_DIR / ".env.local"
ROOT_ENV_PATH = ROOT_DIR / ".env"

print(f"Creating {ENV_LOCAL_PATH}...")

# Read root .env if it exists
supabase_url = None
supabase_key = None

if ROOT_ENV_PATH.exists():
    print(f"Reading {ROOT_ENV_PATH}...")
    with open(ROOT_ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if "SUPABASE_URL" in key.upper() and "NEXT_PUBLIC" not in key:
                        supabase_url = value
                        print(f"  Found: {key}")
                    elif "SUPABASE_ANON_KEY" in key.upper() or ("SUPABASE_KEY" in key.upper() and "ANON" in key.upper()):
                        supabase_key = value
                        print(f"  Found: {key}")
else:
    print(f"Warning: {ROOT_ENV_PATH} not found")

# Create .env.local content
env_content = """# Supabase Configuration
# These values are prefixed with NEXT_PUBLIC_ for Next.js browser access

"""

if supabase_url and supabase_url not in ["", "your_supabase_project_url_here"]:
    env_content += f"NEXT_PUBLIC_SUPABASE_URL={supabase_url}\n"
    print(f"✓ Added NEXT_PUBLIC_SUPABASE_URL")
else:
    env_content += "NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url_here\n"
    print("⚠ NEXT_PUBLIC_SUPABASE_URL not found - using placeholder")

if supabase_key and supabase_key not in ["", "your_supabase_anon_key_here"]:
    env_content += f"NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_key}\n"
    print(f"✓ Added NEXT_PUBLIC_SUPABASE_ANON_KEY")
else:
    env_content += "NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here\n"
    print("⚠ NEXT_PUBLIC_SUPABASE_ANON_KEY not found - using placeholder")

env_content += """
# FastAPI Backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000
"""

# Write .env.local
try:
    with open(ENV_LOCAL_PATH, "w") as f:
        f.write(env_content)
    print(f"\n✓ Created {ENV_LOCAL_PATH}")
    print("\nPlease verify the values are correct before running the app.")
except PermissionError:
    print(f"\n❌ Permission denied: Cannot write to {ENV_LOCAL_PATH}")
    print("Please create the file manually with the following content:")
    print("\n" + "="*50)
    print(env_content)
    print("="*50)
except Exception as e:
    print(f"\n❌ Error: {e}")
