"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  TrendingUp,
  Target,
  Clock,
  Activity,
  Users,
  DollarSign,
  Flame,
  Thermometer,
  Snowflake,
  RefreshCw,
  Loader2,
  Calendar,
  BarChart3,
  PieChart,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { SalesExcellenceData } from "@/lib/types";
import { getOrgId, getApiUrl } from "@/lib/org";

const API_URL = getApiUrl();

export default function SalesExcellencePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SalesExcellenceData | null>(null);
  const [period, setPeriod] = useState(30);

  const orgId = getOrgId();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/manager/excellence?org_id=${orgId}&days=${period}`
      );

      if (response.ok) {
        const result = await response.json();
        setData(result);
      } else {
        setError("Failed to load metrics");
      }
    } catch (err) {
      console.error("Excellence fetch error:", err);
      setError("Connection error");
    } finally {
      setLoading(false);
    }
  }, [orgId, period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("he-IL", {
      style: "currency",
      currency: "ILS",
      minimumFractionDigits: 0,
    }).format(value);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin text-indigo-600 mx-auto" />
          <p className="mt-4 text-gray-500">Loading Sales Excellence metrics...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.push("/dashboard")} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Dashboard
        </Button>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-12 text-center text-red-700">{error}</CardContent>
        </Card>
      </div>
    );
  }

  const { pipeline, conversion, cycle, activity } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.push("/dashboard")} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Dashboard
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Target className="h-6 w-6 text-indigo-600" />
              Sales Excellence
            </h1>
            <p className="text-sm text-gray-500">Manager&apos;s performance dashboard</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            {[7, 30, 90].map((days) => (
              <Button
                key={days}
                variant={period === days ? "default" : "ghost"}
                size="sm"
                onClick={() => setPeriod(days)}
                className={cn("h-7", period === days && "bg-indigo-600")}
              >
                {days}d
              </Button>
            ))}
          </div>
          <Button variant="outline" onClick={fetchData} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Top KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pipeline Value */}
        <Card className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white border-0">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-emerald-100 text-sm">Pipeline Value</p>
                <p className="text-3xl font-bold mt-1">{formatCurrency(pipeline.total_value)}</p>
              </div>
              <DollarSign className="h-10 w-10 text-emerald-200" />
            </div>
          </CardContent>
        </Card>

        {/* Win Rate */}
        <Card className="bg-gradient-to-br from-purple-500 to-indigo-600 text-white border-0">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm">Win Rate</p>
                <p className="text-3xl font-bold mt-1">{conversion.win_rate}%</p>
              </div>
              <TrendingUp className="h-10 w-10 text-purple-200" />
            </div>
          </CardContent>
        </Card>

        {/* Cycle Length */}
        <Card className="bg-gradient-to-br from-amber-500 to-orange-600 text-white border-0">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-amber-100 text-sm">Avg Cycle</p>
                <p className="text-3xl font-bold mt-1">{cycle.avg_days_to_hot}d</p>
                <p className="text-xs text-amber-200 mt-1">{cycle.avg_meetings_to_hot} meetings</p>
              </div>
              <Clock className="h-10 w-10 text-amber-200" />
            </div>
          </CardContent>
        </Card>

        {/* Total Activity */}
        <Card className="bg-gradient-to-br from-blue-500 to-cyan-600 text-white border-0">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Total Meetings</p>
                <p className="text-3xl font-bold mt-1">{conversion.total_meetings}</p>
              </div>
              <Activity className="h-10 w-10 text-blue-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Conversion Funnel & Deal Heat */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Conversion Funnel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5 text-purple-600" />
              Conversion Funnel
            </CardTitle>
            <CardDescription>Deal progression through stages</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(conversion.conversion_funnel).map(([stage, count], idx) => {
              const maxCount = Math.max(...Object.values(conversion.conversion_funnel));
              const percent = (count / maxCount) * 100;
              const labels: Record<string, string> = {
                all_meetings: "All Meetings",
                with_deal_value: "With Deal Value",
                warm_or_hot: "Warm/Hot",
                hot: "Hot Deals",
              };

              return (
                <div key={stage} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">{labels[stage] || stage}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                  <Progress
                    value={percent}
                    className={cn(
                      "h-3",
                      idx === 0
                        ? "[&>div]:bg-blue-500"
                        : idx === 1
                        ? "[&>div]:bg-amber-500"
                        : idx === 2
                        ? "[&>div]:bg-orange-500"
                        : "[&>div]:bg-red-500"
                    )}
                  />
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Deal Heat Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-5 w-5 text-red-500" />
              Deal Heat Distribution
            </CardTitle>
            <CardDescription>Current deal temperature breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              {/* Hot */}
              <div className="text-center p-4 rounded-xl bg-gradient-to-br from-red-50 to-orange-50 border border-red-100">
                <Flame className="h-8 w-8 text-red-500 mx-auto" />
                <p className="text-3xl font-bold text-red-600 mt-2">{conversion.hot_deals}</p>
                <p className="text-sm text-red-700">Hot</p>
              </div>

              {/* Warm */}
              <div className="text-center p-4 rounded-xl bg-gradient-to-br from-amber-50 to-yellow-50 border border-amber-100">
                <Thermometer className="h-8 w-8 text-amber-500 mx-auto" />
                <p className="text-3xl font-bold text-amber-600 mt-2">{conversion.warm_deals}</p>
                <p className="text-sm text-amber-700">Warm</p>
              </div>

              {/* Cold */}
              <div className="text-center p-4 rounded-xl bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-100">
                <Snowflake className="h-8 w-8 text-blue-500 mx-auto" />
                <p className="text-3xl font-bold text-blue-600 mt-2">{conversion.cold_deals}</p>
                <p className="text-sm text-blue-700">Cold</p>
              </div>
            </div>

            {/* Win Rate Bar */}
            <div className="mt-6 pt-6 border-t">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Hot Deal Rate</span>
                <span className="text-sm font-semibold text-red-600">{conversion.win_rate}%</span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 rounded-full transition-all"
                  style={{ width: `${conversion.win_rate}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline by Rep & Activity */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top Performers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-indigo-600" />
              Top Performers
            </CardTitle>
            <CardDescription>Pipeline value by sales rep</CardDescription>
          </CardHeader>
          <CardContent>
            {pipeline.by_rep.length > 0 ? (
              <div className="space-y-3">
                {pipeline.by_rep.slice(0, 5).map((rep, idx) => {
                  const maxValue = pipeline.by_rep[0]?.value || 1;
                  const percent = (rep.value / maxValue) * 100;

                  return (
                    <div key={rep.name} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div
                            className={cn(
                              "h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold text-white",
                              idx === 0
                                ? "bg-gradient-to-br from-amber-400 to-amber-600"
                                : idx === 1
                                ? "bg-gradient-to-br from-gray-400 to-gray-600"
                                : idx === 2
                                ? "bg-gradient-to-br from-orange-400 to-orange-600"
                                : "bg-gradient-to-br from-blue-400 to-blue-600"
                            )}
                          >
                            {idx + 1}
                          </div>
                          <span className="font-medium text-gray-900">{rep.name}</span>
                        </div>
                        <span className="text-sm font-semibold text-emerald-600">
                          {formatCurrency(rep.value)}
                        </span>
                      </div>
                      <Progress value={percent} className="h-2 [&>div]:bg-indigo-500" />
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No pipeline data yet</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Activity Heatmap Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-cyan-600" />
              Activity Patterns
            </CardTitle>
            <CardDescription>When your team is most active</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="p-4 rounded-xl bg-gradient-to-br from-cyan-50 to-blue-50 border border-cyan-100 text-center">
                <Calendar className="h-6 w-6 text-cyan-600 mx-auto" />
                <p className="text-lg font-bold text-cyan-900 mt-2">{activity.peak_day}</p>
                <p className="text-xs text-cyan-700">Peak Day</p>
              </div>
              <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-100 text-center">
                <Clock className="h-6 w-6 text-indigo-600 mx-auto" />
                <p className="text-lg font-bold text-indigo-900 mt-2">
                  {activity.peak_hour}:00
                </p>
                <p className="text-xs text-indigo-700">Peak Hour</p>
              </div>
            </div>

            {/* Activity by Day */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">Activity by Day</p>
              {["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"].map((day) => {
                const count = activity.by_day[day] || 0;
                const maxCount = Math.max(...Object.values(activity.by_day));
                const percent = maxCount > 0 ? (count / maxCount) * 100 : 0;

                return (
                  <div key={day} className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 w-12">{day.slice(0, 3)}</span>
                    <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-600 w-8">{count}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Trend */}
      {pipeline.trend.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-600" />
              Pipeline Trend
            </CardTitle>
            <CardDescription>Daily pipeline value over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-40 flex items-end gap-1">
              {pipeline.trend.map((point, idx) => {
                const maxValue = Math.max(...pipeline.trend.map((p) => p.value));
                const heightPercent = maxValue > 0 ? (point.value / maxValue) * 100 : 0;

                return (
                  <div
                    key={point.date}
                    className="flex-1 bg-gradient-to-t from-emerald-400 to-teal-500 rounded-t transition-all hover:from-emerald-500 hover:to-teal-600"
                    style={{ height: `${Math.max(heightPercent, 2)}%` }}
                    title={`${point.date}: ${formatCurrency(point.value)}`}
                  />
                );
              })}
            </div>
            <div className="flex justify-between mt-2 text-xs text-gray-500">
              <span>{pipeline.trend[0]?.date}</span>
              <span>{pipeline.trend[pipeline.trend.length - 1]?.date}</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
