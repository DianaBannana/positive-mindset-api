"use client";

import { useEffect, useState, useCallback, ReactNode } from "react";
import { Lock, Loader2, Zap, Star, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { FeatureAccessCheck, FeatureBundle } from "@/lib/types";
import { getOrgId, getApiUrl } from "@/lib/org";
import Link from "next/link";

const API_URL = getApiUrl();

interface FeatureGateProps {
  /** The feature to check access for */
  feature: string;
  /** Content to show when feature is accessible */
  children: ReactNode;
  /** Optional fallback when feature is locked (default: upgrade prompt) */
  fallback?: ReactNode;
  /** Optional custom lock message */
  lockMessage?: string;
  /** Show as inline badge instead of blocking overlay */
  inline?: boolean;
  /** Show loading state while checking */
  showLoading?: boolean;
  /** Additional className */
  className?: string;
}

const bundleNames: Record<FeatureBundle, string> = {
  trial: "Trial",
  starter: "Starter",
  pro: "Pro",
  enterprise: "Enterprise",
};

/**
 * FeatureGate - Conditional rendering based on subscription bundle
 * 
 * Usage:
 * ```tsx
 * <FeatureGate feature="crm">
 *   <CRMSyncButton />
 * </FeatureGate>
 * ```
 * 
 * If the user's bundle doesn't include the feature, shows an upgrade prompt instead.
 */
export function FeatureGate({
  feature,
  children,
  fallback,
  lockMessage,
  inline = false,
  showLoading = true,
  className,
}: FeatureGateProps) {
  const [loading, setLoading] = useState(true);
  const [access, setAccess] = useState<FeatureAccessCheck | null>(null);
  const [error, setError] = useState(false);

  const orgId = getOrgId();

  const checkAccess = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/v1/billing/feature/${feature}?org_id=${orgId}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setAccess(data);
      } else {
        setError(true);
      }
    } catch (err) {
      console.error("Feature check error:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [feature, orgId]);

  useEffect(() => {
    checkAccess();
  }, [checkAccess]);

  // Show loading state
  if (loading && showLoading) {
    return (
      <div className={cn("flex items-center gap-2 text-gray-400", className)}>
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm">Checking access...</span>
      </div>
    );
  }

  // On error, allow access (fail open for UX)
  if (error) {
    return <>{children}</>;
  }

  // Feature is accessible
  if (access?.has_access) {
    return <>{children}</>;
  }

  // Feature is locked - show fallback or default lock UI
  if (fallback) {
    return <>{fallback}</>;
  }

  // Inline mode - show a small locked badge
  if (inline) {
    return (
      <span className={cn("inline-flex items-center gap-1 text-gray-400", className)}>
        <Lock className="h-3 w-3" />
        <span className="text-xs">{bundleNames[access?.required_bundle || "pro"]}+</span>
      </span>
    );
  }

  // Default locked overlay
  return (
    <Card className={cn("relative overflow-hidden border-dashed border-2 border-gray-200", className)}>
      <CardContent className="p-6">
        <div className="flex flex-col items-center justify-center text-center space-y-4">
          <div className="h-12 w-12 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
            <Lock className="h-6 w-6 text-indigo-600" />
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-900">
              {lockMessage || `${feature.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())} is a premium feature`}
            </h4>
            <p className="text-sm text-gray-500 mt-1">
              Upgrade to <span className="font-medium text-indigo-600">{bundleNames[access?.required_bundle || "pro"]}</span> to unlock this feature
            </p>
          </div>

          <Link href={access?.upgrade_url || "/dashboard/settings?tab=billing"}>
            <Button className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600">
              <Star className="h-4 w-4 mr-2" />
              Upgrade Now
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * FeatureLockedButton - A button that shows locked state for premium features
 * 
 * Usage:
 * ```tsx
 * <FeatureLockedButton feature="crm" onClick={handleCRMSync}>
 *   Sync to CRM
 * </FeatureLockedButton>
 * ```
 */
interface FeatureLockedButtonProps {
  feature: string;
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  variant?: "default" | "outline" | "ghost" | "secondary";
  size?: "default" | "sm" | "lg" | "icon";
}

export function FeatureLockedButton({
  feature,
  children,
  onClick,
  className,
  variant = "default",
  size = "default",
}: FeatureLockedButtonProps) {
  const [loading, setLoading] = useState(true);
  const [access, setAccess] = useState<FeatureAccessCheck | null>(null);

  const orgId = getOrgId();

  useEffect(() => {
    const checkAccess = async () => {
      try {
        const response = await fetch(
          `${API_URL}/api/v1/billing/feature/${feature}?org_id=${orgId}`
        );
        
        if (response.ok) {
          const data = await response.json();
          setAccess(data);
        }
      } catch (err) {
        console.error("Feature check error:", err);
      } finally {
        setLoading(false);
      }
    };

    checkAccess();
  }, [feature, orgId]);

  if (loading) {
    return (
      <Button variant={variant} size={size} disabled className={className}>
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        {children}
      </Button>
    );
  }

  if (access?.has_access) {
    return (
      <Button variant={variant} size={size} onClick={onClick} className={className}>
        {children}
      </Button>
    );
  }

  // Locked state
  return (
    <Link href={access?.upgrade_url || "/dashboard/settings?tab=billing"} className="inline-block">
      <Button 
        variant="outline" 
        size={size} 
        className={cn(
          "border-dashed border-gray-300 text-gray-500 hover:text-indigo-600 hover:border-indigo-300",
          className
        )}
      >
        <Lock className="h-4 w-4 mr-2" />
        {children}
        <Zap className="h-3 w-3 ml-1 text-amber-500" />
      </Button>
    </Link>
  );
}

/**
 * useFeatureAccess - Hook for checking feature access programmatically
 * 
 * Usage:
 * ```tsx
 * const { hasAccess, loading, requiredBundle } = useFeatureAccess("crm");
 * 
 * if (!hasAccess) {
 *   return <UpgradePrompt bundle={requiredBundle} />;
 * }
 * ```
 */
export function useFeatureAccess(feature: string) {
  const [loading, setLoading] = useState(true);
  const [hasAccess, setHasAccess] = useState(false);
  const [requiredBundle, setRequiredBundle] = useState<FeatureBundle | null>(null);
  const [currentBundle, setCurrentBundle] = useState<FeatureBundle>("trial");

  const orgId = getOrgId();

  useEffect(() => {
    const checkAccess = async () => {
      try {
        const response = await fetch(
          `${API_URL}/api/v1/billing/feature/${feature}?org_id=${orgId}`
        );
        
        if (response.ok) {
          const data: FeatureAccessCheck = await response.json();
          setHasAccess(data.has_access);
          setRequiredBundle(data.required_bundle);
          setCurrentBundle(data.current_bundle);
        }
      } catch (err) {
        console.error("Feature check error:", err);
        // Fail open for UX
        setHasAccess(true);
      } finally {
        setLoading(false);
      }
    };

    checkAccess();
  }, [feature, orgId]);

  return { loading, hasAccess, requiredBundle, currentBundle };
}
