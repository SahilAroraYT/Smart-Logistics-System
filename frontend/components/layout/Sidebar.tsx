"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Map as MapIcon, Package, Users, Route,
  Bell, ScrollText, ClipboardList, Warehouse, LogOut,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/map", label: "Map View", icon: MapIcon },
  { href: "/deliveries", label: "Deliveries", icon: Package },
  { href: "/warehouses", label: "Warehouses", icon: Warehouse },
  { href: "/agents", label: "Agents", icon: Users },
  { href: "/assignments", label: "Assignments", icon: ClipboardList },
  { href: "/routes", label: "Routes", icon: Route },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/audit", label: "Audit Log", icon: ScrollText },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-zinc-900 text-white">
      <div className="flex h-16 items-center border-b border-zinc-800 px-6">
        <h1 className="text-lg font-bold">Smart Logistics</h1>
      </div>
      <nav className="flex flex-col gap-1 p-4">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                active ? "bg-zinc-800 text-white" : "text-zinc-400 hover:bg-zinc-800 hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="absolute bottom-0 left-0 right-0 border-t border-zinc-800 p-4">
        <div className="mb-3 text-xs text-zinc-500">
          {user?.full_name} · {user?.role}
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
