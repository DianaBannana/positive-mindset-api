#!/bin/bash
# Prisma Setup Script for SalesEcho AI

echo "🔧 Setting up Prisma for SalesEcho AI..."

# Check if Prisma is installed
if ! command -v prisma &> /dev/null; then
    echo "⚠️  Prisma CLI not found. Installing via npx..."
    npx prisma generate
else
    echo "✅ Prisma CLI found"
fi

# Generate Prisma Client
echo "📦 Generating Prisma Client..."
prisma generate

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set. Please set it in your .env file"
    echo "   Example: DATABASE_URL=postgresql://user:password@localhost:5432/salesecho_db"
    exit 1
fi

# Create migration
echo "🗄️  Creating database migration..."
prisma migrate dev --name init

echo "✅ Prisma setup complete!"
