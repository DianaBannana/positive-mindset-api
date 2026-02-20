"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Users,
  Search,
  Phone,
  Mail,
  Building2,
  TrendingUp,
  TrendingDown,
  Activity,
  Calendar,
  ChevronRight,
  Plus,
  RefreshCw,
  Loader2,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Client, ClientListResponse, ClientStatsOverview, RelationshipStage } from "@/lib/types";
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

export default function ClientsDirectoryPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [totalClients, setTotalClients] = useState(0);
  const [stats, setStats] = useState<ClientStatsOverview | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  const orgId = getOrgId();

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const fetchClients = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Build query params
      const params = new URLSearchParams({ org_id: orgId });
      if (debouncedSearch) {
        params.append("search", debouncedSearch);
      }

      const response = await fetch(`${API_URL}/api/v1/clients?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error("Failed to fetch clients");
      }

      const data: ClientListResponse = await response.json();
      setClients(data.clients);
      setTotalClients(data.total);

    } catch (err) {
      console.error("Client fetch error:", err);
      setError("Failed to load clients");
    } finally {
      setLoading(false);
    }
  }, [orgId, debouncedSearch]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/clients/stats/overview?org_id=${orgId}`);
      
      if (response.ok) {
        const data: ClientStatsOverview = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Stats fetch error:", err);
    }
  }, [orgId]);

  useEffect(() => {
    fetchClients();
    fetchStats();
  }, [fetchClients, fetchStats]);

  const handleBack = () => {
    router.push("/dashboard");
  };

  const handleClientClick = (clientId: string) => {
    router.push(`/dashboard/clients/${clientId}`);
  };

  const getSentimentIcon = (score: number | null) => {
    if (score === null) return <Activity className="h-4 w-4 text-gray-400" />;
    if (score > 0.3) return <TrendingUp className="h-4 w-4 text-emerald-500" />;
    if (score < -0.3) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Activity className="h-4 w-4 text-amber-500" />;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    return date.toLocaleDateString("he-IL", { day: "numeric", month: "short", year: "numeric" });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={handleBack} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Dashboard
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Users className="h-6 w-6 text-indigo-600" />
              Client Directory
            </h1>
            <p className="text-sm text-gray-500">
              {totalClients} clients in your network
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => { fetchClients(); fetchStats(); }} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button className="gap-2 bg-indigo-600 hover:bg-indigo-700">
            <Plus className="h-4 w-4" />
            Add Client
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {(Object.entries(stats.by_stage) as [RelationshipStage, number][]).map(([stage, count]) => (
            <Card key={stage} className={cn("border-2", stageColors[stage].replace("bg-", "border-").split(" ")[0])}>
              <CardContent className="pt-4 pb-3 text-center">
                <p className="text-2xl font-bold text-gray-900">{count}</p>
                <p className="text-xs text-gray-500 capitalize">{stageLabels[stage]}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Search by name, phone, email, or company..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Loading/Error States */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      )}

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-6 text-center text-red-700">
            {error}
          </CardContent>
        </Card>
      )}

      {/* Client List */}
      {!loading && !error && (
        <div className="space-y-3">
          {clients.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Users className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">
                  {debouncedSearch ? "No clients match your search" : "No clients yet"}
                </p>
                {!debouncedSearch && (
                  <p className="text-sm text-gray-400 mt-1">
                    Clients are automatically created when calls are ingested with phone numbers
                  </p>
                )}
              </CardContent>
            </Card>
          ) : (
            clients.map((client) => (
              <Card
                key={client.id}
                className="hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer"
                onClick={() => handleClientClick(client.id)}
              >
                <CardContent className="py-4">
                  <div className="flex items-center justify-between gap-4">
                    {/* Client Info */}
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                      {/* Avatar */}
                      <div className="h-12 w-12 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-semibold shrink-0">
                        {client.full_name 
                          ? client.full_name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()
                          : <User className="h-6 w-6" />
                        }
                      </div>
                      
                      {/* Details */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-semibold text-gray-900 truncate">
                            {client.full_name || client.company_name || client.phone}
                          </h3>
                          <Badge variant="outline" className={cn("text-xs", stageColors[client.relationship_stage])}>
                            {stageLabels[client.relationship_stage]}
                          </Badge>
                        </div>
                        
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-500 flex-wrap">
                          {client.phone && (
                            <span className="flex items-center gap-1">
                              <Phone className="h-3 w-3" />
                              {client.phone}
                            </span>
                          )}
                          {client.email && (
                            <span className="flex items-center gap-1">
                              <Mail className="h-3 w-3" />
                              {client.email}
                            </span>
                          )}
                          {client.company_name && client.full_name && (
                            <span className="flex items-center gap-1">
                              <Building2 className="h-3 w-3" />
                              {client.company_name}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-6 text-sm">
                      <div className="text-center hidden sm:block">
                        <p className="font-semibold text-gray-900">{client.total_meetings}</p>
                        <p className="text-xs text-gray-500">Meetings</p>
                      </div>
                      
                      <div className="flex items-center gap-1 hidden md:flex">
                        {getSentimentIcon(client.avg_sentiment_score)}
                        <span className="text-xs text-gray-500">
                          {client.avg_sentiment_score !== null 
                            ? (client.avg_sentiment_score > 0 ? "Positive" : client.avg_sentiment_score < 0 ? "Negative" : "Neutral")
                            : "No data"
                          }
                        </span>
                      </div>

                      <div className="text-center hidden lg:block">
                        <div className="flex items-center gap-1 text-gray-500">
                          <Calendar className="h-3 w-3" />
                          <span className="text-xs">{formatDate(client.last_contact_at)}</span>
                        </div>
                        <p className="text-xs text-gray-400">Last contact</p>
                      </div>

                      <ChevronRight className="h-5 w-5 text-gray-400" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Top Performers */}
      {stats && stats.top_clients && stats.top_clients.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-600" />
              Most Active Clients
            </CardTitle>
            <CardDescription>Clients with the most meetings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {stats.top_clients.map((client, idx) => (
                <div
                  key={client.id}
                  className="p-3 rounded-lg border border-gray-200 hover:border-indigo-300 cursor-pointer transition-colors"
                  onClick={() => handleClientClick(client.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "h-8 w-8 rounded-full flex items-center justify-center font-bold text-white text-sm",
                      idx === 0 ? "bg-gradient-to-br from-amber-400 to-amber-600" :
                      idx === 1 ? "bg-gradient-to-br from-gray-400 to-gray-600" :
                      idx === 2 ? "bg-gradient-to-br from-orange-400 to-orange-600" :
                      "bg-gradient-to-br from-blue-400 to-blue-600"
                    )}>
                      {idx + 1}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-900 truncate text-sm">
                        {client.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {client.total_meetings} meetings
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
