#!/bin/bash
# Setup script to create .env.local from root .env file

FRONTEND_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$FRONTEND_DIR/.." && pwd)"

echo "Setting up frontend/.env.local from root .env file..."

# Check if root .env exists
if [ ! -f "$ROOT_DIR/.env" ]; then
    echo "Warning: Root .env file not found at $ROOT_DIR/.env"
    echo "Creating template .env.local file..."
fi

# Create .env.local file
cat > "$FRONTEND_DIR/.env.local" << 'EOF'
# Supabase Configuration
# These values should be prefixed with NEXT_PUBLIC_ for Next.js
EOF

# Try to read Supabase variables from root .env
if [ -f "$ROOT_DIR/.env" ]; then
    # Look for SUPABASE_URL or similar
    SUPABASE_URL=$(grep -E "^SUPABASE_URL=|^SUPABASE_PROJECT_URL=" "$ROOT_DIR/.env" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'" | head -1)
    SUPABASE_KEY=$(grep -E "^SUPABASE_ANON_KEY=|^SUPABASE_KEY=" "$ROOT_DIR/.env" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'" | head -1)
    
    if [ -n "$SUPABASE_URL" ]; then
        echo "NEXT_PUBLIC_SUPABASE_URL=$SUPABASE_URL" >> "$FRONTEND_DIR/.env.local"
        echo "✓ Found and added SUPABASE_URL"
    else
        echo "NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url_here" >> "$FRONTEND_DIR/.env.local"
        echo "⚠ SUPABASE_URL not found in root .env - please update manually"
    fi
    
    if [ -n "$SUPABASE_KEY" ]; then
        echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=$SUPABASE_KEY" >> "$FRONTEND_DIR/.env.local"
        echo "✓ Found and added SUPABASE_ANON_KEY"
    else
        echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here" >> "$FRONTEND_DIR/.env.local"
        echo "⚠ SUPABASE_ANON_KEY not found in root .env - please update manually"
    fi
else
    echo "NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url_herhttps://cerkjbxlqulnttyyvrtp.supabase.coe" >> "$FRONTEND_DIR/.env.local"
    echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_McBNmaRSDYgrU9OAaV3rvw_1e40uhBG >> "$FRONTEND_DIR/.env.local"
fi

# Add API URL
echo "" >> "$FRONTEND_DIR/.env.local"
echo "# FastAPI Backend URL" >> "$FRONTEND_DIR/.env.local"
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> "$FRONTEND_DIR/.env.local"

echo ""
echo "✓ Created $FRONTEND_DIR/.env.local"
echo ""
echo "Please verify the values are correct:"
echo "  - NEXT_PUBLIC_SUPABASE_URL"
echo "  - NEXT_PUBLIC_SUPABASE_ANON_KEY"
echo "  - NEXT_PUBLIC_API_URL"
echo ""
