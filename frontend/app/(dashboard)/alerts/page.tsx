"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Alert } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

const SEVERITY_COLORS: Record<string, "destructive" | "default" | "secondary"> = {
  critical: "destructive",
  high: "destructive",
  medium: "secondary",
  low: "default",
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.alerts.list()
      .then((data: Alert[]) => {
        setAlerts(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleAcknowledge = async (id: number) => {
    await api.alerts.acknowledge(id);
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_acknowledged: true } : a)));
  };

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading alerts...</div>;

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold">Alert Center</h1>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Message</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {alerts.map((a) => (
                <TableRow key={a.id}>
                  <TableCell className="font-medium">{a.alert_type}</TableCell>
                  <TableCell>
                    <Badge variant={SEVERITY_COLORS[a.severity] || "default"}>{a.severity}</Badge>
                  </TableCell>
                  <TableCell className="max-w-md truncate">{a.message}</TableCell>
                  <TableCell>
                    <Badge variant={a.is_acknowledged ? "default" : "destructive"}>
                      {a.is_acknowledged ? "Ack" : "Active"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-zinc-500">
                    {new Date(a.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    {!a.is_acknowledged && (
                      <Button variant="outline" size="sm" onClick={() => handleAcknowledge(a.id)}>
                        Acknowledge
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {alerts.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-zinc-500">No alerts</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
