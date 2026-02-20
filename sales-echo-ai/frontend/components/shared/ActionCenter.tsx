"use client";

import React, { useState } from "react";
import {
  Mail,
  MessageCircle,
  Calendar,
  Database,
  ExternalLink,
  Check,
  Loader2,
  Send,
  Clock,
  User,
  Sparkles,
  ArrowRight,
  Copy,
  CheckCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/use-toast";
import { ActionItem } from "@/lib/types";

interface ActionCenterProps {
  meetingId: string;
  clientName?: string | null;
  clientPhone?: string | null;
  clientEmail?: string | null;
  summaryText?: string | null;
  actionItems?: ActionItem[];
  nextMeetingDate?: string | null;
  onSync?: (type: string) => void;
  className?: string;
}

interface TaskCardProps {
  task: ActionItem;
  index: number;
  clientName?: string | null;
  clientEmail?: string | null;
}

function TaskCard({ task, index, clientName, clientEmail }: TaskCardProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const handleCopy = async () => {
    await navigator.clipboard.writeText(task.task);
    setCopied(true);
    toast({ title: "Copied!", description: "Task copied to clipboard" });
    setTimeout(() => setCopied(false), 2000);
  };

  // Generate mailto link with pre-filled content
  const mailtoLink = clientEmail
    ? `mailto:${clientEmail}?subject=${encodeURIComponent(
        `Follow-up: ${task.task.slice(0, 50)}`
      )}&body=${encodeURIComponent(
        `Hi ${clientName || ""},\n\nFollowing up on our conversation regarding:\n\n${task.task}\n\nPlease let me know if you have any questions.\n\nBest regards`
      )}`
    : "#";

  const confidenceColor =
    (task.confidence || 0) >= 0.8
      ? "bg-emerald-100 text-emerald-700 border-emerald-200"
      : (task.confidence || 0) >= 0.6
      ? "bg-amber-100 text-amber-700 border-amber-200"
      : "bg-red-100 text-red-700 border-red-200";

  return (
    <div
      className={cn(
        "group relative p-4 rounded-xl border-2 transition-all duration-200",
        "bg-white hover:border-indigo-200 hover:shadow-lg",
        "border-gray-100"
      )}
    >
      {/* Task Number Badge */}
      <div className="absolute -top-2 -left-2 h-6 w-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center shadow-sm">
        {index + 1}
      </div>

      {/* Content */}
      <div className="space-y-3">
        <p className="text-gray-900 font-medium leading-relaxed pr-8" dir="auto">
          {task.task}
        </p>

        {/* Meta Row */}
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {task.assignee && (
            <Badge variant="outline" className="bg-gray-50 text-gray-600 border-gray-200">
              <User className="h-3 w-3 mr-1" />
              {task.assignee}
            </Badge>
          )}
          {task.due && (
            <Badge variant="outline" className="bg-blue-50 text-blue-600 border-blue-200">
              <Clock className="h-3 w-3 mr-1" />
              {task.due}
            </Badge>
          )}
          {task.confidence !== undefined && (
            <Badge variant="outline" className={confidenceColor}>
              {Math.round(task.confidence * 100)}%
            </Badge>
          )}
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2 pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleCopy}
            className="h-7 text-xs gap-1 text-gray-500 hover:text-gray-900"
          >
            {copied ? <CheckCircle className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
            {copied ? "Copied" : "Copy"}
          </Button>

          {clientEmail && (
            <a href={mailtoLink}>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs gap-1 text-indigo-600 hover:text-indigo-800"
              >
                <Mail className="h-3 w-3" />
                Email
              </Button>
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

export function ActionCenter({
  meetingId,
  clientName,
  clientPhone,
  clientEmail,
  summaryText,
  actionItems = [],
  nextMeetingDate,
  onSync,
  className,
}: ActionCenterProps) {
  const [syncing, setSyncing] = useState<Record<string, boolean>>({});
  const [synced, setSynced] = useState<Record<string, boolean>>({});
  const { toast } = useToast();

  // Generate WhatsApp message
  const generateWhatsAppMessage = () => {
    let message = `שלום ${clientName || ""},\n\n`;
    message += `תודה על השיחה!\n\n`;

    if (actionItems.length > 0) {
      message += `📋 לסיכום, אלו הצעדים הבאים:\n`;
      actionItems.slice(0, 3).forEach((item, idx) => {
        message += `${idx + 1}. ${item.task}\n`;
      });
      message += `\n`;
    }

    if (nextMeetingDate) {
      message += `📅 פגישה הבאה: ${nextMeetingDate}\n\n`;
    }

    message += `נשמח לעמוד לשירותך!`;
    return message;
  };

  // Generate WhatsApp link
  const getWhatsAppLink = () => {
    if (!clientPhone) return "#";
    const cleanPhone = clientPhone.replace(/[^0-9+]/g, "");
    const message = encodeURIComponent(generateWhatsAppMessage());
    return `https://wa.me/${cleanPhone}?text=${message}`;
  };

  // Generate email content
  const getEmailLink = () => {
    if (!clientEmail) return "#";

    const subject = encodeURIComponent(`סיכום שיחה - ${clientName || "לקוח"}`);
    let body = `שלום ${clientName || ""},\n\n`;
    body += `תודה על הזמן שהקדשת לשיחה שלנו.\n\n`;

    if (summaryText) {
      body += `📝 סיכום:\n${summaryText.slice(0, 500)}...\n\n`;
    }

    if (actionItems.length > 0) {
      body += `📋 צעדים הבאים:\n`;
      actionItems.forEach((item, idx) => {
        body += `${idx + 1}. ${item.task}\n`;
      });
      body += `\n`;
    }

    body += `נשמח לעמוד לשירותך,\nצוות המכירות`;

    return `mailto:${clientEmail}?subject=${subject}&body=${encodeURIComponent(body)}`;
  };

  const handleSync = async (type: string) => {
    setSyncing((prev) => ({ ...prev, [type]: true }));

    // Simulate sync delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    setSyncing((prev) => ({ ...prev, [type]: false }));
    setSynced((prev) => ({ ...prev, [type]: true }));

    toast({
      title: "Synced Successfully!",
      description: `${type} data synced to CRM`,
      variant: "success",
    });

    onSync?.(type);
  };

  return (
    <Card className={cn("border-2 border-indigo-100 bg-gradient-to-br from-indigo-50/50 via-white to-purple-50/50", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Sparkles className="h-5 w-5 text-indigo-600" />
          Action Center
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Magic Buttons */}
        <div className="grid sm:grid-cols-2 gap-3">
          {/* WhatsApp Magic Button */}
          <a
            href={getWhatsAppLink()}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(!clientPhone && "pointer-events-none opacity-50")}
          >
            <Button
              variant="outline"
              className="w-full h-auto py-3 justify-start gap-3 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 hover:from-green-100 hover:to-emerald-100 hover:border-green-300 transition-all group"
              disabled={!clientPhone}
            >
              <div className="h-10 w-10 rounded-full bg-green-500 flex items-center justify-center text-white shrink-0">
                <MessageCircle className="h-5 w-5" />
              </div>
              <div className="text-left">
                <p className="font-semibold text-green-800">Send WhatsApp</p>
                <p className="text-xs text-green-600">AI-generated summary</p>
              </div>
              <ExternalLink className="h-4 w-4 text-green-500 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
            </Button>
          </a>

          {/* Email Magic Button */}
          <a
            href={getEmailLink()}
            className={cn(!clientEmail && "pointer-events-none opacity-50")}
          >
            <Button
              variant="outline"
              className="w-full h-auto py-3 justify-start gap-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 hover:from-blue-100 hover:to-indigo-100 hover:border-blue-300 transition-all group"
              disabled={!clientEmail}
            >
              <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white shrink-0">
                <Mail className="h-5 w-5" />
              </div>
              <div className="text-left">
                <p className="font-semibold text-blue-800">Send Email</p>
                <p className="text-xs text-blue-600">Pre-filled follow-up</p>
              </div>
              <ExternalLink className="h-4 w-4 text-blue-500 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
            </Button>
          </a>

          {/* Calendar Sync Button */}
          <Button
            variant="outline"
            className="w-full h-auto py-3 justify-start gap-3 bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200 hover:from-purple-100 hover:to-pink-100 hover:border-purple-300 transition-all group"
            onClick={() => handleSync("calendar")}
            disabled={syncing.calendar || !nextMeetingDate}
          >
            <div className="h-10 w-10 rounded-full bg-purple-500 flex items-center justify-center text-white shrink-0">
              {syncing.calendar ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : synced.calendar ? (
                <Check className="h-5 w-5" />
              ) : (
                <Calendar className="h-5 w-5" />
              )}
            </div>
            <div className="text-left">
              <p className="font-semibold text-purple-800">Add to Calendar</p>
              <p className="text-xs text-purple-600">
                {nextMeetingDate || "No date detected"}
              </p>
            </div>
            {synced.calendar && (
              <Badge className="ml-auto bg-purple-500 text-white">Synced</Badge>
            )}
          </Button>

          {/* CRM Sync Button */}
          <Button
            variant="outline"
            className="w-full h-auto py-3 justify-start gap-3 bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200 hover:from-amber-100 hover:to-orange-100 hover:border-amber-300 transition-all group"
            onClick={() => handleSync("crm")}
            disabled={syncing.crm}
          >
            <div className="h-10 w-10 rounded-full bg-amber-500 flex items-center justify-center text-white shrink-0">
              {syncing.crm ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : synced.crm ? (
                <Check className="h-5 w-5" />
              ) : (
                <Database className="h-5 w-5" />
              )}
            </div>
            <div className="text-left">
              <p className="font-semibold text-amber-800">Sync to CRM</p>
              <p className="text-xs text-amber-600">Push meeting summary</p>
            </div>
            {synced.crm && (
              <Badge className="ml-auto bg-amber-500 text-white">Synced</Badge>
            )}
          </Button>
        </div>

        {/* Task Cards */}
        {actionItems.length > 0 && (
          <div className="pt-4 border-t border-indigo-100">
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Send className="h-4 w-4 text-indigo-600" />
              Action Items ({actionItems.length})
            </h4>
            <div className="space-y-3">
              {actionItems.slice(0, 5).map((task, idx) => (
                <TaskCard
                  key={idx}
                  task={task}
                  index={idx}
                  clientName={clientName}
                  clientEmail={clientEmail}
                />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
