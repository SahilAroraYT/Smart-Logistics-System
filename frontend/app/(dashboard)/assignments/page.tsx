"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { AssignmentSession } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

export default function AssignmentsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<AssignmentSession[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSessions = () => {
    api.assignments.list()
      .then((data: AssignmentSession[]) => {
        setSessions(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(loadSessions, []);

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    await api.assignments.delete(id);
    loadSessions();
  };

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading assignments...</div>;

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Assignments</h1>
          <p className="text-sm text-zinc-500">Batch assignment sessions for route generation</p>
        </div>
      </div>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Deliveries</TableHead>
                <TableHead>Agents</TableHead>
                <TableHead>Routes</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sessions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-zinc-500">
                    No assignments yet. Go to Deliveries and use "Assign to Route" to create one.
                  </TableCell>
                </TableRow>
              )}
              {sessions.map((s) => (
                <TableRow
                  key={s.id}
                  className="cursor-pointer hover:bg-zinc-50"
                  onClick={() => router.push(`/assignments/${s.id}`)}
                >
                  <TableCell className="font-medium">{s.name}</TableCell>
                  <TableCell>{new Date(s.date).toLocaleDateString()}</TableCell>
                  <TableCell>{s.delivery_count}</TableCell>
                  <TableCell>{s.agent_count}</TableCell>
                  <TableCell>{s.routes_count}</TableCell>
                  <TableCell>
                    <Badge variant={s.status === "completed" ? "default" : "secondary"}>
                      {s.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600"
                      onClick={(e) => handleDelete(s.id, e)}
                    >
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
