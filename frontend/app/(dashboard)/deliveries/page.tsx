"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Delivery, AssignmentSession } from "@/types";
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
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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
          <AddManualOrderDialog onAdded={() => {
            const params: Record<string, string> = { page: "1", page_size: "100" };
            if (filter !== "all") params.status = filter;
            api.deliveries.list(params).then((data: { deliveries: Delivery[] }) => {
              setDeliveries(data.deliveries);
            });
          }} />
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
                <TableHead>Weight</TableHead>
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
                    <TableCell>{d.package_weight ? `${d.package_weight} kg` : "-"}</TableCell>
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

function AddManualOrderDialog({ onAdded }: { onAdded: () => void }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [pincode, setPincode] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [useCoords, setUseCoords] = useState(false);
  const [weight, setWeight] = useState("1.0");
  const [sessionId, setSessionId] = useState<string>("");
  const [sessions, setSessions] = useState<AssignmentSession[]>([]);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (open) {
      api.assignments.list().then(setSessions).catch(() => {});
    }
  }, [open]);

  const handleSubmit = async () => {
    if (!name) return;
    setAdding(true);
    try {
      const payload: Record<string, unknown> = {
        customer_name: name,
        delivery_street: street || undefined,
        delivery_city: city || undefined,
        delivery_pincode: pincode || undefined,
        package_weight: parseFloat(weight),
      };
      if (useCoords && lat && lon) {
        payload.customer_lat = parseFloat(lat);
        payload.customer_lon = parseFloat(lon);
      }
      if (sessionId) {
        payload.session_id = parseInt(sessionId);
      }
      await api.deliveries.addManual(payload as Parameters<typeof api.deliveries.addManual>[0]);
      setName(""); setStreet(""); setCity(""); setPincode("");
      setLat(""); setLon(""); setUseCoords(false); setWeight("1.0"); setSessionId("");
      setOpen(false);
      onAdded();
    } catch (err) {
      alert((err as Error).message);
    }
    setAdding(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="outline" />}>
        Add Manual Order
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Manual Order</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Customer Name *</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="John Doe" />
          </div>
          <div>
            <Label>Street / Area</Label>
            <Input value={street} onChange={(e) => setStreet(e.target.value)} placeholder="123 Main St" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label>City</Label>
              <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="New Delhi" />
            </div>
            <div>
              <Label>Pincode</Label>
              <Input value={pincode} onChange={(e) => setPincode(e.target.value)} placeholder="110001" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="useCoords"
              checked={useCoords}
              onChange={(e) => setUseCoords(e.target.checked)}
              className="h-4 w-4 rounded border-zinc-300"
            />
            <Label htmlFor="useCoords" className="text-sm text-zinc-500">Specify coordinates manually (optional)</Label>
          </div>
          {useCoords && (
            <div className="grid grid-cols-2 gap-2 pl-6 border-l-2 border-zinc-200">
              <div>
                <Label>Latitude</Label>
                <Input value={lat} onChange={(e) => setLat(e.target.value)} placeholder="28.65" />
              </div>
              <div>
                <Label>Longitude</Label>
                <Input value={lon} onChange={(e) => setLon(e.target.value)} placeholder="77.15" />
              </div>
            </div>
          )}
          <div>
            <Label>Session (optional)</Label>
            <select
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">No session (standalone)</option>
              {sessions.filter((s) => s.status !== "completed").map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.delivery_count} deliveries)
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Package Weight (kg)</Label>
            <Input value={weight} onChange={(e) => setWeight(e.target.value)} placeholder="1.0" type="number" step="0.1" />
          </div>
          <p className="text-xs text-zinc-400">
            Address will be geocoded automatically. If attached to a session, the order will be available for route generation.
          </p>
          <Button onClick={handleSubmit} disabled={adding || !name}>
            {adding ? "Adding..." : "Add Delivery"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
