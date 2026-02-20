/**
 * Shared Components Index
 * 
 * Re-exports all shared components for cleaner imports.
 * Usage: import { FeedbackWidget, UsageTracker, FeatureGate, ActionCenter } from "@/components/shared";
 */

export { FeedbackWidget, FeedbackSummary } from "./FeedbackWidget";
export { UsageTracker } from "./UsageTracker";
export { FeatureGate, FeatureLockedButton, useFeatureAccess } from "./FeatureGate";
export { RequireRole, RequirePermission, RoleBadge } from "./RequireRole";
export { ActionCenter } from "./ActionCenter";
