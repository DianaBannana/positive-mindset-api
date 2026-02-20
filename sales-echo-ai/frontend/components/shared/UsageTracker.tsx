"use client";

import { useEffect, useState, useCallback } from "react";
import { Loader2, AlertTriangle, Zap, Clock, Star, TrendingUp } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { UsageStatus, FeatureBundle } from "@/lib/types";
import { getOrgId, getApiUrl } from "@/lib/org";
import Link from "next/link";

const API_URL = getApiUrl();

interface UsageTrackerProps {
  className?: string;
  compact?: boolean;
}

const bundleColors: Record<FeatureBundle, string> = {
  trial: "bg-amber-100 text-amber-700 border-amber-200",
  starter: "bg-blue-100 text-blue-700 border-blue-200",
  pro: "bg-purple-100 text-purple-700 border-purple-200",
  enterprise: "bg-emerald-100 text-emerald-700 border-emerald-200",
};

const bundleLabels: Record<FeatureBundle, string> = {
  trial: "Trial",
  starter: "Starter",
  pro: "Pro",
  enterprise: "Enterprise",
};

export function UsageTracker({ className, compact = false }: UsageTrackerProps) {
  const [loading, setLoading] = useState(true);
  const [usage, setUsage] = useState<UsageStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const orgId = getOrgId();

  const fetchUsage = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/billing/usage?org_id=${orgId}`);
      
      if (response.ok) {
        const data = await response.json();
        setUsage(data);
        setError(null);
      } else {
        setError("Failed to load usage");
      }
    } catch (err) {
      console.error("Usage fetch error:", err);
      setError("Connection error");
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    fetchUsage();
    // Refresh every 60 seconds
    const interval = setInterval(fetchUsage, 60000);
    return () => clearInterval(interval);
  }, [fetchUsage]);

  if (loading) {
    return (
      <div className={cn("p-3 rounded-lg bg-gray-50 border", className)}>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Loading usage...</span>
        </div>
      </div>
    );
  }

  if (error || !usage) {
    return (
      <div className={cn("p-3 rounded-lg bg-red-50 border border-red-200", className)}>
        <div className="flex items-center gap-2 text-sm text-red-600">
          <AlertTriangle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  const meetingPercent = usage.meetings.unlimited 
    ? 0 
    : Math.min(100, (usage.meetings.used / usage.meetings.limit) * 100);
  
  const isLow = usage.meetings.remaining <= 3 && !usage.meetings.unlimited;
  const isCritical = usage.is_over_quota || usage.is_expired;

  // Compact mode for sidebar
  if (compact) {
    return (
      <div className={cn(
        "p-3 rounded-lg border transition-colors",
        isCritical 
          ? "bg-red-50 border-red-200" 
          : isLow 
            ? "bg-amber-50 border-amber-200" 
            : "bg-gray-50 border-gray-200",
        className
      )}>
        <div className="flex items-center justify-between mb-2">
          <Badge variant="outline" className={cn("text-xs", bundleColors[usage.bundle])}>
            {bundleLabels[usage.bundle]}
          </Badge>
          {usage.is_trial && usage.trial && usage.trial.days_remaining !== null && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {usage.trial.days_remaining}d left
            </span>
          )}
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Meetings</span>
            <span className={cn(
              "font-medium",
              isCritical ? "text-red-600" : isLow ? "text-amber-600" : "text-gray-900"
            )}>
              {usage.meetings.unlimited 
                ? `${usage.meetings.used} used` 
                : `${usage.meetings.used}/${usage.meetings.limit}`
              }
            </span>
          </div>
          
          {!usage.meetings.unlimited && (
            <Progress 
              value={meetingPercent} 
              className={cn(
                "h-1.5",
                isCritical ? "[&>div]:bg-red-500" : isLow ? "[&>div]:bg-amber-500" : "[&>div]:bg-indigo-500"
              )}
            />
          )}
        </div>

        {isCritical && (
          <Link href="/dashboard/settings?tab=billing">
            <Button size="sm" className="w-full mt-3 h-7 text-xs bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600">
              <Zap className="h-3 w-3 mr-1" />
              Upgrade Now
            </Button>
          </Link>
        )}
      </div>
    );
  }

  // Full mode
  return (
    <div className={cn(
      "p-4 rounded-xl border-2 transition-colors",
      isCritical 
        ? "bg-red-50 border-red-200" 
        : isLow 
          ? "bg-amber-50 border-amber-200" 
          : "bg-gradient-to-br from-indigo-50 via-white to-purple-50 border-indigo-200",
      className
    )}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-indigo-600" />
          <h3 className="font-semibold text-gray-900">Usage</h3>
        </div>
        <Badge variant="outline" className={cn(bundleColors[usage.bundle])}>
          {bundleLabels[usage.bundle]}
        </Badge>
      </div>

      {/* Trial Info */}
      {usage.is_trial && usage.trial && (
        <div className={cn(
          "p-3 rounded-lg mb-4",
          usage.is_expired 
            ? "bg-red-100 text-red-800" 
            : usage.trial.days_remaining !== null && usage.trial.days_remaining <= 3 
              ? "bg-amber-100 text-amber-800" 
              : "bg-blue-100 text-blue-800"
        )}>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            {usage.is_expired ? (
              <span className="font-medium">Trial expired</span>
            ) : (
              <span>
                <span className="font-medium">{usage.trial.days_remaining} days</span> remaining in trial
              </span>
            )}
          </div>
        </div>
      )}

      {/* Meetings Usage */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Meetings Used</span>
          <span className={cn(
            "font-semibold",
            isCritical ? "text-red-600" : isLow ? "text-amber-600" : "text-gray-900"
          )}>
            {usage.meetings.unlimited 
              ? `${usage.meetings.used} (Unlimited)` 
              : `${usage.meetings.used} / ${usage.meetings.limit}`
            }
          </span>
        </div>
        
        {!usage.meetings.unlimited && (
          <>
            <Progress 
              value={meetingPercent} 
              className={cn(
                "h-2",
                isCritical ? "[&>div]:bg-red-500" : isLow ? "[&>div]:bg-amber-500" : "[&>div]:bg-indigo-500"
              )}
            />
            <p className="text-xs text-gray-500">
              {usage.meetings.remaining} meetings remaining
            </p>
          </>
        )}
      </div>

      {/* Minutes Usage */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Minutes Used</span>
          <span className="font-semibold text-gray-900">
            {usage.minutes.unlimited 
              ? `${usage.minutes.used} min` 
              : `${Math.round(usage.minutes.used)} / ${usage.minutes.limit} min`
            }
          </span>
        </div>
        
        {!usage.minutes.unlimited && (
          <Progress 
            value={Math.min(100, (usage.minutes.used / usage.minutes.limit) * 100)} 
            className="h-2 [&>div]:bg-purple-500"
          />
        )}
      </div>

      {/* Status Message */}
      {isCritical && (
        <div className="text-center">
          <p className="text-sm text-red-600 mb-3">
            {usage.is_expired 
              ? "Your trial has expired. Upgrade to continue analyzing calls."
              : "You've reached your plan limit. Upgrade for more meetings."
            }
          </p>
          <Link href="/dashboard/settings?tab=billing">
            <Button className="w-full bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600">
              <Star className="h-4 w-4 mr-2" />
              Upgrade Plan
            </Button>
          </Link>
        </div>
      )}

      {!isCritical && isLow && (
        <div className="text-center">
          <p className="text-sm text-amber-700 mb-2">
            Running low on meetings. Consider upgrading.
          </p>
          <Link href="/dashboard/settings?tab=billing">
            <Button variant="outline" size="sm" className="text-amber-700 border-amber-300 hover:bg-amber-50">
              <Zap className="h-4 w-4 mr-1" />
              View Plans
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
