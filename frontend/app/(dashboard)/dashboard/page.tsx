"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Package, AlertTriangle, TrendingUp, Users, CheckCircle, XCircle, Bell as BellIcon,
} from "lucide-react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend,
} from "recharts";

const RISK_COLORS = { LOW: "#22c55e", MEDIUM: "#f59e0b", HIGH: "#ef4444" };

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total: 0, pending: 0, delivered: 0, failed: 0,
    avgRisk: 0, activeAlerts: 0,
  });
  const [riskData, setRiskData] = useState<{ name: string; value: number; color: string }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.deliveries.list({ page: 1, page_size: 1000 }),
      api.alerts.list({ acknowledged: false }),
    ]).then(([deliveries, alerts]) => {
      const dels = (deliveries as { deliveries: Array<{ status: string; risk_score?: number; risk_category?: string }> }).deliveries;
      const pending = dels.filter((d) => d.status === "pending").length;
      const delivered = dels.filter((d) => d.status === "delivered").length;
      const failed = dels.filter((d) => d.status === "failed").length;
      const avgRisk = dels.length ? dels.reduce((s, d) => s + (d.risk_score || 0), 0) / dels.length : 0;

      const riskMap: Record<string, number> = { LOW: 0, MEDIUM: 0, HIGH: 0 };
      dels.forEach((d) => {
        if (d.risk_category && riskMap[d.risk_category] !== undefined) riskMap[d.risk_category]++;
      });
      setRiskData([
        { name: "Low", value: riskMap.LOW, color: RISK_COLORS.LOW },
        { name: "Medium", value: riskMap.MEDIUM, color: RISK_COLORS.MEDIUM },
        { name: "High", value: riskMap.HIGH, color: RISK_COLORS.HIGH },
      ]);

      setStats({
        total: dels.length, pending, delivered, failed,
        avgRisk: Math.round(avgRisk),
        activeAlerts: (alerts as Array<unknown>).length,
      });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading dashboard...</div>;

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold">Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Package} label="Total Deliveries" value={stats.total} />
        <StatCard icon={TrendingUp} label="Pending" value={stats.pending} color="text-yellow-500" />
        <StatCard icon={CheckCircle} label="Delivered" value={stats.delivered} color="text-green-500" />
        <StatCard icon={XCircle} label="Failed" value={stats.failed} color="text-red-500" />
        <StatCard icon={AlertTriangle} label="Avg Risk Score" value={stats.avgRisk} />
        <StatCard icon={BellIcon} label="Active Alerts" value={stats.activeAlerts} color="text-red-500" />
      </div>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Risk Distribution</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {riskData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Delivery Status</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { name: "Pending", value: stats.pending, fill: "#f59e0b" },
                { name: "Delivered", value: stats.delivered, fill: "#22c55e" },
                { name: "Failed", value: stats.failed, fill: "#ef4444" },
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color = "text-zinc-900" }: { icon: React.ComponentType<{ className?: string }>; label: string; value: number; color?: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-6">
        <Icon className={`h-8 w-8 ${color}`} />
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm text-zinc-500">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}
