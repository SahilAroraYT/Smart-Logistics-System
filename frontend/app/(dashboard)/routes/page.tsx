"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Route } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

export default function RoutesPage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.routes.list()
      .then((data: Route[]) => {
        setRoutes(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleGenerate = () => {
    api.routes.generate({ max_deliveries: 20 })
      .then(() => api.routes.list().then((data: Route[]) => setRoutes(data)))
      .catch((err: Error) => alert(err.message));
  };

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading routes...</div>;

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Routes</h1>
        <Button onClick={handleGenerate}>Generate Route</Button>
      </div>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Agent ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Distance</TableHead>
                <TableHead>Avg Risk</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {routes.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.name}</TableCell>
                  <TableCell>{r.agent_id}</TableCell>
                  <TableCell><Badge variant="outline">{r.status}</Badge></TableCell>
                  <TableCell>{r.total_distance ? `${r.total_distance.toFixed(1)} km` : "-"}</TableCell>
                  <TableCell>{r.total_risk_score ? r.total_risk_score.toFixed(1) : "-"}</TableCell>
                  <TableCell>{new Date(r.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
              {routes.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-zinc-500">No routes yet. Click Generate to create one.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
