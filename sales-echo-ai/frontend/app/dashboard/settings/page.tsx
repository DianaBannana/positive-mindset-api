"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Save,
  RefreshCw,
  Key,
  Copy,
  Check,
  Eye,
  EyeOff,
  Brain,
  Settings2,
  Mail,
  MessageSquare,
  Calendar,
  Database,
  Shield,
  AlertTriangle,
  Loader2,
  Sparkles,
  ToggleLeft,
  ToggleRight,
  Clock,
  Globe,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";

// Types
interface EnabledModules {
  email: boolean;
  whatsapp: boolean;
  calendar: boolean;
  crm: boolean;
}

interface OrganizationSettings {
  id: string;
  org_id: string;
  custom_prompt_instructions: string | null;
  enabled_modules: EnabledModules;
  industry_type: string | null;
  default_language: string;
  auto_dispatch_actions: boolean;
  require_approval: boolean;
  webhook_secret: string | null;
  callback_url: string | null;
  audio_retention_hours: number;
}

interface APIKey {
  id: string;
  key_prefix: string;
  name: string;
  permissions: string[];
  is_active: boolean;
  last_used_at: string | null;
  usage_count: number;
  created_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Default settings for new organizations
const DEFAULT_SETTINGS: Omit<OrganizationSettings, 'id' | 'org_id'> = {
  custom_prompt_instructions: null,
  enabled_modules: {
    email: true,
    whatsapp: true,
    calendar: true,
    crm: true,
  },
  industry_type: null,
  default_language: "he",
  auto_dispatch_actions: false,
  require_approval: true,
  webhook_secret: null,
  callback_url: null,
  audio_retention_hours: 24,
};

export default function SettingsPage() {
  const router = useRouter();
  const orgId = process.env.NEXT_PUBLIC_DEV_ORG_ID || "default-org-id";

  // State
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [settings, setSettings] = useState<OrganizationSettings | null>(null);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [showApiKey, setShowApiKey] = useState(false);
  const [keyCopied, setKeyCopied] = useState(false);
  const [regeneratingKey, setRegeneratingKey] = useState(false);

  // Form state (editable copy of settings)
  const [formData, setFormData] = useState({
    custom_prompt_instructions: "",
    enabled_modules: { ...DEFAULT_SETTINGS.enabled_modules },
    industry_type: "",
    default_language: "he",
    auto_dispatch_actions: false,
    require_approval: true,
    callback_url: "",
    audio_retention_hours: 24,
  });

  // Fetch settings
  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch org settings
      const settingsRes = await fetch(
        `${API_URL}/api/v1/settings?org_id=${orgId}`
      );
      
      if (settingsRes.ok) {
        const data = await settingsRes.json();
        setSettings(data);
        setFormData({
          custom_prompt_instructions: data.custom_prompt_instructions || "",
          enabled_modules: data.enabled_modules || DEFAULT_SETTINGS.enabled_modules,
          industry_type: data.industry_type || "",
          default_language: data.default_language || "he",
          auto_dispatch_actions: data.auto_dispatch_actions || false,
          require_approval: data.require_approval ?? true,
          callback_url: data.callback_url || "",
          audio_retention_hours: data.audio_retention_hours || 24,
        });
      } else if (settingsRes.status === 404) {
        // No settings yet, use defaults
        setSettings(null);
      } else {
        throw new Error("Failed to fetch settings");
      }

      // Fetch API keys
      const keysRes = await fetch(
        `${API_URL}/api/v1/settings/api-keys?org_id=${orgId}`
      );
      
      if (keysRes.ok) {
        const keysData = await keysRes.json();
        setApiKeys(keysData.keys || []);
      }
    } catch (err) {
      console.error("Settings fetch error:", err);
      setError("Failed to load settings. Using defaults.");
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // Save settings
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/settings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          org_id: orgId,
          ...formData,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save settings");
      }

      const data = await response.json();
      setSettings(data);
      setSuccess("Settings saved successfully!");
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error("Save error:", err);
      setError("Failed to save settings. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  // Toggle module
  const handleModuleToggle = (module: keyof EnabledModules) => {
    setFormData(prev => ({
      ...prev,
      enabled_modules: {
        ...prev.enabled_modules,
        [module]: !prev.enabled_modules[module],
      },
    }));
  };

  // Regenerate API key
  const handleRegenerateKey = async () => {
    if (!confirm("Are you sure? This will invalidate the current API key.")) {
      return;
    }

    setRegeneratingKey(true);
    
    try {
      const response = await fetch(`${API_URL}/api/v1/settings/api-keys/regenerate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          org_id: orgId,
          name: "Primary Integration Key",
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to regenerate key");
      }

      const data = await response.json();
      
      // Show the new key (only shown once!)
      alert(`New API Key (save it now!):\n\n${data.api_key}\n\nThis will not be shown again.`);
      
      // Refresh keys list
      await fetchSettings();
    } catch (err) {
      console.error("Key regeneration error:", err);
      setError("Failed to regenerate API key");
    } finally {
      setRegeneratingKey(false);
    }
  };

  // Copy API key prefix to clipboard
  const handleCopyKeyPrefix = async () => {
    if (apiKeys.length > 0) {
      await navigator.clipboard.writeText(apiKeys[0].key_prefix + "...");
      setKeyCopied(true);
      setTimeout(() => setKeyCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-500">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Organization Settings</h1>
            <p className="text-sm text-gray-500">Configure AI behavior and automations</p>
          </div>
        </div>
        <Button
          onClick={handleSave}
          disabled={saving}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
        >
          {saving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>

      {/* Alerts */}
      {error && (
        <Card className="bg-red-50 border-red-200">
          <CardContent className="py-3 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <p className="text-sm text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}
      
      {success && (
        <Card className="bg-emerald-50 border-emerald-200">
          <CardContent className="py-3 flex items-center gap-2">
            <Check className="h-5 w-5 text-emerald-600" />
            <p className="text-sm text-emerald-700">{success}</p>
          </CardContent>
        </Card>
      )}

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Custom Brain Config */}
        <Card className="lg:col-span-2 border-2 border-purple-200 bg-gradient-to-br from-purple-50 via-white to-indigo-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-purple-900">
              <Brain className="h-6 w-6" />
              Custom Brain Configuration
              <Badge className="bg-purple-600 ml-2">AI Training</Badge>
            </CardTitle>
            <CardDescription>
              Add custom instructions to guide the AI analysis. These instructions are injected
              into every summary generation for your organization.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="custom_prompt" className="text-purple-900 font-medium">
                Custom Analysis Instructions
              </Label>
              <p className="text-xs text-purple-700 mb-2">
                Examples: &ldquo;Focus on technical objections&rdquo;, &ldquo;Always extract budget timeline&rdquo;,
                &ldquo;Flag competitor mentions&rdquo;, &ldquo;For real estate, extract property details&rdquo;
              </p>
              <textarea
                id="custom_prompt"
                value={formData.custom_prompt_instructions}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  custom_prompt_instructions: e.target.value,
                }))}
                placeholder="Enter your custom instructions here...&#10;&#10;Example:&#10;- Focus on identifying budget constraints and timeline pressures&#10;- Always extract competitor mentions and objections&#10;- For enterprise deals, note the decision-making hierarchy&#10;- Flag any technical requirements or integration needs"
                className="w-full h-40 p-4 text-sm rounded-lg border border-purple-200 bg-white resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="industry_type" className="text-purple-900 font-medium">
                  Industry Type
                </Label>
                <select
                  id="industry_type"
                  value={formData.industry_type}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    industry_type: e.target.value,
                  }))}
                  className="w-full mt-1 p-2 text-sm rounded-lg border border-purple-200 bg-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Select industry...</option>
                  <option value="saas">SaaS / Software</option>
                  <option value="real_estate">Real Estate</option>
                  <option value="consulting">Consulting / Services</option>
                  <option value="ecommerce">E-commerce / Retail</option>
                  <option value="finance">Finance / Insurance</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="manufacturing">Manufacturing</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <Label htmlFor="default_language" className="text-purple-900 font-medium">
                  Default Language
                </Label>
                <select
                  id="default_language"
                  value={formData.default_language}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    default_language: e.target.value,
                  }))}
                  className="w-full mt-1 p-2 text-sm rounded-lg border border-purple-200 bg-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="he">Hebrew (עברית)</option>
                  <option value="en">English</option>
                  <option value="he-en">Bilingual (Hebrew + English)</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Module Toggles */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings2 className="h-5 w-5 text-blue-600" />
              Automation Modules
            </CardTitle>
            <CardDescription>
              Enable or disable specific automation features
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Email Module */}
            <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "h-10 w-10 rounded-lg flex items-center justify-center",
                  formData.enabled_modules.email ? "bg-blue-100" : "bg-gray-100"
                )}>
                  <Mail className={cn(
                    "h-5 w-5",
                    formData.enabled_modules.email ? "text-blue-600" : "text-gray-400"
                  )} />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Email Drafts</p>
                  <p className="text-xs text-gray-500">Generate follow-up emails</p>
                </div>
              </div>
              <Switch
                checked={formData.enabled_modules.email}
                onCheckedChange={() => handleModuleToggle("email")}
              />
            </div>

            {/* WhatsApp Module */}
            <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "h-10 w-10 rounded-lg flex items-center justify-center",
                  formData.enabled_modules.whatsapp ? "bg-green-100" : "bg-gray-100"
                )}>
                  <MessageSquare className={cn(
                    "h-5 w-5",
                    formData.enabled_modules.whatsapp ? "text-green-600" : "text-gray-400"
                  )} />
                </div>
                <div>
                  <p className="font-medium text-gray-900">WhatsApp Messages</p>
                  <p className="text-xs text-gray-500">Generate summary messages</p>
                </div>
              </div>
              <Switch
                checked={formData.enabled_modules.whatsapp}
                onCheckedChange={() => handleModuleToggle("whatsapp")}
              />
            </div>

            {/* Calendar Module */}
            <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "h-10 w-10 rounded-lg flex items-center justify-center",
                  formData.enabled_modules.calendar ? "bg-purple-100" : "bg-gray-100"
                )}>
                  <Calendar className={cn(
                    "h-5 w-5",
                    formData.enabled_modules.calendar ? "text-purple-600" : "text-gray-400"
                  )} />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Calendar Events</p>
                  <p className="text-xs text-gray-500">Extract meeting dates</p>
                </div>
              </div>
              <Switch
                checked={formData.enabled_modules.calendar}
                onCheckedChange={() => handleModuleToggle("calendar")}
              />
            </div>

            {/* CRM Module */}
            <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "h-10 w-10 rounded-lg flex items-center justify-center",
                  formData.enabled_modules.crm ? "bg-orange-100" : "bg-gray-100"
                )}>
                  <Database className={cn(
                    "h-5 w-5",
                    formData.enabled_modules.crm ? "text-orange-600" : "text-gray-400"
                  )} />
                </div>
                <div>
                  <p className="font-medium text-gray-900">CRM Sync</p>
                  <p className="text-xs text-gray-500">Push data to CRM</p>
                </div>
              </div>
              <Switch
                checked={formData.enabled_modules.crm}
                onCheckedChange={() => handleModuleToggle("crm")}
              />
            </div>
          </CardContent>
        </Card>

        {/* Automation Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-amber-600" />
              Automation Controls
            </CardTitle>
            <CardDescription>
              Configure how actions are processed
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Auto Dispatch */}
            <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "h-10 w-10 rounded-lg flex items-center justify-center",
                  formData.auto_dispatch_actions ? "bg-emerald-100" : "bg-gray-100"
                )}>
                  <Sparkles className={cn(
                    "h-5 w-5",
                    formData.auto_dispatch_actions ? "text-emerald-600" : "text-gray-400"
                  )} />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Auto-Dispatch Actions</p>
                  <p className="text-xs text-gray-500">Automatically execute detected actions</p>
                </div>
              </div>
              <Switch
                checked={formData.auto_dispatch_actions}
                onCheckedChange={(checked) => setFormData(prev => ({
                  ...prev,
                  auto_dispatch_actions: checked,
                }))}
              />
            </div>

            {/* Require Approval */}
            <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "h-10 w-10 rounded-lg flex items-center justify-center",
                  formData.require_approval ? "bg-amber-100" : "bg-gray-100"
                )}>
                  <Shield className={cn(
                    "h-5 w-5",
                    formData.require_approval ? "text-amber-600" : "text-gray-400"
                  )} />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Require Approval</p>
                  <p className="text-xs text-gray-500">Human approval before sending</p>
                </div>
              </div>
              <Switch
                checked={formData.require_approval}
                onCheckedChange={(checked) => setFormData(prev => ({
                  ...prev,
                  require_approval: checked,
                }))}
              />
            </div>

            {/* Audio Retention */}
            <div className="p-4 rounded-lg border border-gray-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-10 w-10 rounded-lg bg-gray-100 flex items-center justify-center">
                  <Clock className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Audio Retention</p>
                  <p className="text-xs text-gray-500">Hours to keep audio files</p>
                </div>
              </div>
              <Input
                type="number"
                min={1}
                max={720}
                value={formData.audio_retention_hours}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  audio_retention_hours: parseInt(e.target.value) || 24,
                }))}
                className="w-32"
              />
            </div>

            {/* Callback URL */}
            <div className="p-4 rounded-lg border border-gray-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-10 w-10 rounded-lg bg-gray-100 flex items-center justify-center">
                  <Globe className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Callback URL</p>
                  <p className="text-xs text-gray-500">POST results to this URL</p>
                </div>
              </div>
              <Input
                type="url"
                placeholder="https://your-system.com/webhook/salesecho"
                value={formData.callback_url}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  callback_url: e.target.value,
                }))}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* API Key Management */}
      <Card className="border-2 border-amber-200 bg-gradient-to-br from-amber-50 via-white to-orange-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-amber-900">
            <Key className="h-5 w-5" />
            API Key Management
            <Badge className="bg-amber-600 ml-2">Security</Badge>
          </CardTitle>
          <CardDescription>
            Use this key to authenticate webhook requests from external systems
          </CardDescription>
        </CardHeader>
        <CardContent>
          {apiKeys.length > 0 ? (
            <div className="space-y-4">
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg border border-amber-200 bg-white"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-900">{key.name}</p>
                      <Badge variant={key.is_active ? "default" : "secondary"}>
                        {key.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <code className="text-sm bg-gray-100 px-3 py-1 rounded font-mono">
                        {showApiKey ? key.key_prefix + "••••••••••••••••••••" : "••••••••••••••••••••••••"}
                      </code>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setShowApiKey(!showApiKey)}
                      >
                        {showApiKey ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleCopyKeyPrefix}
                      >
                        {keyCopied ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span>Used: {key.usage_count} times</span>
                      {key.last_used_at && (
                        <span>Last: {new Date(key.last_used_at).toLocaleDateString()}</span>
                      )}
                      <span>Created: {new Date(key.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleRegenerateKey}
                    disabled={regeneratingKey}
                    className="border-amber-300 text-amber-700 hover:bg-amber-50"
                  >
                    {regeneratingKey ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Regenerating...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Regenerate
                      </>
                    )}
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Key className="h-12 w-12 text-amber-300 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No API keys configured</p>
              <Button
                onClick={handleRegenerateKey}
                disabled={regeneratingKey}
                className="bg-amber-600 hover:bg-amber-700"
              >
                {regeneratingKey ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Key className="h-4 w-4 mr-2" />
                    Generate API Key
                  </>
                )}
              </Button>
            </div>
          )}

          <div className="mt-6 p-4 rounded-lg bg-amber-100/50 border border-amber-200">
            <h4 className="font-medium text-amber-900 mb-2">Usage Example</h4>
            <code className="text-xs bg-amber-50 p-3 rounded block overflow-x-auto whitespace-pre">
{`curl -X POST https://api.salesecho.ai/api/v1/ingest/webhook \\
  -H "X-API-Key: ${apiKeys[0]?.key_prefix || 'sk_live_'}••••••••" \\
  -H "X-Org-ID: ${orgId}" \\
  -F "recording_url=https://pbx.example.com/call.mp3"`}
            </code>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
