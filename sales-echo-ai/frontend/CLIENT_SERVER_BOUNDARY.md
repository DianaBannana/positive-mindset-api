# Client/Server Boundary Guide

## Overview

This project uses Next.js App Router which has strict client/server boundaries. Supabase clients must be created differently for client and server contexts.

## File Structure

### Client-Side (`lib/supabase.ts`)
- **Use in**: Client Components (files with `"use client"`)
- **Exports**: `createBrowserClient()`, `createClient()` (legacy)
- **Does NOT use**: `cookies()` or any server-only APIs
- **Safe to import in**: Any client component

### Server-Side (`lib/supabase-server.ts`)
- **Use in**: Server Components, Server Actions, Route Handlers
- **Exports**: `createServerClient()`
- **Uses**: `cookies()` from `next/headers` (server-only)
- **DO NOT import in**: Client components (will cause build errors)

### Middleware (`middleware.ts`)
- **Uses**: `createMiddlewareClient()` from `@supabase/auth-helpers-nextjs`
- **Purpose**: Edge Runtime compatible client for route protection
- **Runs on**: Edge Runtime (not Node.js or Browser)

## Usage Examples

### Client Component (Login Page)
```tsx
"use client"

import { createBrowserClient } from "@/lib/supabase"

export default function LoginPage() {
  const supabase = createBrowserClient()
  
  const handleSignIn = async () => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
  }
}
```

### Server Component (Dashboard Layout)
```tsx
// NO "use client" directive

import { createServerClient } from "@/lib/supabase-server"

export default async function DashboardLayout() {
  const supabase = createServerClient()
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    redirect("/login")
  }
  
  return <div>...</div>
}
```

### Middleware
```tsx
import { createMiddlewareClient } from "@supabase/auth-helpers-nextjs"

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })
  const { data: { session } } = await supabase.auth.getSession()
  
  // Protect routes
  if (!session && req.nextUrl.pathname.startsWith("/dashboard")) {
    return NextResponse.redirect(new URL("/login", req.url))
  }
  
  return res
}
```

## Common Errors

### Error: "cookies() can only be used in Server Components"
**Cause**: Importing `lib/supabase-server.ts` in a client component
**Fix**: Use `createBrowserClient()` from `lib/supabase.ts` instead

### Error: "use client" directive required
**Cause**: Using hooks or browser APIs in a server component
**Fix**: Add `"use client"` directive at the top of the file

### Error: Cannot use cookies() in middleware
**Cause**: Middleware runs on Edge Runtime, not Node.js
**Fix**: Use `createMiddlewareClient()` instead of `createServerClient()`

## Migration Checklist

- ✅ `lib/supabase.ts` - Client-only, no server imports
- ✅ `lib/supabase-server.ts` - Server-only, uses cookies()
- ✅ `app/login/page.tsx` - Uses `createBrowserClient()`
- ✅ `components/Sidebar.tsx` - Uses `createBrowserClient()`
- ✅ `app/dashboard/layout.tsx` - Uses `createServerClient()`
- ✅ `app/dashboard/page.tsx` - Uses `createServerClient()`
- ✅ `middleware.ts` - Uses `createMiddlewareClient()`

## Best Practices

1. **Always check the file type**:
   - Client Component → `createBrowserClient()`
   - Server Component → `createServerClient()`
   - Middleware → `createMiddlewareClient()`

2. **Never import server utilities in client files**:
   - ❌ `import { createServerClient } from "@/lib/supabase-server"` in a `"use client"` file
   - ✅ `import { createBrowserClient } from "@/lib/supabase"` in a `"use client"` file

3. **Use TypeScript to catch errors**:
   - TypeScript will warn if you try to use server-only APIs in client code
   - Pay attention to these warnings during development

4. **Test both environments**:
   - Client components: Test in browser DevTools
   - Server components: Check server logs and build output
