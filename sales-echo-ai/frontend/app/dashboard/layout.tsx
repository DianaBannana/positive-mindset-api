import { createServerClient } from "@/lib/supabase-server";
import { Sidebar } from "@/components/Sidebar";
import { redirect } from "next/navigation";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Temporarily allow dashboard access for debugging
  // TODO: Re-enable auth check once Supabase is configured
  let session = null;
  let isAdmin = false;
  
  try {
    const supabase = createServerClient();
    const {
      data: { session: userSession },
    } = await supabase.auth.getSession();
    session = userSession;
    
    // Check if user is admin (you can customize this logic)
    isAdmin = session?.user?.email?.endsWith("@admin.salesecho.ai") || false;
    
    // Only redirect if Supabase is properly configured and no session
    // For now, allow access for debugging
    // if (!session) {
    //   redirect("/login");
    // }
  } catch (error) {
    // If Supabase is not configured, allow access for debugging
    console.warn("Supabase auth check failed, allowing access for debugging:", error);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar isAdmin={isAdmin} />
      <main className="lg:pl-64 min-h-screen">
        <div className="p-4 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
