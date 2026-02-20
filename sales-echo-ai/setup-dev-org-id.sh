#!/bin/bash
# Setup script to add DEV_ORG_ID to environment files

DEV_ORG_ID="4eda10d2-761b-4b67-acef-7bbe10e7ce65"

# Frontend .env.local
FRONTEND_ENV="frontend/.env.local"
if [ -f "$FRONTEND_ENV" ]; then
    # Check if variable already exists
    if ! grep -q "NEXT_PUBLIC_DEV_ORG_ID" "$FRONTEND_ENV"; then
        echo "" >> "$FRONTEND_ENV"
        echo "# Development Only: Standardized org_id for POC testing" >> "$FRONTEND_ENV"
        echo "NEXT_PUBLIC_DEV_ORG_ID='$DEV_ORG_ID'" >> "$FRONTEND_ENV"
        echo "✅ Added NEXT_PUBLIC_DEV_ORG_ID to $FRONTEND_ENV"
    else
        echo "⚠️  NEXT_PUBLIC_DEV_ORG_ID already exists in $FRONTEND_ENV"
        # Update it to ensure it has the correct value
        sed -i.bak "s|NEXT_PUBLIC_DEV_ORG_ID=.*|NEXT_PUBLIC_DEV_ORG_ID='$DEV_ORG_ID'|" "$FRONTEND_ENV"
        echo "✅ Updated NEXT_PUBLIC_DEV_ORG_ID in $FRONTEND_ENV"
    fi
else
    # Create new file
    cat > "$FRONTEND_ENV" << EOF
# Development Only: Standardized org_id for POC testing
NEXT_PUBLIC_DEV_ORG_ID='$DEV_ORG_ID'
EOF
    echo "✅ Created $FRONTEND_ENV with NEXT_PUBLIC_DEV_ORG_ID"
fi

# Backend .env (root directory)
BACKEND_ENV=".env"
if [ -f "$BACKEND_ENV" ]; then
    # Check if variable already exists
    if ! grep -q "^DEV_ORG_ID" "$BACKEND_ENV"; then
        echo "" >> "$BACKEND_ENV"
        echo "# Development Only: Standardized org_id for POC testing" >> "$BACKEND_ENV"
        echo "DEV_ORG_ID='$DEV_ORG_ID'" >> "$BACKEND_ENV"
        echo "✅ Added DEV_ORG_ID to $BACKEND_ENV"
    else
        echo "⚠️  DEV_ORG_ID already exists in $BACKEND_ENV"
        # Update it to ensure it has the correct value
        sed -i.bak "s|^DEV_ORG_ID=.*|DEV_ORG_ID='$DEV_ORG_ID'|" "$BACKEND_ENV"
        echo "✅ Updated DEV_ORG_ID in $BACKEND_ENV"
    fi
else
    # Create new file
    cat > "$BACKEND_ENV" << EOF
# Development Only: Standardized org_id for POC testing
DEV_ORG_ID='$DEV_ORG_ID'
EOF
    echo "✅ Created $BACKEND_ENV with DEV_ORG_ID"
fi

echo ""
echo "🎉 Environment setup complete!"
echo ""
echo "⚠️  IMPORTANT: Restart your servers for changes to take effect:"
echo "   - Frontend: Stop and restart 'npm run dev'"
echo "   - Backend: Stop and restart 'python3 -m uvicorn main:app --reload --port 8000'"
