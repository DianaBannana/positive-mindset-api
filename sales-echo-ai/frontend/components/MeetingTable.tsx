"use client";

import { useState, useEffect } from "react";
import { Meeting } from "@/lib/api";
import { fetchMeetings } from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Eye, Loader2 } from "lucide-react";

interface MeetingTableProps {
  orgId: string;
  userId?: string;
}

export function MeetingTable({ orgId, userId }: MeetingTableProps) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadMeetings = async () => {
    try {
      setLoading(true);
      
      // Priority order: DEV_ORG_ID from env (for POC) > passed orgId > default
      // This ensures POC uses correct org_id even if wrong orgId is passed from dashboard
      const finalOrgId = process.env.NEXT_PUBLIC_DEV_ORG_ID || orgId || "default-org-id";
      
      console.log("[MeetingTable] Loading meetings - finalOrgId:", finalOrgId, "original orgId:", orgId, "userId:", userId);
      
      const data = await fetchMeetings(finalOrgId, userId);
      
      const uniqueOrgIds = [...new Set(data?.map((m) => m.org_id) || [])];
      const count = data?.length || 0;
      
      console.log("[MeetingTable] Received meetings data:", {
        count: count,
        orgIds: data?.map((m) => m.org_id) || [],
        uniqueOrgIds: uniqueOrgIds,
        sampleMeeting: data?.[0] || null,
      });
      
      // Fallback warning: if no meetings found, log the attempted org_id
      if (count === 0) {
        console.warn(
          "[MeetingTable] No meetings found for finalOrgId:",
          finalOrgId,
          "(original orgId was:",
          orgId,
          ") userId:",
          userId,
          "- Backend should have tried fallback resolution. Check backend logs."
        );
      } else if (uniqueOrgIds.length > 0 && !uniqueOrgIds.includes(finalOrgId)) {
        // If meetings were found but with different org_id, log the mismatch
        console.warn(
          "[MeetingTable] OrgId mismatch detected:",
          "Requested finalOrgId:",
          finalOrgId,
          "(original orgId was:",
          orgId,
          ") Actual orgIds in response:",
          uniqueOrgIds,
          "- Backend resolved to different organization."
        );
      }
      
      setMeetings(data);
      setError(null);
    } catch (err) {
      console.error("[MeetingTable] Error loading meetings:", err);
      setError("Failed to load meetings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (orgId) {
      console.log("[MeetingTable] useEffect triggered - orgId:", orgId, "userId:", userId, "refreshKey:", refreshKey);
      loadMeetings();
    } else {
      console.warn("[MeetingTable] No orgId provided, skipping load");
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId, userId, refreshKey]);

  // Expose refresh function via window for external access
  useEffect(() => {
    const refresh = () => {
      setRefreshKey(prev => prev + 1);
    };
    (window as any).refreshMeetingsTable = refresh;
    return () => {
      delete (window as any).refreshMeetingsTable;
    };
  }, []);

  const getStatusBadgeVariant = (status: Meeting["status"]) => {
    switch (status) {
      case "COMPLETED":
        return "success";
      case "PROCESSING":
        return "warning";
      case "FAILED":
        return "destructive";
      case "PENDING":
      default:
        return "secondary";
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleViewSummary = (meetingId: string) => {
    // Navigate to meeting detail page
    window.location.href = `/dashboard/meetings/${meetingId}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading meetings...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <div className="text-center">
          <p className="text-red-600 font-medium mb-2">{error}</p>
          <p className="text-sm text-gray-500">
            Unable to load meetings. Please check your connection and try again.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            setError(null);
            loadMeetings();
          }}
        >
          Retry
        </Button>
      </div>
    );
  }

  if (meetings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-gray-500 mb-4">No meetings found</p>
        <p className="text-sm text-gray-400">
          Upload your first meeting to get started
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Client Name</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {meetings.map((meeting) => (
            <TableRow key={meeting.id}>
              <TableCell className="font-medium">
                {formatDate(meeting.created_at)}
              </TableCell>
              <TableCell>
                {meeting.client_name || "Unknown Client"}
              </TableCell>
              <TableCell>
                <Badge variant={getStatusBadgeVariant(meeting.status)}>
                  {meeting.status}
                </Badge>
              </TableCell>
              <TableCell>
                {meeting.duration_seconds
                  ? `${Math.round(meeting.duration_seconds / 60)} min`
                  : "—"}
              </TableCell>
              <TableCell className="text-right">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleViewSummary(meeting.id)}
                  disabled={meeting.status !== "COMPLETED"}
                >
                  <Eye className="h-4 w-4 mr-2" />
                  View Summary
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
