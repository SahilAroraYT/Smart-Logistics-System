"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AuditLog } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.audit.list()
      .then((data: AuditLog[]) => {
        setLogs(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading audit logs...</div>;

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold">Audit Log</h1>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Entity ID</TableHead>
                <TableHead>User</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm">{new Date(log.timestamp).toLocaleString()}</TableCell>
                  <TableCell><Badge variant="outline">{log.action_type}</Badge></TableCell>
                  <TableCell>{log.entity_type || "-"}</TableCell>
                  <TableCell>{log.entity_id || "-"}</TableCell>
                  <TableCell>{log.user_id ? `User #${log.user_id}` : "System"}</TableCell>
                </TableRow>
              ))}
              {logs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-zinc-500">No audit logs</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
