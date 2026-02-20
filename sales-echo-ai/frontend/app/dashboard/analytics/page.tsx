"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle,
  Clock,
  AlertTriangle,
  Flame,
  Thermometer,
  Snowflake,
  Activity,
  BarChart3,
  ListTodo,
  RefreshCw,
  Play,
  Phone,
  Loader2,
  Brain,
  ThumbsUp,
  ThumbsDown,
  Lightbulb,
  ChevronRight,
  Settings,
  Eye,
  EyeOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Types for analytics data
interface ActionItemStats {
  total: number;
  pending: number;
  high_confidence: number;
  by_assignee: Record<string, number>;
}

interface SentimentBreakdown {
  positive: number;
  neutral: number;
  negative: number;
  average_score: number;
}

interface DealHeatStats {
  hot: number;
  warm: number;
  cold: number;
  total_pipeline_value: number;
  currency: string;
}

interface TimeSeriesPoint {
  date: string;
  value: number;
}

interface AnalyticsSummary {
  org_id: string;
  period_start: string;
  period_end: string;
  total_meetings: number;
  completed_meetings: number;
  failed_meetings: number;
  pending_meetings: number;
  total_duration_minutes: number;
  average_duration_minutes: number;
  action_items: ActionItemStats;
  sentiment: SentimentBreakdown;
  deal_heat: DealHeatStats;
  average_confidence: number;
  requires_review_count: number;
  meetings_by_day: TimeSeriesPoint[];
  pipeline_by_day: TimeSeriesPoint[];
  top_users: Array<{
    user_id: string;
    meeting_count: number;
    total_duration_minutes: number;
  }>;
  generated_at: string;
}

interface ActionItem {
  meeting_id: string;
  meeting_date: string;
  client_name: string | null;
  task: string;
  due: string | null;
  assignee: string | null;
  confidence: number;
}

interface ManagerInsights {
  period_days: number;
  total_meetings: number;
  total_feedback: number;
  accuracy_rate: number;
  section_accuracy: Record<string, number>;
  common_issues: Array<{
    section: string;
    type: string;
    note: string;
    date: string;
  }>;
  category_distribution: Record<string, number>;
  recommendations: Array<{
    type: string;
    priority: string;
    suggestion: string;
    section?: string;
    current_accuracy?: number;
    example_instruction?: string;
  }>;
  trend: "improving" | "stable" | "declining";
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AnalyticsDashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<string | null>(null);
  const [managerInsights, setManagerInsights] = useState<ManagerInsights | null>(null);
  const [showManagerView, setShowManagerView] = useState(false);

  const orgId = process.env.NEXT_PUBLIC_DEV_ORG_ID || "default-org-id";

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch analytics summary
      const summaryRes = await fetch(
        `${API_URL}/api/v1/analytics/summary?org_id=${orgId}&days=30`
      );
      
      if (!summaryRes.ok) {
        throw new Error("Failed to fetch analytics");
      }
      
      const summaryData = await summaryRes.json();
      setAnalytics(summaryData);

      // Fetch action items
      const actionsRes = await fetch(
        `${API_URL}/api/v1/analytics/action-items?org_id=${orgId}&limit=10`
      );
      
      if (actionsRes.ok) {
        const actionsData = await actionsRes.json();
        setActionItems(actionsData.action_items || []);
      }

      // Fetch manager insights (feedback data)
      const insightsRes = await fetch(
        `${API_URL}/api/v1/feedback/manager-insights?org_id=${orgId}&days=30`
      );
      
      if (insightsRes.ok) {
        const insightsData = await insightsRes.json();
        setManagerInsights(insightsData);
      }
    } catch (err) {
      console.error("Analytics fetch error:", err);
      setError("Failed to load analytics data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleSimulateCall = async () => {
    setSimulating(true);
    setSimulationResult(null);

    try {
      // Create a mock audio blob (in production, this would be a real file)
      // For simulation, we'll call the upload endpoint with a test file
      const formData = new FormData();
      
      // Create a simple audio file placeholder
      const mockAudio = new Blob(
        [new ArrayBuffer(1000)],
        { type: "audio/mp3" }
      );
      formData.append("file", mockAudio, "simulated_call.mp3");
      formData.append("org_id", orgId);
      formData.append("user_id", "simulation-user");
      formData.append("client_name", "Simulated Client - Demo Corp");

      const response = await fetch(`${API_URL}/api/v1/meetings/upload`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setSimulationResult(`✅ Call simulated! Meeting ID: ${result.meeting_id}`);
        // Refresh analytics after simulation
        setTimeout(() => fetchAnalytics(), 2000);
      } else {
        const errorData = await response.json();
        setSimulationResult(`⚠️ Simulation failed: ${errorData.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Simulation error:", err);
      setSimulationResult("❌ Simulation failed: Network error");
    } finally {
      setSimulating(false);
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const formatCurrency = (value: number, currency: string = "ILS") => {
    if (currency === "ILS" || currency === "₪") {
      return `₪${value.toLocaleString()}`;
    }
    return `${currency} ${value.toLocaleString()}`;
  };

  const getSentimentColor = (score: number) => {
    if (score >= 0.7) return "text-emerald-500";
    if (score >= 0.4) return "text-amber-500";
    return "text-red-500";
  };

  const getMaxChartValue = (data: TimeSeriesPoint[]) => {
    if (!data || data.length === 0) return 1;
    return Math.max(...data.map((d) => d.value), 1);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-500">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <AlertTriangle className="h-12 w-12 text-amber-500" />
        <p className="text-lg text-gray-700">{error}</p>
        <Button onClick={fetchAnalytics} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Command Center</h1>
            <p className="text-sm text-gray-500">
              Last 30 days • Updated {analytics ? new Date(analytics.generated_at).toLocaleTimeString() : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={fetchAnalytics} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button 
            onClick={handleSimulateCall} 
            disabled={simulating}
            className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
          >
            {simulating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Simulating...
              </>
            ) : (
              <>
                <Phone className="h-4 w-4 mr-2" />
                Simulate Inbound Call
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Simulation Result */}
      {simulationResult && (
        <Card className={`${simulationResult.includes("✅") ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200"}`}>
          <CardContent className="py-3">
            <p className="text-sm font-medium">{simulationResult}</p>
          </CardContent>
        </Card>
      )}

      {/* Top Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Calls</p>
                <p className="text-3xl font-bold text-gray-900">
                  {analytics?.total_meetings || 0}
                </p>
              </div>
              <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                <Phone className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-2 flex items-center text-sm">
              <span className="text-emerald-600 font-medium">
                {analytics?.completed_meetings || 0}
              </span>
              <span className="text-gray-500 ml-1">completed</span>
              {analytics && analytics.pending_meetings > 0 && (
                <>
                  <span className="mx-2 text-gray-300">•</span>
                  <span className="text-amber-600">{analytics.pending_meetings} pending</span>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Talk Time</p>
                <p className="text-3xl font-bold text-gray-900">
                  {formatDuration(analytics?.total_duration_minutes || 0)}
                </p>
              </div>
              <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
                <Clock className="h-6 w-6 text-purple-600" />
              </div>
            </div>
            <div className="mt-2 text-sm text-gray-500">
              Avg: {formatDuration(analytics?.average_duration_minutes || 0)} per call
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Action Items</p>
                <p className="text-3xl font-bold text-gray-900">
                  {analytics?.action_items.total || 0}
                </p>
              </div>
              <div className="h-12 w-12 rounded-full bg-amber-100 flex items-center justify-center">
                <ListTodo className="h-6 w-6 text-amber-600" />
              </div>
            </div>
            <div className="mt-2 flex items-center text-sm">
              <span className="text-emerald-600 font-medium">
                {analytics?.action_items.high_confidence || 0}
              </span>
              <span className="text-gray-500 ml-1">high confidence</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
      <div>
                <p className="text-sm font-medium text-gray-500">Pipeline</p>
                <p className="text-3xl font-bold text-gray-900">
                  {formatCurrency(analytics?.deal_heat.total_pipeline_value || 0)}
                </p>
              </div>
              <div className="h-12 w-12 rounded-full bg-emerald-100 flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-emerald-600" />
              </div>
            </div>
            <div className="mt-2 flex items-center gap-2 text-sm">
              <span className="text-red-500 flex items-center">
                <Flame className="h-3 w-3 mr-1" />{analytics?.deal_heat.hot || 0}
              </span>
              <span className="text-amber-500 flex items-center">
                <Thermometer className="h-3 w-3 mr-1" />{analytics?.deal_heat.warm || 0}
              </span>
              <span className="text-blue-500 flex items-center">
                <Snowflake className="h-3 w-3 mr-1" />{analytics?.deal_heat.cold || 0}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Sentiment Gauge */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              Sentiment Gauge
            </CardTitle>
            <CardDescription>Call sentiment breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative pt-4">
              {/* Gauge visualization */}
              <div className="flex items-center justify-center mb-6">
                <div className="relative w-48 h-24 overflow-hidden">
                  {/* Background arc */}
                  <div 
                    className="absolute bottom-0 left-0 right-0 h-24 rounded-t-full border-[16px] border-gray-100"
                    style={{ borderBottomWidth: 0 }}
                  />
                  {/* Colored segments */}
                  <div className="absolute bottom-0 left-0 right-0 h-24">
                    <svg className="w-full h-full" viewBox="0 0 200 100">
                      {/* Red segment (negative) */}
                      <path
                        d="M 16 100 A 84 84 0 0 1 50 30"
                        fill="none"
                        stroke="#ef4444"
                        strokeWidth="16"
                        strokeLinecap="round"
                      />
                      {/* Yellow segment (neutral) */}
                      <path
                        d="M 50 30 A 84 84 0 0 1 150 30"
                        fill="none"
                        stroke="#f59e0b"
                        strokeWidth="16"
                      />
                      {/* Green segment (positive) */}
                      <path
                        d="M 150 30 A 84 84 0 0 1 184 100"
                        fill="none"
                        stroke="#10b981"
                        strokeWidth="16"
                        strokeLinecap="round"
                      />
                      {/* Needle */}
                      <line
                        x1="100"
                        y1="100"
                        x2={100 + 70 * Math.cos((Math.PI * (1 - (analytics?.sentiment.average_score || 0.5))))}
                        y2={100 - 70 * Math.sin((Math.PI * (1 - (analytics?.sentiment.average_score || 0.5))))}
                        stroke="#1f2937"
                        strokeWidth="3"
                        strokeLinecap="round"
                      />
                      <circle cx="100" cy="100" r="8" fill="#1f2937" />
                    </svg>
                  </div>
                </div>
              </div>
              
              {/* Score display */}
              <div className="text-center mb-6">
                <span className={`text-4xl font-bold ${getSentimentColor(analytics?.sentiment.average_score || 0.5)}`}>
                  {Math.round((analytics?.sentiment.average_score || 0.5) * 100)}%
                </span>
                <p className="text-sm text-gray-500 mt-1">Overall Positive</p>
              </div>

              {/* Breakdown */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-3 rounded-lg bg-emerald-50">
                  <p className="text-2xl font-bold text-emerald-600">
                    {analytics?.sentiment.positive || 0}
                  </p>
                  <p className="text-xs text-emerald-700">Positive</p>
                </div>
                <div className="p-3 rounded-lg bg-amber-50">
                  <p className="text-2xl font-bold text-amber-600">
                    {analytics?.sentiment.neutral || 0}
                  </p>
                  <p className="text-xs text-amber-700">Neutral</p>
                </div>
                <div className="p-3 rounded-lg bg-red-50">
                  <p className="text-2xl font-bold text-red-600">
                    {analytics?.sentiment.negative || 0}
                  </p>
                  <p className="text-xs text-red-700">Negative</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Trend Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              Call Volume Trend
            </CardTitle>
            <CardDescription>Calls processed per day (last 30 days)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {analytics?.meetings_by_day && analytics.meetings_by_day.length > 0 ? (
                <div className="flex items-end justify-between h-full gap-1">
                  {analytics.meetings_by_day.slice(-14).map((point, idx) => {
                    const maxVal = getMaxChartValue(analytics.meetings_by_day.slice(-14));
                    const height = (point.value / maxVal) * 100;
                    const date = new Date(point.date);
                    const isToday = new Date().toDateString() === date.toDateString();
                    
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center justify-end h-full">
                        <div
                          className={`w-full rounded-t transition-all duration-300 ${
                            isToday ? "bg-blue-600" : "bg-blue-400 hover:bg-blue-500"
                          }`}
                          style={{ height: `${Math.max(height, 4)}%` }}
                          title={`${point.date}: ${point.value} calls`}
                        />
                        <span className="text-[10px] text-gray-400 mt-2 rotate-45 origin-left">
                          {date.getDate()}/{date.getMonth() + 1}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-30" />
                    <p>No data available</p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Actions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <ListTodo className="h-5 w-5 text-amber-600" />
                Pending Actions
              </CardTitle>
              <CardDescription>Tasks requiring attention across all meetings</CardDescription>
            </div>
            <Badge variant="secondary" className="text-lg px-3 py-1">
              {actionItems.length} items
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {actionItems.length > 0 ? (
            <div className="space-y-3">
              {actionItems.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-4 p-4 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => router.push(`/dashboard/meetings/${item.meeting_id}`)}
                >
                  <div className="flex-shrink-0 mt-1">
                    <div className={`w-3 h-3 rounded-full ${
                      item.confidence >= 0.8 ? "bg-emerald-500" : 
                      item.confidence >= 0.5 ? "bg-amber-500" : "bg-gray-300"
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">{item.task}</p>
                    <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                      <span>{item.client_name || "Unknown client"}</span>
                      {item.due && (
                        <>
                          <span>•</span>
                          <span className="text-amber-600">Due: {item.due}</span>
                        </>
                      )}
                      {item.assignee && (
                        <>
                          <span>•</span>
                          <span>{item.assignee}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <Badge variant={item.confidence >= 0.8 ? "default" : "secondary"}>
                      {Math.round(item.confidence * 100)}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              <CheckCircle className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p className="text-lg font-medium">All caught up!</p>
              <p className="text-sm">No pending action items</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Deal Heat & Top Performers */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Deal Heat Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-5 w-5 text-red-500" />
              Deal Heat Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Hot */}
              <div className="flex items-center gap-4">
                <div className="w-20 flex items-center gap-2">
                  <Flame className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-medium">Hot</span>
                </div>
                <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-red-500 to-orange-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${analytics && analytics.total_meetings > 0
                        ? (analytics.deal_heat.hot / analytics.total_meetings) * 100
                        : 0}%`,
                    }}
                  />
                </div>
                <span className="w-12 text-right font-bold text-red-600">
                  {analytics?.deal_heat.hot || 0}
                </span>
              </div>

              {/* Warm */}
              <div className="flex items-center gap-4">
                <div className="w-20 flex items-center gap-2">
                  <Thermometer className="h-4 w-4 text-amber-500" />
                  <span className="text-sm font-medium">Warm</span>
                </div>
                <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-yellow-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${analytics && analytics.total_meetings > 0
                        ? (analytics.deal_heat.warm / analytics.total_meetings) * 100
                        : 0}%`,
                    }}
                  />
                </div>
                <span className="w-12 text-right font-bold text-amber-600">
                  {analytics?.deal_heat.warm || 0}
                </span>
              </div>

              {/* Cold */}
              <div className="flex items-center gap-4">
                <div className="w-20 flex items-center gap-2">
                  <Snowflake className="h-4 w-4 text-blue-500" />
                  <span className="text-sm font-medium">Cold</span>
                </div>
                <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${analytics && analytics.total_meetings > 0
                        ? (analytics.deal_heat.cold / analytics.total_meetings) * 100
                        : 0}%`,
                    }}
                  />
                </div>
                <span className="w-12 text-right font-bold text-blue-600">
                  {analytics?.deal_heat.cold || 0}
                </span>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Total Pipeline Value</span>
                <span className="text-2xl font-bold text-emerald-600">
                  {formatCurrency(analytics?.deal_heat.total_pipeline_value || 0)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Top Performers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-indigo-600" />
              Top Performers
            </CardTitle>
            <CardDescription>By meeting volume</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics?.top_users && analytics.top_users.length > 0 ? (
              <div className="space-y-4">
                {analytics.top_users.map((user, idx) => (
                  <div key={idx} className="flex items-center gap-4">
                    <div className={`
                      w-10 h-10 rounded-full flex items-center justify-center font-bold text-white
                      ${idx === 0 ? "bg-gradient-to-br from-amber-400 to-amber-600" :
                        idx === 1 ? "bg-gradient-to-br from-gray-400 to-gray-600" :
                        idx === 2 ? "bg-gradient-to-br from-orange-400 to-orange-600" :
                        "bg-gradient-to-br from-blue-400 to-blue-600"}
                    `}>
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">
                        User {user.user_id.slice(0, 8)}...
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatDuration(user.total_duration_minutes)} total
                      </p>
                    </div>
                    <Badge variant="secondary">
                      {user.meeting_count} calls
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <Users className="h-12 w-12 mx-auto mb-2 opacity-30" />
                <p>No user data available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* AI Confidence */}
      <Card>
        <CardContent className="py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Activity className="h-7 w-7 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Average AI Confidence</p>
                <p className="text-3xl font-bold text-gray-900">
                  {Math.round((analytics?.average_confidence || 0) * 100)}%
                </p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-amber-600">
                  {analytics?.requires_review_count || 0}
                </p>
                <p className="text-xs text-gray-500">Require Review</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-emerald-600">
                  {(analytics?.total_meetings || 0) - (analytics?.requires_review_count || 0)}
                </p>
                <p className="text-xs text-gray-500">Auto-approved</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Manager's View - Feedback Insights */}
      <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 via-white to-indigo-50">
        <CardHeader className="cursor-pointer" onClick={() => setShowManagerView(!showManagerView)}>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-purple-900">
              <Brain className="h-5 w-5" />
              Manager&apos;s View: AI Learning Insights
              <Badge className="bg-purple-600 ml-2">Feedback</Badge>
            </CardTitle>
            <Button variant="ghost" size="icon">
              {showManagerView ? (
                <EyeOff className="h-5 w-5 text-purple-600" />
              ) : (
                <Eye className="h-5 w-5 text-purple-600" />
              )}
            </Button>
          </div>
          <CardDescription>
            User feedback summary and recommendations for improving AI accuracy
          </CardDescription>
        </CardHeader>

        {showManagerView && (
          <CardContent className="space-y-6">
            {managerInsights ? (
              <>
                {/* Feedback Stats Row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-white border border-purple-100">
                    <p className="text-2xl font-bold text-purple-900">
                      {managerInsights.total_feedback}
                    </p>
                    <p className="text-xs text-purple-600">Total Feedback</p>
                  </div>
                  <div className="p-4 rounded-lg bg-white border border-purple-100">
                    <p className="text-2xl font-bold text-emerald-600">
                      {managerInsights.accuracy_rate}%
                    </p>
                    <p className="text-xs text-gray-600">Accuracy Rate</p>
                  </div>
                  <div className="p-4 rounded-lg bg-white border border-purple-100">
                    <div className="flex items-center gap-2">
                      {managerInsights.trend === "improving" && (
                        <TrendingUp className="h-5 w-5 text-emerald-600" />
                      )}
                      {managerInsights.trend === "declining" && (
                        <TrendingDown className="h-5 w-5 text-red-600" />
                      )}
                      {managerInsights.trend === "stable" && (
                        <Activity className="h-5 w-5 text-blue-600" />
                      )}
                      <span className="text-lg font-semibold capitalize">
                        {managerInsights.trend}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">Trend</p>
                  </div>
                  <div className="p-4 rounded-lg bg-white border border-purple-100">
                    <p className="text-2xl font-bold text-gray-900">
                      {managerInsights.total_meetings}
                    </p>
                    <p className="text-xs text-gray-600">Reviewed Meetings</p>
                  </div>
                </div>

                {/* Section Accuracy */}
                {Object.keys(managerInsights.section_accuracy).length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" />
                      Accuracy by Section
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(managerInsights.section_accuracy).map(([section, accuracy]) => (
                        <div key={section} className="flex items-center gap-3">
                          <span className="text-sm text-gray-600 w-32 capitalize">
                            {section.replace("_", " ")}
                          </span>
                          <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                accuracy >= 80
                                  ? "bg-emerald-500"
                                  : accuracy >= 60
                                  ? "bg-amber-500"
                                  : "bg-red-500"
                              }`}
                              style={{ width: `${accuracy}%` }}
                            />
                          </div>
                          <span className={`text-sm font-medium w-12 text-right ${
                            accuracy >= 80
                              ? "text-emerald-600"
                              : accuracy >= 60
                              ? "text-amber-600"
                              : "text-red-600"
                          }`}>
                            {accuracy}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Category Distribution */}
                {Object.keys(managerInsights.category_distribution).length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <ListTodo className="h-4 w-4" />
                      Feedback Categories
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(managerInsights.category_distribution).map(([category, count]) => (
                        <Badge
                          key={category}
                          variant="outline"
                          className="bg-purple-50 text-purple-700 border-purple-200"
                        >
                          {category.replace("_", " ")} ({count})
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {managerInsights.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <Lightbulb className="h-4 w-4 text-amber-500" />
                      AI Recommendations
                    </h4>
                    <div className="space-y-3">
                      {managerInsights.recommendations.map((rec, idx) => (
                        <div
                          key={idx}
                          className={`p-4 rounded-lg border ${
                            rec.priority === "high"
                              ? "bg-red-50 border-red-200"
                              : rec.priority === "medium"
                              ? "bg-amber-50 border-amber-200"
                              : "bg-emerald-50 border-emerald-200"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <Badge
                                  variant="outline"
                                  className={
                                    rec.priority === "high"
                                      ? "bg-red-100 text-red-700 border-red-300"
                                      : rec.priority === "medium"
                                      ? "bg-amber-100 text-amber-700 border-amber-300"
                                      : "bg-emerald-100 text-emerald-700 border-emerald-300"
                                  }
                                >
                                  {rec.priority} priority
                                </Badge>
                                {rec.section && (
                                  <span className="text-xs text-gray-500 capitalize">
                                    {rec.section}
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-800">{rec.suggestion}</p>
                              {rec.example_instruction && (
                                <div className="mt-2 p-2 bg-white/60 rounded border border-gray-200">
                                  <p className="text-xs text-gray-500 mb-1">Suggested instruction:</p>
                                  <code className="text-xs text-purple-700">
                                    {rec.example_instruction}
                                  </code>
                                </div>
                              )}
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => router.push("/dashboard/settings")}
                              className="shrink-0"
                            >
                              <Settings className="h-4 w-4 mr-1" />
                              Configure
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Common Issues */}
                {managerInsights.common_issues.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                      Recent Issues
                    </h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {managerInsights.common_issues.slice(0, 5).map((issue, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-white border border-gray-100 text-sm"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className="text-xs capitalize">
                              {issue.section}
                            </Badge>
                            <span className="text-xs text-gray-400">
                              {new Date(issue.date).toLocaleDateString()}
                            </span>
                          </div>
                          <p className="text-gray-700" dir="auto">{issue.note}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8">
                <Brain className="h-12 w-12 text-purple-200 mx-auto mb-3" />
                <p className="text-gray-500">No feedback data available yet</p>
                <p className="text-xs text-gray-400 mt-1">
                  User feedback will appear here once collected
                </p>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  );
}
