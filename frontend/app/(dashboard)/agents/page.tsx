"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Agent, Warehouse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger,
} from "@/components/ui/select";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      api.agents.list(),
      api.warehouses.list(),
    ])
      .then(([agentsData, warehousesData]) => {
        setAgents(agentsData);
        setWarehouses(warehousesData);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(load, []);

  const handleWarehouseChange = async (agentId: number, warehouseId: string) => {
    const whId = warehouseId ? parseInt(warehouseId) : null;
    try {
      const updated = await api.agents.update(agentId, { warehouse_id: whId || null });
      setAgents((prev) => prev.map((a) => (a.id === agentId ? updated : a)));
    } catch (err) {
      alert((err as Error).message);
    }
  };

  const handleAutoAssign = () => {
    api.agents.autoAssign().then(() => load());
  };

  const warehouseMap = Object.fromEntries(warehouses.map((w) => [w.id, w]));

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading agents...</div>;

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Delivery Agents</h1>
        <Button onClick={handleAutoAssign}>Auto-Assign All</Button>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => {
          const wh = agent.warehouse_id ? warehouseMap[agent.warehouse_id] : null;
          return (
            <Card key={agent.id}>
              <CardHeader>
                <CardTitle className="text-lg">{agent.name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Status</span>
                  <Badge variant={agent.is_available ? "default" : "secondary"}>
                    {agent.status || "offline"}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Load</span>
                  <span>{agent.current_load} / {agent.max_load}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Success Rate</span>
                  <span>{(agent.success_rate * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Vehicle</span>
                  <span>{agent.vehicle_type || "N/A"}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-zinc-500 text-xs">Warehouse</span>
                  <Select
                    key={`agent-${agent.id}-wh-${warehouses.length}`}
                    value={agent.warehouse_id?.toString() || ""}
                    onValueChange={(v) => handleWarehouseChange(agent.id, v ?? "")}
                  >
                    <SelectTrigger className="w-full h-7 text-xs">
                      <span>{wh?.name || "Not assigned"}</span>
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">Not assigned</SelectItem>
                      {warehouses.map((w) => (
                        <SelectItem key={w.id} value={w.id.toString()}>
                          {w.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
