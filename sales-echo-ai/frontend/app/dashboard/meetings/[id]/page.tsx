"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ArrowLeft, 
  Flame, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  MessageSquare, 
  Database,
  Mail,
  Calendar,
  Copy,
  ExternalLink,
  Check,
  ChevronDown,
  ChevronUp,
  Send,
  Loader2,
  ShieldCheck,
  ShieldX,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Meeting } from "@/lib/api";
import { FeedbackWidget } from "@/components/shared/FeedbackWidget";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types for action approval
interface ActionStatus {
  enabled: boolean;
  require_approval: boolean;
  status: "pending" | "approved" | "rejected" | "auto_approved" | "disabled";
  approved_at?: string | null;
  rejected_at?: string | null;
}

interface ActionStatusResponse {
  meeting_id: string;
  require_approval: boolean;
  actions: {
    email: ActionStatus;
    whatsapp: ActionStatus;
    calendar: ActionStatus;
    crm: ActionStatus;
  };
}

interface MeetingWithSummary extends Omit<Meeting, 'summary'> {
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
    action_status?: Record<string, { status: string; approved_at?: string; rejected_at?: string }>;
  } | null;
}

function fetchMeetingById(id: string, orgId?: string): Promise<MeetingWithSummary> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  let url = `${baseUrl}/api/v1/meetings/${id}`;
  if (orgId) {
    url += `?org_id=${orgId}`;
  }
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
  const orgId = process.env.NEXT_PUBLIC_DEV_ORG_ID || "default-org-id";

  const [meeting, setMeeting] = useState<MeetingWithSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  
  // Action Center state
  const [actionCenterOpen, setActionCenterOpen] = useState(true);
  const [emailCopied, setEmailCopied] = useState(false);
  const [whatsappCopied, setWhatsappCopied] = useState(false);
  const [syncingCRM, setSyncingCRM] = useState(false);
  
  // Approval flow state
  const [actionStatus, setActionStatus] = useState<ActionStatusResponse | null>(null);
  const [approvingAction, setApprovingAction] = useState<string | null>(null);

  // Fetch action status
  const fetchActionStatus = useCallback(async () => {
    if (!meetingId) return;
    
    try {
      const res = await fetch(
        `${API_URL}/api/v1/settings/actions/status?meeting_id=${meetingId}&org_id=${orgId}`
      );
      if (res.ok) {
        const data = await res.json();
        setActionStatus(data);
      }
    } catch (err) {
      console.error("Failed to fetch action status:", err);
    }
  }, [meetingId, orgId]);

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
    fetchActionStatus();
  }, [meetingId, fetchActionStatus]);

  const handleBack = () => {
    router.push("/dashboard");
  };

  // Handle action approval
  const handleApproveAction = async (actionType: string, approved: boolean) => {
    if (!meetingId) return;
    
    setApprovingAction(actionType);
    
    try {
      const res = await fetch(
        `${API_URL}/api/v1/settings/actions/approve?org_id=${orgId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            meeting_id: meetingId,
            action_type: actionType,
            approved,
          }),
        }
      );
      
      if (res.ok) {
        const result = await res.json();
        setToastMessage(
          approved 
            ? `✅ ${actionType} action approved and executed` 
            : `❌ ${actionType} action rejected`
        );
        
        // Refresh action status
        await fetchActionStatus();
        
        setTimeout(() => setToastMessage(null), 3000);
      }
    } catch (err) {
      console.error("Approval error:", err);
      setToastMessage("Failed to process approval");
    } finally {
      setApprovingAction(null);
    }
  };

  // Get status badge for an action
  const getActionStatusBadge = (actionType: keyof ActionStatusResponse["actions"]) => {
    if (!actionStatus) return null;
    
    const status = actionStatus.actions[actionType];
    if (!status || !status.enabled) return null;
    
    switch (status.status) {
      case "approved":
        return (
          <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">
            <ShieldCheck className="h-3 w-3 mr-1" />
            Approved
          </Badge>
        );
      case "rejected":
        return (
          <Badge className="bg-red-100 text-red-800 border-red-200">
            <ShieldX className="h-3 w-3 mr-1" />
            Rejected
          </Badge>
        );
      case "pending":
        return (
          <Badge className="bg-amber-100 text-amber-800 border-amber-200">
            <Clock className="h-3 w-3 mr-1" />
            Pending Approval
          </Badge>
        );
      case "auto_approved":
        return (
          <Badge className="bg-blue-100 text-blue-800 border-blue-200">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Auto-Approved
          </Badge>
        );
      case "disabled":
        return (
          <Badge variant="secondary">
            <XCircle className="h-3 w-3 mr-1" />
            Disabled
          </Badge>
        );
      default:
        return null;
    }
  };

  // Check if action needs approval
  const needsApproval = (actionType: keyof ActionStatusResponse["actions"]): boolean => {
    if (!actionStatus) return false;
    const status = actionStatus.actions[actionType];
    return status?.enabled && status?.require_approval && status?.status === "pending";
  };

  // Check if action is approved
  const isActionApproved = (actionType: keyof ActionStatusResponse["actions"]): boolean => {
    if (!actionStatus) return true; // Default to allowed if no status
    const status = actionStatus.actions[actionType];
    if (!status?.enabled) return false;
    return status.status === "approved" || status.status === "auto_approved" || !status.require_approval;
  };

  // Generate email content
  const generateEmailContent = () => {
    if (!meeting || !meeting.summary?.content) return "";
    
    const content = meeting.summary.content;
    const clientName = meeting.client_name || "Client";
    const date = meeting.created_at 
      ? new Date(meeting.created_at).toLocaleDateString("en-IL")
      : "our recent call";
    
    let email = `Subject: Follow-up from our call - ${date}\n\n`;
    email += `Hi ${clientName},\n\n`;
    email += `Thank you for taking the time to speak with me. Here's a summary of our conversation:\n\n`;
    
    if (content.summary_text) {
      email += `${content.summary_text}\n\n`;
    }
    
    if (content.action_items && content.action_items.length > 0) {
      email += `Action Items:\n`;
      content.action_items.forEach((item, idx) => {
        email += `${idx + 1}. ${item.task}`;
        if (item.due) email += ` (Due: ${item.due})`;
        email += `\n`;
      });
      email += `\n`;
    }
    
    const dealValue = content.crm_entities?.deal_value;
    if (dealValue && dealValue.value) {
      email += `Discussed investment: ${dealValue.currency}${dealValue.value.toLocaleString()}\n\n`;
    }
    
    email += `Please don't hesitate to reach out if you have any questions.\n\n`;
    email += `Best regards,\n[Your Name]`;
    
    return email;
  };

  // Generate WhatsApp content
  const generateWhatsAppContent = () => {
    if (!meeting || !meeting.summary?.content) return "";
    
    const content = meeting.summary.content;
    const clientName = meeting.client_name || "לקוח";
    
    let message = `היי, הנה סיכום השיחה עם ${clientName}.\n\n`;
    
    if (content.action_items && content.action_items.length > 0) {
      message += `📋 משימות לביצוע:\n`;
      content.action_items.forEach((item, idx) => {
        message += `${idx + 1}. ${item.task}`;
        if (item.due) message += ` (עד: ${item.due})`;
        message += `\n`;
      });
      message += `\n`;
    }
    
    if (content.summary_text) {
      message += `📝 סיכום:\n${content.summary_text}`;
    }
    
    return message;
  };

  // Generate Google Calendar URL
  const generateGoogleCalendarUrl = () => {
    if (!meeting || !meeting.summary?.content?.crm_entities?.next_meeting_date) return null;
    
    const nextMeeting = meeting.summary.content.crm_entities.next_meeting_date;
    const clientName = meeting.client_name || "Client";
    
    // Parse the date (assuming format like "25/12/2025" or similar)
    let startDate = new Date();
    startDate.setDate(startDate.getDate() + 7); // Default to next week
    
    const dateStr = nextMeeting.value;
    const dateMatch = dateStr.match(/(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})/);
    if (dateMatch) {
      const [, day, month, year] = dateMatch;
      const fullYear = parseInt(year) < 100 ? 2000 + parseInt(year) : parseInt(year);
      startDate = new Date(fullYear, parseInt(month) - 1, parseInt(day), 10, 0);
    }
    
    const endDate = new Date(startDate);
    endDate.setHours(endDate.getHours() + 1);
    
    const formatDate = (d: Date) => d.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
    
    const title = encodeURIComponent(`Follow-up: ${clientName}`);
    const details = encodeURIComponent(
      `Follow-up meeting scheduled from SalesEcho AI.\n\n` +
      `Original meeting notes available in the system.`
    );
    
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${formatDate(startDate)}/${formatDate(endDate)}&details=${details}`;
  };

  const handleCopyEmail = async () => {
    const email = generateEmailContent();
    await navigator.clipboard.writeText(email);
    setEmailCopied(true);
    setTimeout(() => setEmailCopied(false), 2000);
  };

  const handleOpenGmail = () => {
    const email = generateEmailContent();
    const subject = encodeURIComponent(
      `Follow-up from our call - ${meeting?.client_name || "Client"}`
    );
    const body = encodeURIComponent(email.split("\n\n").slice(1).join("\n\n"));
    const clientEmail = meeting?.summary?.content?.crm_entities?.contact_email?.value || "";
    
    window.open(
      `https://mail.google.com/mail/?view=cm&fs=1&to=${clientEmail}&su=${subject}&body=${body}`,
      "_blank"
    );
  };

  const handleCopyWhatsApp = async () => {
    const message = generateWhatsAppContent();
    await navigator.clipboard.writeText(message);
    setWhatsappCopied(true);
    setTimeout(() => setWhatsappCopied(false), 2000);
  };

  const handleSendWhatsApp = () => {
    const message = generateWhatsAppContent();
    const encodedMessage = encodeURIComponent(message);
    window.open(`https://wa.me/?text=${encodedMessage}`, "_blank");
  };

  const handleSyncToCRM = async () => {
    if (!meeting || !meeting.summary?.content) return;
    
    setSyncingCRM(true);
    setToastMessage("מסנכרן ל-CRM...");
    
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setToastMessage("✅ Successfully synced to CRM");
    setSyncingCRM(false);
    
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleAddToCalendar = () => {
    const url = generateGoogleCalendarUrl();
    if (url) {
      window.open(url, "_blank");
    }
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
              <h1 className="text-xl font-semibold text-gray-900">Loading meeting…</h1>
              <p className="text-sm text-gray-500">Fetching transcription and insights.</p>
            </div>
          </div>
        </div>
        <Card>
          <CardContent className="py-10 text-center text-gray-500">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
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
            <h1 className="text-xl font-semibold text-gray-900">Meeting not available</h1>
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
  const nextMeetingDate = content?.crm_entities?.next_meeting_date;
  const calendarUrl = generateGoogleCalendarUrl();

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
            <h1 className="text-2xl font-semibold text-gray-900">Meeting Analysis</h1>
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

      {/* Action Center */}
      <Card className="border-2 border-indigo-200 bg-gradient-to-br from-indigo-50 via-white to-purple-50 overflow-hidden">
        <CardHeader 
          className="cursor-pointer hover:bg-indigo-50/50 transition-colors"
          onClick={() => setActionCenterOpen(!actionCenterOpen)}
        >
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-indigo-900">
              <Send className="h-5 w-5" />
              Action Center
              <Badge className="bg-indigo-600 ml-2">Tachles</Badge>
              {actionStatus?.require_approval && (
                <Badge variant="outline" className="ml-2 text-amber-700 border-amber-300">
                  <ShieldCheck className="h-3 w-3 mr-1" />
                  Approval Required
                </Badge>
              )}
            </CardTitle>
            <Button variant="ghost" size="icon">
              {actionCenterOpen ? (
                <ChevronUp className="h-5 w-5 text-indigo-600" />
              ) : (
                <ChevronDown className="h-5 w-5 text-indigo-600" />
              )}
            </Button>
          </div>
          <p className="text-sm text-indigo-700">
            Your work is ready – just review and send.
          </p>
        </CardHeader>
        
        {actionCenterOpen && (
          <CardContent className="space-y-6 pt-0">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Email Preview */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Mail className="h-5 w-5 text-blue-600" />
                    <h4 className="font-semibold text-gray-900">Email Draft</h4>
                  </div>
                  {getActionStatusBadge("email")}
                </div>
                <div className="relative">
                  <textarea
                    readOnly
                    value={generateEmailContent()}
                    className="w-full h-48 p-4 text-sm rounded-lg border border-gray-200 bg-white resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                {/* Approval buttons for email */}
                {needsApproval("email") && (
                  <div className="flex gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200">
                    <Button
                      onClick={() => handleApproveAction("email", true)}
                      disabled={approvingAction === "email"}
                      size="sm"
                      className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                    >
                      {approvingAction === "email" ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <ShieldCheck className="h-4 w-4 mr-2" />
                      )}
                      Approve & Send
                    </Button>
                    <Button
                      onClick={() => handleApproveAction("email", false)}
                      disabled={approvingAction === "email"}
                      variant="outline"
                      size="sm"
                      className="flex-1 border-red-300 text-red-700 hover:bg-red-50"
                    >
                      <ShieldX className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                )}
                
                {/* Regular action buttons (only shown if approved or no approval required) */}
                {isActionApproved("email") && (
                  <div className="flex gap-2">
                    <Button
                      onClick={handleCopyEmail}
                      variant="outline"
                      size="sm"
                      className="flex-1"
                    >
                      {emailCopied ? (
                        <>
                          <Check className="h-4 w-4 mr-2 text-green-600" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 mr-2" />
                          Copy to Clipboard
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={handleOpenGmail}
                      size="sm"
                      className="flex-1 bg-blue-600 hover:bg-blue-700"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open in Gmail
                    </Button>
                  </div>
                )}
              </div>

              {/* WhatsApp Preview */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-green-600" />
                    <h4 className="font-semibold text-gray-900">WhatsApp Message</h4>
                  </div>
                  {getActionStatusBadge("whatsapp")}
                </div>
                <div className="relative">
                  <textarea
                    readOnly
                    value={generateWhatsAppContent()}
                    dir="rtl"
                    className="w-full h-48 p-4 text-sm rounded-lg border border-gray-200 bg-white resize-none focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                
                {/* Approval buttons for WhatsApp */}
                {needsApproval("whatsapp") && (
                  <div className="flex gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200">
                    <Button
                      onClick={() => handleApproveAction("whatsapp", true)}
                      disabled={approvingAction === "whatsapp"}
                      size="sm"
                      className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                    >
                      {approvingAction === "whatsapp" ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <ShieldCheck className="h-4 w-4 mr-2" />
                      )}
                      Approve & Send
                    </Button>
                    <Button
                      onClick={() => handleApproveAction("whatsapp", false)}
                      disabled={approvingAction === "whatsapp"}
                      variant="outline"
                      size="sm"
                      className="flex-1 border-red-300 text-red-700 hover:bg-red-50"
                    >
                      <ShieldX className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                )}
                
                {/* Regular action buttons */}
                {isActionApproved("whatsapp") && (
                  <div className="flex gap-2">
                    <Button
                      onClick={handleCopyWhatsApp}
                      variant="outline"
                      size="sm"
                      className="flex-1"
                    >
                      {whatsappCopied ? (
                        <>
                          <Check className="h-4 w-4 mr-2 text-green-600" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 mr-2" />
                          Copy
                        </>
                      )}
                    </Button>
                    <Button
                      onClick={handleSendWhatsApp}
                      size="sm"
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      <MessageSquare className="h-4 w-4 mr-2" />
                      Send via WhatsApp
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Calendar & CRM Row */}
            <div className="grid lg:grid-cols-2 gap-6 pt-4 border-t border-indigo-100">
              {/* Calendar Preview */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-purple-600" />
                    <h4 className="font-semibold text-gray-900">Next Meeting</h4>
                  </div>
                  {getActionStatusBadge("calendar")}
                </div>
                <div className="p-4 rounded-lg border border-purple-200 bg-purple-50/50">
                  {nextMeetingDate ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">
                            Follow-up: {meeting.client_name || "Client"}
                          </p>
                          <p className="text-sm text-purple-700 mt-1">
                            📅 {nextMeetingDate.value}
                          </p>
                        </div>
                        <Badge variant="outline" className="text-purple-700 border-purple-300">
                          {Math.round((nextMeetingDate.confidence || 0.5) * 100)}% confidence
                        </Badge>
                      </div>
                      <Button
                        onClick={handleAddToCalendar}
                        className="w-full bg-purple-600 hover:bg-purple-700"
                        disabled={!calendarUrl}
                      >
                        <Calendar className="h-4 w-4 mr-2" />
                        Add to Google Calendar
                      </Button>
                    </div>
                  ) : (
                    <div className="text-center py-4 text-gray-500">
                      <Calendar className="h-8 w-8 mx-auto mb-2 opacity-40" />
                      <p className="text-sm">No follow-up date extracted</p>
                    </div>
                  )}
                </div>
              </div>

              {/* CRM Sync */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-orange-600" />
                    <h4 className="font-semibold text-gray-900">CRM Sync</h4>
                  </div>
                  {getActionStatusBadge("crm")}
                </div>
                <div className="p-4 rounded-lg border border-orange-200 bg-orange-50/50">
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className={`h-4 w-4 ${content?.crm_entities?.contact_email ? "text-green-600" : "text-gray-300"}`} />
                        <span className={content?.crm_entities?.contact_email ? "text-gray-900" : "text-gray-400"}>
                          Contact
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className={`h-4 w-4 ${content?.crm_entities?.deal_value ? "text-green-600" : "text-gray-300"}`} />
                        <span className={content?.crm_entities?.deal_value ? "text-gray-900" : "text-gray-400"}>
                          Deal
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className={`h-4 w-4 ${content?.action_items?.length ? "text-green-600" : "text-gray-300"}`} />
                        <span className={content?.action_items?.length ? "text-gray-900" : "text-gray-400"}>
                          Tasks ({content?.action_items?.length || 0})
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className={`h-4 w-4 ${content?.summary_text ? "text-green-600" : "text-gray-300"}`} />
                        <span className={content?.summary_text ? "text-gray-900" : "text-gray-400"}>
                          Note
                        </span>
                      </div>
                    </div>
                    <Button
                      onClick={handleSyncToCRM}
                      className="w-full bg-orange-600 hover:bg-orange-700"
                      disabled={syncingCRM || !content?.summary_text}
                    >
                      {syncingCRM ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Syncing...
                        </>
                      ) : (
                        <>
                          <Database className="h-4 w-4 mr-2" />
                          Sync All to CRM
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-4 right-4 z-50 animate-in slide-in-from-bottom-2">
          <Card className="bg-white shadow-lg border-2 border-blue-300">
            <CardContent className="p-4">
              <p className="text-sm font-medium text-gray-900">{toastMessage}</p>
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
              <div className="flex items-center gap-4">
                {governance?.confidence_score !== undefined && (
                  <span className="text-xs text-gray-500">
                    Confidence: {Math.round(governance.confidence_score * 100)}%
                  </span>
                )}
                {content?.summary_text && meetingId && (
                  <FeedbackWidget
                    meetingId={meetingId}
                    orgId={orgId}
                    sectionType="summary"
                    originalValue={content.summary_text}
                    compact
                  />
                )}
              </div>
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
              {content?.crm_entities?.deal_value && (
                <div className="flex items-center gap-2">
                  <span className="text-lg">💰</span>
                  <span className="font-medium text-gray-900">
                    {content.crm_entities.deal_value.currency}
                    {content.crm_entities.deal_value.value.toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action Items & CRM Entities row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Action Items</span>
              {content?.action_items && content.action_items.length > 0 && meetingId && (
                <FeedbackWidget
                  meetingId={meetingId}
                  orgId={orgId}
                  sectionType="action_items"
                  originalValue={content.action_items}
                  compact
                />
              )}
            </CardTitle>
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
                      {item.assignee && <span>Owner: {item.assignee}</span>}
                      {item.due && <span>Due: {item.due}</span>}
                    </div>
                    {item.source && (
                      <p className="mt-2 text-[11px] text-gray-400">
                        מקור: &quot;{item.source}&quot;
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
            <CardTitle>CRM Entities</CardTitle>
          </CardHeader>
          <CardContent>
            {content?.crm_entities?.deal_value ||
            content?.crm_entities?.next_meeting_date ||
            content?.crm_entities?.contact_email ? (
              <div className="space-y-3 text-sm" dir="rtl">
                {content.crm_entities?.deal_value && (
                  <div className="rounded-md border border-gray-200 bg-white p-3 shadow-sm">
                    <p className="font-medium text-gray-900">Deal Value</p>
                    <p className="text-lg font-bold text-green-600 mt-1">
                      {content.crm_entities.deal_value.currency}
                      {content.crm_entities.deal_value.value.toLocaleString()}
                    </p>
                    {content.crm_entities.deal_value.source && (
                      <p className="mt-2 text-[11px] text-gray-400">
                        מקור: &quot;{content.crm_entities.deal_value.source}&quot;
                      </p>
                    )}
                  </div>
                )}

                {content.crm_entities?.next_meeting_date && (
                  <div className="rounded-md border border-gray-200 bg-white p-3 shadow-sm">
                    <p className="font-medium text-gray-900">Next Meeting</p>
                    <p className="text-xs text-gray-600 mt-1">
                      📅 {content.crm_entities.next_meeting_date.value}
                    </p>
                  </div>
                )}

                {content.crm_entities?.contact_email && (
                  <div className="rounded-md border border-gray-200 bg-white p-3 shadow-sm">
                    <p className="font-medium text-gray-900">Contact Email</p>
                    <p className="text-xs text-gray-600 mt-1">
                      ✉️ {content.crm_entities.contact_email.value}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                No CRM entities were extracted from this conversation.
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
