"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Flame, AlertCircle, CheckCircle2, Clock, MessageSquare, Database } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Meeting } from "@/lib/api";

interface MeetingWithSummary extends Meeting {
  summary?: {
    content?: {
      summary_text?: string;
      action_items?: {
        task: string;
        due?: string | null;
        assignee?: string | null;
        confidence?: number;
        source?: string | null;
      }[];
      crm_entities?: {
        deal_value?: {
          value: number;
          currency: string;
          confidence?: number;
          source?: string;
        } | null;
        next_meeting_date?: {
          value: string;
          confidence?: number;
          source?: string;
        } | null;
        contact_email?: {
          value: string;
          confidence?: number;
          source?: string;
        } | null;
      } | null;
    };
    governance?: {
      confidence_score?: number;
      requires_review?: boolean;
    };
  } | null;
  transcript?: string | null;
}

function fetchMeetingById(id: string, orgId?: string): Promise<MeetingWithSummary> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  let url = `${baseUrl}/api/v1/meetings/${id}`;
  if (orgId) {
    url += `?org_id=${orgId}`;
  }
  console.log("[fetchMeetingById] Request URL:", url);
  return fetch(url)
    .then((res) => {
      if (!res.ok) {
        throw new Error(`Failed to fetch meeting: ${res.statusText}`);
      }
      return res.json();
    });
}

function getDealHeatLevel(confidence?: number): {
  label: string;
  color: string;
  description: string;
} {
  if (confidence === undefined || confidence === null) {
    return {
      label: "Unknown",
      color: "bg-gray-200 text-gray-700",
      description: "No confidence score available yet.",
    };
  }
  if (confidence >= 0.8) {
    return {
      label: "Hot",
      color: "bg-red-500 text-white",
      description: "High-confidence opportunity. Tachles – follow up now.",
    };
  }
  if (confidence >= 0.6) {
    return {
      label: "Warm",
      color: "bg-orange-400 text-white",
      description: "Promising, but needs follow-up and validation.",
    };
  }
  return {
    label: "Cool",
    color: "bg-gray-400 text-white",
    description: "Low-confidence signal. Treat as early-stage / unqualified.",
  };
}

export default function MeetingDetailsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const meetingId = params?.id;

  const [meeting, setMeeting] = useState<MeetingWithSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!meetingId) return;

    const loadMeeting = async () => {
      try {
        setLoading(true);
        const data = await fetchMeetingById(meetingId);
        setMeeting(data);
        setError(null);
      } catch (err) {
        console.error(err);
        setError("Failed to load meeting details");
      } finally {
        setLoading(false);
      }
    };

    loadMeeting();
  }, [meetingId]);

  const handleBack = () => {
    router.push("/dashboard");
  };

  const handleSendToWhatsApp = () => {
    if (!meeting || !meeting.summary?.content) return;
    
    const content = meeting.summary.content;
    const clientName = meeting.client_name || "לקוח";
    
    // Build WhatsApp message in the requested format
    let message = `היי, הנה סיכום השיחה עם ${clientName}.\n\n`;
    
    // Add action items if available
    if (content.action_items && content.action_items.length > 0) {
      message += `משימות לביצוע:\n`;
      content.action_items.forEach((item, idx) => {
        message += `${idx + 1}. ${item.task}`;
        if (item.due) message += ` (דדליין: ${item.due})`;
        if (item.assignee) message += ` (אחראי: ${item.assignee})`;
        message += `\n`;
      });
    } else {
      message += `אין משימות ספציפיות להמשך.\n`;
    }
    
    // Add summary text if available
    if (content.summary_text) {
      message += `\nסיכום:\n${content.summary_text}`;
    }
    
    // Encode message for URL
    const encodedMessage = encodeURIComponent(message);
    const whatsappUrl = `https://wa.me/?text=${encodedMessage}`;
    
    // Open WhatsApp in new window
    window.open(whatsappUrl, "_blank");
  };

  const handleSyncToCRM = async () => {
    if (!meeting || !meeting.summary?.content) return;
    
    // Mock CRM sync function
    setToastMessage("מסנכרן ל-CRM...");
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock success response
    setToastMessage("Successfully synced to Priority/HubSpot");
    
    // Clear toast after 3 seconds
    setTimeout(() => {
      setToastMessage(null);
    }, 3000);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={handleBack}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Loading meeting…
              </h1>
              <p className="text-sm text-gray-500">
                Fetching transcription and Tachles insights.
              </p>
            </div>
          </div>
        </div>
        <Card>
          <CardContent className="py-10 text-center text-gray-500">
            Loading…
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              Meeting not available
            </h1>
            <p className="text-sm text-gray-500">{error || "Unknown error"}</p>
          </div>
        </div>
        <Card>
          <CardContent className="py-8 text-center text-red-500">
            Failed to load meeting details.
          </CardContent>
        </Card>
      </div>
    );
  }

  const summary = meeting.summary;
  const content = summary?.content;
  const governance = summary?.governance;
  const dealHeat = getDealHeatLevel(governance?.confidence_score);

  const createdAt = meeting.created_at
    ? new Date(meeting.created_at).toLocaleString("en-IL", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "N/A";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              Meeting Analysis
            </h1>
            <p className="text-sm text-gray-500">
              {meeting.client_name || "Unknown client"} • {createdAt}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            Status: {meeting.status}
          </Badge>
          {governance?.requires_review && (
            <Badge variant="destructive" className="text-xs flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Requires Review
            </Badge>
          )}
        </div>
      </div>

      {/* Take Action Section */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-gray-900 mb-1">Take Action</h3>
              <p className="text-xs text-gray-600">שלח תובנות או סנכרן ל-CRM</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <Button
                onClick={handleSendToWhatsApp}
                variant="outline"
                className="flex-1 sm:flex-none bg-white hover:bg-green-50 border-green-300 text-green-700 hover:text-green-800"
                disabled={!content?.summary_text}
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                Send to WhatsApp
              </Button>
              <Button
                onClick={handleSyncToCRM}
                variant="outline"
                className="flex-1 sm:flex-none bg-white hover:bg-blue-50 border-blue-300 text-blue-700 hover:text-blue-800"
                disabled={!content?.summary_text}
              >
                <Database className="h-4 w-4 mr-2" />
                Sync to CRM
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 z-50 animate-in slide-in-from-bottom-2">
          <Card className="bg-white shadow-lg border-2 border-blue-300">
            <CardContent className="p-4">
              <p className="text-sm font-medium text-gray-900" dir="rtl">
                {toastMessage}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Top row: Summary + Deal Heat */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Tachles Summary</span>
              {governance?.confidence_score !== undefined && (
                <span className="text-xs text-gray-500">
                  Confidence: {Math.round(governance.confidence_score * 100)}%
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={cn(
                "prose max-w-none text-sm leading-relaxed",
                "whitespace-pre-wrap",
                "text-gray-800"
              )}
              dir="rtl"
            >
              {content?.summary_text || "No summary available for this meeting yet."}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-5 w-5 text-orange-500" />
              Deal Heat
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "inline-flex items-center rounded-full px-3 py-1 text-sm font-medium",
                  dealHeat.color
                )}
              >
                {dealHeat.label}
              </div>
            </div>
            <p className="text-xs text-gray-600">{dealHeat.description}</p>

            <div className="mt-4 space-y-2 text-xs text-gray-500">
              <div className="flex items-center gap-2">
                <Clock className="h-3 w-3" />
                <span>
                  Duration:{" "}
                  {meeting.duration_seconds
                    ? `${Math.round(meeting.duration_seconds / 60)} min`
                    : "N/A"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-3 w-3" />
                <span>Org: {meeting.org_id}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action Items & Objections row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Action Items</CardTitle>
          </CardHeader>
          <CardContent>
            {content?.action_items && content.action_items.length > 0 ? (
              <ul className="space-y-3 text-sm" dir="rtl">
                {content.action_items.map((item, idx) => (
                  <li
                    key={idx}
                    className="rounded-md border border-gray-200 bg-white p-3 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium text-gray-900">{item.task}</p>
                      {item.confidence !== undefined && (
                        <span className="text-xs text-gray-500">
                          {Math.round(item.confidence * 100)}%
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-2 text-xs text-gray-500">
                      {item.assignee && (
                        <span>Owner: {item.assignee}</span>
                      )}
                      {item.due && <span>Due: {item.due}</span>}
                    </div>
                    {item.source && (
                      <p className="mt-2 text-[11px] text-gray-400">
                        מקור: “{item.source}”
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">
                No explicit action items were detected in this conversation.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Objections & Risks</CardTitle>
          </CardHeader>
          <CardContent>
            {content?.crm_entities?.deal_value ||
            content?.crm_entities?.next_meeting_date ||
            content?.crm_entities?.contact_email ? (
              <div className="space-y-3 text-sm" dir="rtl">
                {content.crm_entities?.deal_value && (
                  <div className="rounded-md border border-gray-200 bg-white p-3 shadow-sm">
                    <p className="font-medium text-gray-900">Deal Value</p>
                    <p className="text-xs text-gray-600 mt-1">
                      {content.crm_entities.deal_value.value}{" "}
                      {content.crm_entities.deal_value.currency}
                    </p>
                    {content.crm_entities.deal_value.source && (
                      <p className="mt-2 text-[11px] text-gray-400">
                        מקור: “{content.crm_entities.deal_value.source}”
                      </p>
                    )}
                  </div>
                )}

                {content.crm_entities?.next_meeting_date && (
                  <div className="rounded-md border border-gray-200 bg-white p-3 shadow-sm">
                    <p className="font-medium text-gray-900">Next Meeting</p>
                    <p className="text-xs text-gray-600 mt-1">
                      {content.crm_entities.next_meeting_date.value}
                    </p>
                    {content.crm_entities.next_meeting_date.source && (
                      <p className="mt-2 text-[11px] text-gray-400">
                        מקור: “{content.crm_entities.next_meeting_date.source}”
                      </p>
                    )}
                  </div>
                )}

                {content.crm_entities?.contact_email && (
                  <div className="rounded-md border border-gray-200 bg-white p-3 shadow-sm">
                    <p className="font-medium text-gray-900">Contact Email</p>
                    <p className="text-xs text-gray-600 mt-1">
                      {content.crm_entities.contact_email.value}
                    </p>
                    {content.crm_entities.contact_email.source && (
                      <p className="mt-2 text-[11px] text-gray-400">
                        מקור: “{content.crm_entities.contact_email.source}”
                      </p>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                No explicit objections or CRM entities were extracted. Review the
                transcript for hidden risks.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Transcript */}
      <Card>
        <CardHeader>
          <CardTitle>Full Transcript</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className={cn(
              "h-80 overflow-y-auto rounded-md border border-gray-200 bg-white p-4",
              "text-sm leading-relaxed text-gray-800",
              "whitespace-pre-wrap"
            )}
            dir="rtl"
          >
            {meeting.transcript || "No transcript available for this meeting."}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

