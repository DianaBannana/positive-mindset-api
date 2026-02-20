"use client";

import { ReactNode } from "react";
import { useAuth, useRequireRole } from "@/lib/auth-context";
import { UserRole, Permission } from "@/lib/types";
import { Shield, Lock, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface RequireRoleProps {
  /** Required role(s) to access the content */
  roles: UserRole | UserRole[];
  /** Content to show when authorized */
  children: ReactNode;
  /** Optional fallback content when not authorized */
  fallback?: ReactNode;
  /** Show loading state */
  showLoading?: boolean;
  /** Redirect path when not authorized */
  redirectTo?: string;
}

/**
 * RequireRole - Conditional rendering based on user role
 * 
 * Usage:
 * ```tsx
 * <RequireRole roles={["manager", "admin"]}>
 *   <AnalyticsDashboard />
 * </RequireRole>
 * ```
 */
export function RequireRole({
  roles,
  children,
  fallback,
  showLoading = true,
  redirectTo,
}: RequireRoleProps) {
  const { loading, authorized, role } = useRequireRole(roles);

  if (loading && showLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (authorized) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  // Default unauthorized UI
  const rolesArray = Array.isArray(roles) ? roles : [roles];
  const roleLabels: Record<UserRole, string> = {
    sales_rep: "Sales Rep",
    manager: "Manager",
    admin: "Admin",
  };

  return (
    <Card className="border-2 border-dashed border-gray-200 bg-gray-50">
      <CardContent className="py-12">
        <div className="flex flex-col items-center justify-center text-center space-y-4">
          <div className="h-14 w-14 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
            <Lock className="h-7 w-7 text-amber-600" />
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 text-lg">Access Restricted</h4>
            <p className="text-sm text-gray-500 mt-1">
              This section requires{" "}
              <span className="font-medium text-amber-700">
                {rolesArray.map((r) => roleLabels[r]).join(" or ")}
              </span>{" "}
              access.
            </p>
            {role && (
              <p className="text-xs text-gray-400 mt-2">
                Your current role: <span className="font-medium">{roleLabels[role]}</span>
              </p>
            )}
          </div>

          {redirectTo && (
            <Link href={redirectTo}>
              <Button variant="outline" className="mt-2">
                Go Back
              </Button>
            </Link>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface RequirePermissionProps {
  /** Required permission to access the content */
  permission: Permission;
  /** Content to show when authorized */
  children: ReactNode;
  /** Optional fallback content */
  fallback?: ReactNode;
  /** Inline mode (no card wrapper) */
  inline?: boolean;
}

/**
 * RequirePermission - Conditional rendering based on permission
 */
export function RequirePermission({
  permission,
  children,
  fallback,
  inline = false,
}: RequirePermissionProps) {
  const { hasPermission, loading } = useAuth();

  if (loading) {
    return null;
  }

  if (hasPermission(permission)) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  if (inline) {
    return (
      <span className="inline-flex items-center gap-1 text-gray-400">
        <Lock className="h-3 w-3" />
        <span className="text-xs">Restricted</span>
      </span>
    );
  }

  return null;
}

/**
 * RoleBadge - Display user's role with icon
 */
export function RoleBadge({ role }: { role: UserRole }) {
  const config: Record<UserRole, { label: string; color: string; icon: ReactNode }> = {
    sales_rep: {
      label: "Sales Rep",
      color: "bg-blue-100 text-blue-700 border-blue-200",
      icon: null,
    },
    manager: {
      label: "Manager",
      color: "bg-purple-100 text-purple-700 border-purple-200",
      icon: <Shield className="h-3 w-3" />,
    },
    admin: {
      label: "Admin",
      color: "bg-red-100 text-red-700 border-red-200",
      icon: <Shield className="h-3 w-3" />,
    },
  };

  const { label, color, icon } = config[role] || config.sales_rep;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${color}`}
    >
      {icon}
      {label}
    </span>
  );
}
