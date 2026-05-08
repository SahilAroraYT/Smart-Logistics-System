"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Delivery } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

const RISK_BADGE: Record<string, { variant: "default" | "secondary" | "destructive"; label: string }> = {
  LOW: { variant: "default", label: "LOW" },
  MEDIUM: { variant: "secondary", label: "MEDIUM" },
  HIGH: { variant: "destructive", label: "HIGH" },
};

export default function DeliveriesPage() {
  const router = useRouter();
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params: Record<string, string> = { page: "1", page_size: "100" };
    if (filter !== "all") params.status = filter;
    api.deliveries.list(params)
      .then((data: { deliveries: Delivery[] }) => {
        setDeliveries(data.deliveries);
        setSelected(new Set());
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [filter]);

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === deliveries.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(deliveries.filter((d) => d.status === "pending").map((d) => d.id)));
    }
  };

  const handleAssignToRoute = async () => {
    const ids = Array.from(selected);
    if (ids.length === 0) return;
    try {
      const session = await api.assignments.create({ delivery_ids: ids });
      router.push(`/assignments/${session.id}`);
    } catch (err) {
      alert((err as Error).message);
    }
  };

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading deliveries...</div>;

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Deliveries</h1>
        <div className="flex items-center gap-3">
          {selected.size > 0 && (
            <span className="text-sm text-zinc-500">{selected.size} selected</span>
          )}
          <Button
            onClick={handleAssignToRoute}
            disabled={selected.size === 0}
            size="sm"
          >
            Assign to Route
          </Button>
          <Select value={filter} onValueChange={(v) => setFilter(v ?? "all")}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="assigned">Assigned</SelectItem>
              <SelectItem value="in_transit">In Transit</SelectItem>
              <SelectItem value="delivered">Delivered</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Checkbox
                    checked={selected.size === deliveries.filter((d) => d.status === "pending").length && deliveries.length > 0}
                    onCheckedChange={toggleAll}
                  />
                </TableHead>
                <TableHead>Order ID</TableHead>
                <TableHead>Zone</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Weather</TableHead>
                <TableHead>Traffic</TableHead>
                <TableHead>Distance</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {deliveries.map((d) => {
                const riskInfo = d.risk_category ? RISK_BADGE[d.risk_category] : null;
                const isPending = d.status === "pending";
                return (
                  <TableRow key={d.id} className={selected.has(d.id) ? "bg-zinc-50" : ""}>
                    <TableCell>
                      <Checkbox
                        checked={selected.has(d.id)}
                        onCheckedChange={() => toggleSelect(d.id)}
                        disabled={!isPending}
                      />
                    </TableCell>
                    <TableCell className="font-medium">#{d.order_id}</TableCell>
                    <TableCell>{d.delivery_zone || "-"}</TableCell>
                    <TableCell>
                      {riskInfo ? <Badge variant={riskInfo.variant}>{riskInfo.label}</Badge> : "-"}
                    </TableCell>
                    <TableCell>{d.risk_score ? d.risk_score.toFixed(1) : "-"}</TableCell>
                    <TableCell><Badge variant="outline">{d.status || "N/A"}</Badge></TableCell>
                    <TableCell>{d.weather || "-"}</TableCell>
                    <TableCell>{d.traffic_level || "-"}</TableCell>
                    <TableCell>{d.distance_km ? `${d.distance_km.toFixed(1)} km` : "-"}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
