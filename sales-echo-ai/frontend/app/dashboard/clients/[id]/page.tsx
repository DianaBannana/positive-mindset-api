"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  User,
  Phone,
  Mail,
  Building2,
  Calendar,
  Clock,
  TrendingUp,
  TrendingDown,
  Activity,
  MessageSquare,
  ChevronRight,
  Edit,
  ExternalLink,
  Loader2,
  RefreshCw,
  FileText,
  Flame,
  Thermometer,
  Snowflake,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { 
  Client, 
  ClientTimelineResponse, 
  ClientMeetingSummary, 
  SentimentTrendPoint,
  RelationshipStage 
} from "@/lib/types";
import { getOrgId, getApiUrl } from "@/lib/org";

const API_URL = getApiUrl();

// Stage badge colors
const stageColors: Record<RelationshipStage, string> = {
  new: "bg-blue-100 text-blue-700 border-blue-200",
  engaged: "bg-emerald-100 text-emerald-700 border-emerald-200",
  nurturing: "bg-amber-100 text-amber-700 border-amber-200",
  closing: "bg-purple-100 text-purple-700 border-purple-200",
  won: "bg-green-100 text-green-800 border-green-200",
  lost: "bg-red-100 text-red-700 border-red-200",
};

const stageLabels: Record<RelationshipStage, string> = {
  new: "New",
  engaged: "Engaged",
  nurturing: "Nurturing",
  closing: "Closing",
  won: "Won",
  lost: "Lost",
};

// Deal heat helpers
const getDealHeatConfig = (heat: string | null) => {
  switch (heat) {
    case "hot":
      return { icon: Flame, color: "text-red-500", bg: "bg-red-50", label: "Hot" };
    case "warm":
      return { icon: Thermometer, color: "text-amber-500", bg: "bg-amber-50", label: "Warm" };
    default:
      return { icon: Snowflake, color: "text-blue-500", bg: "bg-blue-50", label: "Cold" };
  }
};

export default function ClientTimelinePage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params?.id as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [client, setClient] = useState<Client | null>(null);
  const [meetings, setMeetings] = useState<ClientMeetingSummary[]>([]);
  const [sentimentTrend, setSentimentTrend] = useState<SentimentTrendPoint[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const orgId = getOrgId();

  const fetchClientData = useCallback(async () => {
    if (!clientId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/clients/${clientId}?org_id=${orgId}`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Client not found");
        }
        throw new Error("Failed to fetch client");
      }

      const data: ClientTimelineResponse = await response.json();
      setClient(data.client);
      setMeetings(data.meetings);
      setSentimentTrend(data.sentiment_trend);

    } catch (err) {
      console.error("Client fetch error:", err);
      setError(err instanceof Error ? err.message : "Failed to load client");
    } finally {
      setLoading(false);
    }
  }, [clientId, orgId]);

  useEffect(() => {
    fetchClientData();
  }, [fetchClientData]);

  const handleBack = () => {
    router.push("/dashboard/clients");
  };

  const handleMeetingClick = (meetingId: string) => {
    router.push(`/dashboard/meetings/${meetingId}`);
  };

  const handleRefreshStats = async () => {
    setRefreshing(true);
    try {
      await fetch(
        `${API_URL}/api/v1/clients/${clientId}/refresh-stats?org_id=${orgId}`,
        { method: "POST" }
      );
      await fetchClientData();
    } catch (err) {
      console.error("Refresh error:", err);
    } finally {
      setRefreshing(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "—";
    const date = new Date(dateStr);
    return date.toLocaleDateString("he-IL", { 
      day: "numeric", 
      month: "long", 
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "—";
    const mins = Math.floor(seconds / 60);
    return `${mins} min`;
  };

  const getSentimentDisplay = (score: number | null) => {
    if (score === null) return { label: "Unknown", color: "text-gray-400", icon: Activity };
    if (score > 0.3) return { label: "Positive", color: "text-emerald-600", icon: TrendingUp };
    if (score < -0.3) return { label: "Negative", color: "text-red-600", icon: TrendingDown };
    return { label: "Neutral", color: "text-amber-600", icon: Activity };
  };

  // Calculate sentiment trend line (simple SVG)
  const renderSentimentChart = () => {
    if (sentimentTrend.length < 2) return null;

    const width = 200;
    const height = 60;
    const padding = 10;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    const points = sentimentTrend
      .filter(p => p.score !== null)
      .map((point, idx, arr) => {
        const x = padding + (idx / (arr.length - 1)) * chartWidth;
        // Map score from [-1, 1] to [chartHeight, 0] (inverted Y)
        const y = padding + ((1 - (point.score! + 1) / 2) * chartHeight);
        return `${x},${y}`;
      })
      .join(" ");

    const lastPoint = sentimentTrend[sentimentTrend.length - 1];
    const trendColor = lastPoint?.score === null ? "#9CA3AF" :
      lastPoint.score > 0.3 ? "#10B981" :
      lastPoint.score < -0.3 ? "#EF4444" : "#F59E0B";

    return (
      <svg width={width} height={height} className="overflow-visible">
        {/* Grid lines */}
        <line x1={padding} y1={height/2} x2={width-padding} y2={height/2} stroke="#E5E7EB" strokeDasharray="2,2" />
        
        {/* Trend line */}
        <polyline
          fill="none"
          stroke={trendColor}
          strokeWidth="2"
          points={points}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* Points */}
        {sentimentTrend.filter(p => p.score !== null).map((point, idx, arr) => {
          const x = padding + (idx / (arr.length - 1)) * chartWidth;
          const y = padding + ((1 - (point.score! + 1) / 2) * chartHeight);
          return (
            <circle
              key={idx}
              cx={x}
              cy={y}
              r="4"
              fill={trendColor}
            />
          );
        })}
      </svg>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={handleBack} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Clients
        </Button>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-12 text-center text-red-700">
            {error || "Client not found"}
          </CardContent>
        </Card>
      </div>
    );
  }

  const sentiment = getSentimentDisplay(client.avg_sentiment_score);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Button variant="ghost" onClick={handleBack} className="gap-2 shrink-0">
            <ArrowLeft className="h-4 w-4" />
            Clients
          </Button>
          
          <div className="flex items-center gap-4">
            {/* Avatar */}
            <div className="h-16 w-16 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-xl font-bold shrink-0">
              {client.full_name 
                ? client.full_name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()
                : <User className="h-8 w-8" />
              }
            </div>
            
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {client.full_name || client.company_name || client.phone}
              </h1>
              <div className="flex items-center gap-3 mt-1 flex-wrap">
                <Badge variant="outline" className={cn("text-sm", stageColors[client.relationship_stage])}>
                  {stageLabels[client.relationship_stage]}
                </Badge>
                {client.external_crm_id && (
                  <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                    <ExternalLink className="h-3 w-3 mr-1" />
                    {client.external_crm_type || "CRM"}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            onClick={handleRefreshStats}
            disabled={refreshing}
            className="gap-2"
          >
            <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
            Refresh
          </Button>
          <Button variant="outline" className="gap-2">
            <Edit className="h-4 w-4" />
            Edit
          </Button>
        </div>
      </div>

      {/* Contact Info & Stats */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Contact Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Contact Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <Phone className="h-5 w-5 text-gray-400" />
              <span className="font-mono">{client.phone}</span>
            </div>
            {client.email && (
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-gray-400" />
                <span>{client.email}</span>
              </div>
            )}
            {client.company_name && (
              <div className="flex items-center gap-3">
                <Building2 className="h-5 w-5 text-gray-400" />
                <span>{client.company_name}</span>
              </div>
            )}
            <div className="pt-4 border-t space-y-2 text-sm text-gray-500">
              <div className="flex justify-between">
                <span>First Contact</span>
                <span className="text-gray-900">{formatDate(client.first_contact_at)}</span>
              </div>
              <div className="flex justify-between">
                <span>Last Contact</span>
                <span className="text-gray-900">{formatDate(client.last_contact_at)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Engagement Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Engagement</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 rounded-lg bg-indigo-50 text-center">
                <p className="text-2xl font-bold text-indigo-900">{client.total_meetings}</p>
                <p className="text-xs text-indigo-600">Meetings</p>
              </div>
              <div className="p-3 rounded-lg bg-purple-50 text-center">
                <p className="text-2xl font-bold text-purple-900">
                  {client.total_talk_minutes ? Math.round(client.total_talk_minutes) : 0}
                </p>
                <p className="text-xs text-purple-600">Minutes</p>
              </div>
            </div>
            
            <div className="pt-4 border-t">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-500">Overall Sentiment</span>
                <div className={cn("flex items-center gap-1", sentiment.color)}>
                  <sentiment.icon className="h-4 w-4" />
                  <span className="text-sm font-medium">{sentiment.label}</span>
                </div>
              </div>
              {client.avg_sentiment_score !== null && (
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className={cn(
                      "h-full rounded-full transition-all",
                      client.avg_sentiment_score > 0.3 ? "bg-emerald-500" :
                      client.avg_sentiment_score < -0.3 ? "bg-red-500" : "bg-amber-500"
                    )}
                    style={{ width: `${((client.avg_sentiment_score + 1) / 2) * 100}%` }}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Sentiment Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sentiment Trend</CardTitle>
            <CardDescription>Relationship sentiment over time</CardDescription>
          </CardHeader>
          <CardContent>
            {sentimentTrend.length >= 2 ? (
              <div className="flex flex-col items-center">
                {renderSentimentChart()}
                <p className="text-xs text-gray-500 mt-2">
                  Based on {sentimentTrend.length} meeting{sentimentTrend.length !== 1 ? "s" : ""}
                </p>
              </div>
            ) : (
              <div className="text-center py-6 text-gray-400">
                <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">More meetings needed for trend</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Meeting Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-indigo-600" />
            Meeting Timeline
          </CardTitle>
          <CardDescription>
            All meetings with this client in chronological order
          </CardDescription>
        </CardHeader>
        <CardContent>
          {meetings.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No meetings recorded yet</p>
            </div>
          ) : (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />
              
              {/* Timeline items */}
              <div className="space-y-6">
                {meetings.map((meeting, idx) => {
                  const heatConfig = getDealHeatConfig(meeting.deal_heat);
                  const HeatIcon = heatConfig.icon;
                  
                  return (
                    <div
                      key={meeting.id}
                      className="relative pl-14 cursor-pointer group"
                      onClick={() => handleMeetingClick(meeting.id)}
                    >
                      {/* Timeline dot */}
                      <div className={cn(
                        "absolute left-4 w-4 h-4 rounded-full border-2 border-white shadow",
                        meeting.status === "COMPLETED" ? "bg-emerald-500" :
                        meeting.status === "FAILED" ? "bg-red-500" :
                        "bg-amber-500"
                      )} />
                      
                      {/* Meeting card */}
                      <div className="p-4 rounded-lg border border-gray-200 bg-white group-hover:border-indigo-300 group-hover:shadow-md transition-all">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap mb-2">
                              <span className="text-sm font-medium text-gray-900">
                                {formatDate(meeting.created_at)}
                              </span>
                              <Badge 
                                variant="outline" 
                                className={cn(
                                  "text-xs",
                                  meeting.status === "COMPLETED" ? "bg-emerald-50 text-emerald-700" :
                                  meeting.status === "FAILED" ? "bg-red-50 text-red-700" :
                                  "bg-amber-50 text-amber-700"
                                )}
                              >
                                {meeting.status}
                              </Badge>
                              {meeting.deal_heat && (
                                <Badge variant="outline" className={cn("text-xs", heatConfig.bg, heatConfig.color)}>
                                  <HeatIcon className="h-3 w-3 mr-1" />
                                  {heatConfig.label}
                                </Badge>
                              )}
                            </div>
                            
                            {meeting.summary_text ? (
                              <p className="text-sm text-gray-600 line-clamp-2" dir="auto">
                                {meeting.summary_text}
                              </p>
                            ) : (
                              <p className="text-sm text-gray-400 italic">No summary available</p>
                            )}
                            
                            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {formatDuration(meeting.duration_seconds)}
                              </span>
                              {meeting.confidence_score !== null && (
                                <span className="flex items-center gap-1">
                                  <Activity className="h-3 w-3" />
                                  {Math.round(meeting.confidence_score * 100)}% confidence
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-indigo-500 shrink-0" />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Notes */}
      {client.notes && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-gray-600" />
              Notes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700 whitespace-pre-wrap" dir="auto">
              {client.notes}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
