"use client";

import { AuthGuard } from "@/components/layout/AuthGuard";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, Truck } from "lucide-react";
import { api } from "@/lib/api";
import type { Agent } from "@/types";

function AgentBar() {
  const { user, logout } = useAuth();
  const [agent, setAgent] = useState<Agent | null>(null);
  const router = useRouter();

  useEffect(() => {
    api.agent.me().then(setAgent).catch(() => {});
  }, []);

  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-4 shadow-sm">
      <div className="flex items-center gap-3">
        <Truck className="h-5 w-5 text-blue-600" />
        <span className="font-semibold text-zinc-800">
          {agent?.name || user?.full_name || "Agent"}
        </span>
        {agent?.vehicle_type && (
          <span className="hidden rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 sm:inline-block">
            {agent.vehicle_type}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-zinc-400">
          {agent?.current_load ?? 0}/{agent?.max_load ?? 0} load
        </span>
        <button
          onClick={() => { logout(); router.push("/login"); }}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-zinc-500 transition-colors hover:bg-red-50 hover:text-red-600"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  );
}

export default function AgentLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user && user.role !== "delivery_agent") {
      router.replace("/dashboard");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-zinc-300 border-t-zinc-900" />
      </div>
    );
  }

  if (!user || user.role !== "delivery_agent") return null;

  return (
    <AuthGuard>
      <div className="flex h-screen flex-col">
        <AgentBar />
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </AuthGuard>
  );
}
