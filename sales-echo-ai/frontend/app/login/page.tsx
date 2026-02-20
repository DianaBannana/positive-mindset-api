"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { createBrowserClient } from "@/lib/supabase";
import { LogIn, Loader2, AlertCircle, X } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [supabaseConfigured, setSupabaseConfigured] = useState(false);
  const [configError, setConfigError] = useState<string | null>(null);
  
  // Check if Supabase is configured on mount
  useEffect(() => {
    // Force check environment variables
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    
    // Detailed console logging
    console.log("=== SUPABASE CONFIGURATION CHECK ===");
    console.log("[Login Page] NEXT_PUBLIC_SUPABASE_URL:", supabaseUrl ? `✅ DEFINED (${supabaseUrl.substring(0, 30)}...)` : "❌ UNDEFINED");
    console.log("[Login Page] NEXT_PUBLIC_SUPABASE_ANON_KEY:", supabaseKey ? `✅ DEFINED (${supabaseKey.substring(0, 20)}...)` : "❌ UNDEFINED");
    console.log("[Login Page] All env vars:", Object.keys(process.env).filter(k => k.startsWith("NEXT_PUBLIC_")));
    console.log("====================================");
    
    if (!supabaseUrl || !supabaseKey) {
      const errorMsg = "CRITICAL: Supabase environment variables are missing. Check frontend/.env.local and restart the dev server.";
      console.error("[Login Page] Configuration error:", errorMsg);
      console.error("[Login Page] URL:", supabaseUrl || "MISSING");
      console.error("[Login Page] KEY:", supabaseKey ? "EXISTS" : "MISSING");
      setConfigError(errorMsg);
      setError(errorMsg);
    } else if (
      supabaseUrl === "your_supabase_project_url_here" || 
      supabaseKey === "your_supabase_anon_key_here" ||
      supabaseUrl.includes("your_") ||
      supabaseKey.includes("your_")
    ) {
      const errorMsg = "Supabase is not configured. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local";
      console.error("[Login Page] Placeholder values detected");
      setConfigError(errorMsg);
      setError(errorMsg);
    } else {
      console.log("[Login Page] ✅ Supabase is properly configured");
      setSupabaseConfigured(true);
      setConfigError(null);
      setError(null);
    }
  }, []);
  
  const handleSignIn = async (e: React.FormEvent<HTMLFormElement>) => {
    // CRITICAL: Prevent default form submission to avoid page reload
    e.preventDefault();
    e.stopPropagation();
    
    // Console logs for debugging
    console.log("[Login] Form submitted");
    console.log("[Login] Email:", email ? "provided" : "missing");
    console.log("[Login] Password:", password ? "provided" : "missing");
    console.log("[Login] Supabase configured:", supabaseConfigured);
    console.log("[Login] Config error:", configError);
    
    // Check configuration first - BLOCK if not configured
    if (!supabaseConfigured || configError) {
      const errorMsg = configError || "Supabase is not configured. Please check your .env.local file and restart the dev server.";
      console.error("[Login] Configuration check failed:", errorMsg);
      setError(errorMsg);
      setLoading(false);
      return;
    }
    
    // Validate inputs
    if (!email || !password) {
      const errorMsg = "Please enter both email and password";
      console.error("[Login] Validation failed:", errorMsg);
      setError(errorMsg);
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);

    // Create Supabase client fresh for each attempt
    const supabase = createBrowserClient();
    console.log("[Login] Supabase client created:", !!supabase);
    console.log("[Login] Supabase auth method exists:", typeof supabase?.auth?.signInWithPassword === "function");

    try {
      console.log("[Login] Calling supabase.auth.signInWithPassword...");
      console.log("[Login] Email:", email.trim());
      
      const result = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      console.log("[Login] Full response:", result);
      console.log("[Login] Response error:", result.error ? result.error.message : "none");
      console.log("[Login] Response data:", result.data ? "present" : "missing");
      console.log("[Login] User:", result.data?.user ? "present" : "missing");

      if (result.error) {
        console.error("[Login] Authentication error:", result.error);
        console.error("[Login] Error code:", result.error.status);
        console.error("[Login] Error message:", result.error.message);
        
        // Map common Supabase errors to user-friendly messages
        let errorMessage = "Failed to sign in";
        const errorMsg = result.error.message || "";
        
        if (errorMsg.includes("Invalid login credentials") || errorMsg.includes("invalid_credentials")) {
          errorMessage = "Invalid email or password. Please check your credentials and try again.";
        } else if (errorMsg.includes("Email not confirmed") || errorMsg.includes("email_not_confirmed")) {
          errorMessage = "Please verify your email address before signing in.";
        } else if (errorMsg.includes("Too many requests") || errorMsg.includes("too_many_requests")) {
          errorMessage = "Too many login attempts. Please wait a moment and try again.";
        } else if (errorMsg.includes("Supabase not configured")) {
          errorMessage = "Supabase is not configured. Check your .env.local file and restart the dev server.";
        } else {
          errorMessage = errorMsg || "Authentication failed. Please try again.";
        }
        
        console.error("[Login] Setting error message:", errorMessage);
        setError(errorMessage);
        setLoading(false);
        return;
      }

      if (!result.data?.user) {
        const errorMsg = "No user data returned from authentication";
        console.error("[Login]", errorMsg);
        setError(errorMsg);
        setLoading(false);
        return;
      }

      // Success - redirect using window.location.href for clean transition
      console.log("[Login] ✅ Login successful!");
      console.log("[Login] User ID:", result.data.user.id);
      console.log("[Login] Redirecting to dashboard...");
      
      // Small delay to ensure state updates are visible
      setTimeout(() => {
        window.location.href = "/dashboard";
      }, 100);
      
    } catch (err: any) {
      const errorMessage = err?.message || err?.toString() || "An unexpected error occurred. Please try again.";
      console.error("[Login] Exception caught:", err);
      console.error("[Login] Error type:", typeof err);
      console.error("[Login] Error message:", errorMessage);
      setError(errorMessage);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-xl p-8">
          {/* Logo/Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-blue-600 mb-2">
              SalesEcho AI
            </h1>
            <p className="text-gray-600">Sign in to your account</p>
          </div>

          {/* Configuration Error Banner (Critical) */}
          {configError && (
            <div className="mb-4 p-4 bg-red-100 border-2 border-red-500 rounded-md">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-red-800 mb-1">Configuration Error</p>
                  <p className="text-xs text-red-700">{configError}</p>
                </div>
                <button
                  onClick={() => {
                    setConfigError(null);
                    setError(null);
                  }}
                  className="text-red-600 hover:text-red-800"
                  aria-label="Dismiss"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* Login Error Message */}
          {error && !configError && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-800">Login Failed</p>
                  <p className="text-xs text-red-600 mt-1">{error}</p>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="text-red-600 hover:text-red-800"
                  aria-label="Dismiss"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* Login form */}
          <form onSubmit={handleSignIn} className="space-y-6">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="••••••••"
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loading || !supabaseConfigured || !!configError}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  <LogIn className="h-4 w-4 mr-2" />
                  Sign In
                </>
              )}
            </Button>
            {(!supabaseConfigured || configError) && (
              <p className="text-xs text-red-600 mt-2 text-center">
                Cannot sign in: Supabase is not configured
              </p>
            )}
          </form>

          {/* Demo note */}
          <div className="mt-6 p-4 bg-blue-50 rounded-md">
            <p className="text-xs text-blue-800">
              <strong>Note:</strong> This is a demo. Use your Supabase
              credentials to sign in.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
