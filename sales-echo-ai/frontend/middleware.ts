import { createMiddlewareClient } from "@supabase/auth-helpers-nextjs";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for route protection and session management
 * 
 * This runs on the Edge Runtime and uses createMiddlewareClient
 * which is designed for middleware context.
 */
export async function middleware(req: NextRequest) {
  const res = NextResponse.next();
  
  // Diagnostics: Check if environment variables are defined
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  console.log("[Middleware] NEXT_PUBLIC_SUPABASE_URL:", supabaseUrl ? "defined" : "undefined");
  console.log("[Middleware] NEXT_PUBLIC_SUPABASE_ANON_KEY:", supabaseKey ? "defined" : "undefined");
  
  // If Supabase is not configured, allow all routes (graceful degradation)
  if (!supabaseUrl || !supabaseKey) {
    console.warn("[Middleware] Supabase not configured. Allowing all routes.");
    return res;
  }
  
  try {
    // Create Supabase client for middleware (Edge Runtime compatible)
    const supabase = createMiddlewareClient({ req, res });
    
    // Refresh session if expired
    const {
      data: { session },
    } = await supabase.auth.getSession();

    // Protect dashboard routes
    if (req.nextUrl.pathname.startsWith("/dashboard")) {
      if (!session) {
        return NextResponse.redirect(new URL("/login", req.url));
      }
    }

    // Redirect authenticated users away from login
    if (req.nextUrl.pathname === "/login" && session) {
      return NextResponse.redirect(new URL("/dashboard", req.url));
    }
  } catch (error) {
    // If Supabase is not configured or fails, allow access for debugging
    // In production, you may want to be more strict here
    console.warn("Middleware auth check failed:", error);
    
    // Still protect dashboard routes even if Supabase fails
    // Uncomment the line below to enable strict protection:
    // if (req.nextUrl.pathname.startsWith("/dashboard")) {
    //   return NextResponse.redirect(new URL("/login", req.url));
    // }
  }

  return res;
}

export const config = {
  matcher: ["/dashboard/:path*", "/login"],
};
