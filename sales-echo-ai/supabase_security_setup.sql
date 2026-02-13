-- SalesEcho AI - Supabase Security Setup (FIXED)
-- Row Level Security (RLS) and Multi-tenancy Policies
-- This script is idempotent and can be safely re-run.

-- ============================================
-- Enable RLS on all relevant tables
-- ============================================

ALTER TABLE public.organizations      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meetings           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.corrections        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crm_integrations   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crm_audit_logs     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public."_prisma_migrations" ENABLE ROW LEVEL SECURITY;


-- ============================================
-- ORGANIZATIONS: Users can only see their own organization
-- ============================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'organizations'
      AND policyname = 'org_authenticated_select'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "org_authenticated_select"
      ON public.organizations
      FOR SELECT
      TO authenticated
      USING (
        id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      );
    $policy$;
  END IF;
END
$$;


-- ============================================
-- USERS: Users can only access their own record (prevents infinite recursion)
-- ============================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'users'
      AND policyname = 'Users can manage their own profile'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "Users can manage their own profile"
      ON public.users
      FOR ALL
      TO authenticated
      USING (id = auth.uid())
      WITH CHECK (id = auth.uid());
    $policy$;
  END IF;
END
$$;


-- ============================================
-- MEETINGS: Multi-tenant access based on org_id
-- ============================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'meetings'
      AND policyname = 'meetings_authenticated_select'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "meetings_authenticated_select"
      ON public.meetings
      FOR SELECT
      TO authenticated
      USING (
        org_id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      );
    $policy$;
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'meetings'
      AND policyname = 'meetings_authenticated_insert'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "meetings_authenticated_insert"
      ON public.meetings
      FOR INSERT
      TO authenticated
      WITH CHECK (
        org_id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      );
    $policy$;
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'meetings'
      AND policyname = 'meetings_authenticated_update'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "meetings_authenticated_update"
      ON public.meetings
      FOR UPDATE
      TO authenticated
      USING (
        org_id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      )
      WITH CHECK (
        org_id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      );
    $policy$;
  END IF;
END
$$;


-- ============================================
-- CORRECTIONS: Multi-tenant access based on org_id
-- ============================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'corrections'
      AND policyname = 'corrections_authenticated_select'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "corrections_authenticated_select"
      ON public.corrections
      FOR SELECT
      TO authenticated
      USING (
        org_id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      );
    $policy$;
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'corrections'
      AND policyname = 'corrections_authenticated_insert'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "corrections_authenticated_insert"
      ON public.corrections
      FOR INSERT
      TO authenticated
      WITH CHECK (
        org_id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      );
    $policy$;
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'corrections'
      AND policyname = 'corrections_authenticated_update'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "corrections_authenticated_update"
      ON public.corrections
      FOR UPDATE
      TO authenticated
      USING (
        org_id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      )
      WITH CHECK (
        org_id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      );
    $policy$;
  END IF;
END
$$;


-- ============================================
-- CRM AUDIT LOGS: Multi-tenant access based on org_id
-- ============================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'crm_audit_logs'
      AND policyname = 'crm_audit_logs_authenticated_select'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "crm_audit_logs_authenticated_select"
      ON public.crm_audit_logs
      FOR SELECT
      TO authenticated
      USING (
        org_id = (
          SELECT org_id
          FROM public.users
          WHERE id = auth.uid()
        )
      );
    $policy$;
  END IF;
END
$$;


-- ============================================
-- Secure Sensitive Data: crm_integrations
-- ============================================

REVOKE ALL ON TABLE public.crm_integrations FROM anon;
REVOKE ALL ON TABLE public.crm_integrations FROM authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.crm_integrations TO service_role;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'crm_integrations'
      AND policyname = 'crm_integrations_service_all'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "crm_integrations_service_all"
      ON public.crm_integrations
      FOR ALL
      TO service_role
      USING (true)
      WITH CHECK (true);
    $policy$;
  END IF;
END
$$;


-- ============================================
-- _prisma_migrations: Lock down to service_role
-- ============================================

REVOKE ALL ON TABLE public."_prisma_migrations" FROM anon;
REVOKE ALL ON TABLE public."_prisma_migrations" FROM authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public."_prisma_migrations" TO service_role;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = '_prisma_migrations'
      AND policyname = 'prisma_migrations_service_all'
  ) THEN
    EXECUTE $policy$
      CREATE POLICY "prisma_migrations_service_all"
      ON public."_prisma_migrations"
      FOR ALL
      TO service_role
      USING (true)
      WITH CHECK (true);
    $policy$;
  END IF;
END
$$;