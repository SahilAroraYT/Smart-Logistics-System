"use client";

import { AuthProvider } from "@/lib/auth";
import { AuthGuard } from "@/components/layout/AuthGuard";
import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AuthGuard>
        <div className="min-h-screen bg-zinc-50">
          <Sidebar />
          <main className="ml-64 min-h-screen">{children}</main>
        </div>
      </AuthGuard>
    </AuthProvider>
  );
}
