"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Agent } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.agents.list()
      .then((data: Agent[]) => {
        setAgents(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleAutoAssign = () => {
    api.agents.autoAssign().then(() => {
      api.agents.list().then((data: Agent[]) => setAgents(data));
    });
  };

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading agents...</div>;

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Delivery Agents</h1>
        <Button onClick={handleAutoAssign}>Auto-Assign All</Button>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => (
          <Card key={agent.id}>
            <CardHeader>
              <CardTitle className="text-lg">{agent.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
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
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
