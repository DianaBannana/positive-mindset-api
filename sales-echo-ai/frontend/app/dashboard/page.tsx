"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { MeetingTable } from "@/components/MeetingTable";
import { AudioUpload } from "@/components/AudioUpload";
import { createBrowserClient } from "@/lib/supabase";

export default function DashboardPage() {
  const router = useRouter();
  const [orgId, setOrgId] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkSession() {
      const supabase = createBrowserClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      // Get user's org_id and user_id from session metadata or user metadata
      // DEV_ONLY: FORCE override - if DEV_ORG_ID is set, use it regardless of session metadata
      const devOrgId = process.env.NEXT_PUBLIC_DEV_ORG_ID;
      let userOrgId = session.user.user_metadata?.org_id;
      const userUserId = session.user.id;
      
      console.log("[Dashboard] Session data:", {
        userId: userUserId,
        orgIdFromMetadata: userOrgId,
        devOrgId: devOrgId,
        userMetadata: session.user.user_metadata,
      });
      
      // Priority order: DEV_ORG_ID from env (for POC) > session metadata > user ID fallback
      // This ensures POC uses correct org_id even if mock session provides wrong ID
      const finalOrgId = devOrgId || userOrgId || session.user.id || "default-org-id";
      
      if (devOrgId && finalOrgId === devOrgId) {
        console.log("!!! FORCING DEV ORG ID:", finalOrgId);
        console.log("[Dashboard] DEV_ONLY OVERRIDE: Using DEV_ORG_ID from environment (original orgId was:", userOrgId, ")");
      } else if (finalOrgId === session.user.id) {
        console.log("[Dashboard] Using user ID as fallback orgId:", finalOrgId);
      }
      
      userOrgId = finalOrgId;

      console.log("[Dashboard] Setting orgId:", userOrgId, "userId:", userUserId);
      setOrgId(userOrgId);
      setUserId(userUserId);
      setLoading(false);
    }

    checkSession();
  }, [router]);

  const handleUploadSuccess = () => {
    // Trigger table refresh via window function
    // Wait a bit longer to allow backend processing to start
    console.log("[Dashboard] Upload success, refreshing meetings table...");
    setTimeout(() => {
      if (typeof window !== "undefined" && (window as any).refreshMeetingsTable) {
        (window as any).refreshMeetingsTable();
        console.log("[Dashboard] Meetings table refresh triggered");
      } else {
        console.warn("[Dashboard] refreshMeetingsTable function not found");
      }
    }, 500);
    
    // Also refresh again after a longer delay to catch completed meetings
    setTimeout(() => {
      if (typeof window !== "undefined" && (window as any).refreshMeetingsTable) {
        (window as any).refreshMeetingsTable();
        console.log("[Dashboard] Secondary meetings table refresh triggered");
      }
    }, 5000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Meetings</h1>
        <p className="mt-2 text-gray-600">
          View and manage your sales meeting transcriptions
        </p>
      </div>

      {/* Audio Upload Component */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Upload Meeting Recording
        </h2>
        <AudioUpload
          orgId={orgId}
          userId={userId}
          onUploadSuccess={handleUploadSuccess}
        />
      </div>

      {/* Meetings Table */}
      <MeetingTable orgId={orgId} userId={userId} />
    </div>
  );
}
