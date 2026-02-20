-- CreateTable
CREATE TABLE "organizations" (
    "id" UUID NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "settings" JSONB,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "organizations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "users" (
    "id" UUID NOT NULL,
    "org_id" UUID NOT NULL,
    "auth0_id" VARCHAR(255),
    "clerk_id" VARCHAR(255),
    "email" VARCHAR(255) NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "role" VARCHAR(50) NOT NULL DEFAULT 'sales_rep',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "meetings" (
    "id" UUID NOT NULL,
    "org_id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "client_name" VARCHAR(255),
    "client_id" UUID,
    "audio_url" TEXT,
    "transcript" TEXT,
    "transcript_raw" JSONB,
    "audio_deleted_at" TIMESTAMPTZ(6),
    "audio_deletion_scheduled_at" TIMESTAMPTZ(6),
    "retention_policy_hours" INTEGER,
    "summary" JSONB,
    "summary_text" TEXT,
    "processing_errors" JSONB,
    "status" VARCHAR(50) NOT NULL DEFAULT 'pending',
    "language_mix" VARCHAR(20),
    "duration_seconds" INTEGER,
    "confidence_score" DOUBLE PRECISION,
    "reviewed_at" TIMESTAMPTZ(6),
    "reviewed_by" UUID,
    "approved_for_sync" BOOLEAN NOT NULL DEFAULT false,
    "synced_to_crm" BOOLEAN NOT NULL DEFAULT false,
    "synced_at" TIMESTAMPTZ(6),
    "sync_status" VARCHAR(50),
    "sync_retry_count" INTEGER NOT NULL DEFAULT 0,
    "sync_error_message" TEXT,
    "sync_scheduled_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "meetings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "corrections" (
    "id" UUID NOT NULL,
    "org_id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "meeting_id" UUID NOT NULL,
    "field_name" VARCHAR(100) NOT NULL,
    "old_value" JSONB,
    "new_value" JSONB,
    "field_path" VARCHAR(255),
    "source_snippet" TEXT,
    "confidence_before" DOUBLE PRECISION,
    "reason" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "corrections_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crm_integrations" (
    "id" UUID NOT NULL,
    "org_id" UUID NOT NULL,
    "provider" VARCHAR(50) NOT NULL,
    "status" VARCHAR(50) NOT NULL DEFAULT 'active',
    "access_token" TEXT,
    "refresh_token" TEXT,
    "token_expires_at" TIMESTAMPTZ(6),
    "config" JSONB,
    "webhook_url" TEXT,
    "last_sync_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "crm_integrations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crm_audit_logs" (
    "id" UUID NOT NULL,
    "org_id" UUID NOT NULL,
    "meeting_id" UUID NOT NULL,
    "created_by" UUID NOT NULL,
    "crm_provider" VARCHAR(50) NOT NULL,
    "operation_type" VARCHAR(50) NOT NULL,
    "crm_entity_id" VARCHAR(255),
    "crm_entity_type" VARCHAR(50) NOT NULL,
    "payload" JSONB,
    "response" JSONB,
    "status" VARCHAR(20) NOT NULL,
    "error_message" TEXT,
    "transcript_source" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "crm_audit_logs_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_auth0_id_key" ON "users"("auth0_id");

-- CreateIndex
CREATE UNIQUE INDEX "users_clerk_id_key" ON "users"("clerk_id");

-- CreateIndex
CREATE INDEX "users_org_id_idx" ON "users"("org_id");

-- CreateIndex
CREATE INDEX "users_auth0_id_idx" ON "users"("auth0_id");

-- CreateIndex
CREATE INDEX "users_clerk_id_idx" ON "users"("clerk_id");

-- CreateIndex
CREATE INDEX "meetings_org_id_idx" ON "meetings"("org_id");

-- CreateIndex
CREATE INDEX "meetings_user_id_idx" ON "meetings"("user_id");

-- CreateIndex
CREATE INDEX "meetings_status_idx" ON "meetings"("status");

-- CreateIndex
CREATE INDEX "meetings_created_at_idx" ON "meetings"("created_at");

-- CreateIndex
CREATE INDEX "meetings_org_id_client_id_created_at_idx" ON "meetings"("org_id", "client_id", "created_at");

-- CreateIndex
CREATE INDEX "corrections_org_id_idx" ON "corrections"("org_id");

-- CreateIndex
CREATE INDEX "corrections_meeting_id_idx" ON "corrections"("meeting_id");

-- CreateIndex
CREATE INDEX "corrections_field_name_idx" ON "corrections"("field_name");

-- CreateIndex
CREATE INDEX "crm_integrations_org_id_idx" ON "crm_integrations"("org_id");

-- CreateIndex
CREATE INDEX "crm_integrations_status_idx" ON "crm_integrations"("status");

-- CreateIndex
CREATE UNIQUE INDEX "crm_integrations_org_id_provider_key" ON "crm_integrations"("org_id", "provider");

-- CreateIndex
CREATE INDEX "crm_audit_logs_org_id_idx" ON "crm_audit_logs"("org_id");

-- CreateIndex
CREATE INDEX "crm_audit_logs_meeting_id_idx" ON "crm_audit_logs"("meeting_id");

-- CreateIndex
CREATE INDEX "crm_audit_logs_crm_provider_idx" ON "crm_audit_logs"("crm_provider");

-- CreateIndex
CREATE INDEX "crm_audit_logs_status_idx" ON "crm_audit_logs"("status");

-- CreateIndex
CREATE INDEX "crm_audit_logs_created_at_idx" ON "crm_audit_logs"("created_at");

-- AddForeignKey
ALTER TABLE "users" ADD CONSTRAINT "users_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "meetings" ADD CONSTRAINT "meetings_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "meetings" ADD CONSTRAINT "meetings_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "corrections" ADD CONSTRAINT "corrections_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "corrections" ADD CONSTRAINT "corrections_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "corrections" ADD CONSTRAINT "corrections_meeting_id_fkey" FOREIGN KEY ("meeting_id") REFERENCES "meetings"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crm_integrations" ADD CONSTRAINT "crm_integrations_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crm_audit_logs" ADD CONSTRAINT "crm_audit_logs_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crm_audit_logs" ADD CONSTRAINT "crm_audit_logs_meeting_id_fkey" FOREIGN KEY ("meeting_id") REFERENCES "meetings"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crm_audit_logs" ADD CONSTRAINT "crm_audit_logs_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
