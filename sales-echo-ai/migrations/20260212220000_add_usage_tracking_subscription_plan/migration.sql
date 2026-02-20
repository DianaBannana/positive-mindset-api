-- Migration: Add usage tracking, subscription plan, and acknowledge existing slug column
-- This migration acknowledges the existing slug column and adds new fields

-- Acknowledge existing slug column (if it doesn't exist, create it; if it exists, do nothing)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'organizations' AND column_name = 'slug'
    ) THEN
        ALTER TABLE "organizations" ADD COLUMN "slug" VARCHAR(255);
        CREATE UNIQUE INDEX IF NOT EXISTS "organizations_slug_key" ON "organizations"("slug");
    END IF;
END $$;

-- Add slug index if it doesn't exist (in addition to unique constraint)
CREATE INDEX IF NOT EXISTS "organizations_slug_idx" ON "organizations"("slug");

-- Change usage_minutes from INTEGER to DOUBLE PRECISION (if it exists as INTEGER)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'organizations' 
        AND column_name = 'usage_minutes' 
        AND data_type = 'integer'
    ) THEN
        ALTER TABLE "organizations" ALTER COLUMN "usage_minutes" TYPE DOUBLE PRECISION USING "usage_minutes"::double precision;
        ALTER TABLE "organizations" ALTER COLUMN "usage_minutes" SET DEFAULT 0.0;
    ELSIF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'organizations' AND column_name = 'usage_minutes'
    ) THEN
        ALTER TABLE "organizations" ADD COLUMN "usage_minutes" DOUBLE PRECISION NOT NULL DEFAULT 0.0;
    END IF;
END $$;

-- Add subscription_plan column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'organizations' AND column_name = 'subscription_plan'
    ) THEN
        ALTER TABLE "organizations" ADD COLUMN "subscription_plan" VARCHAR(50) NOT NULL DEFAULT 'FREE';
    END IF;
END $$;

-- Update meetings.status default to 'PENDING' (if it's currently 'pending')
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'meetings' 
        AND column_name = 'status' 
        AND column_default = '''pending''::character varying'
    ) THEN
        ALTER TABLE "meetings" ALTER COLUMN "status" SET DEFAULT 'PENDING';
    END IF;
END $$;
