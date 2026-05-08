"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { AssignmentSessionDetail, AgentGroupInfo } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function AssignmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = Number(params.id);
  const [detail, setDetail] = useState<AssignmentSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const loadDetail = () => {
    api.assignments.get(sessionId)
      .then((data: AssignmentSessionDetail) => {
        setDetail(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(loadDetail, [sessionId]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.assignments.generateRoutes(sessionId);
      loadDetail();
    } catch (err) {
      alert((err as Error).message);
    }
    setGenerating(false);
  };

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading session...</div>;
  if (!detail) return <div className="p-8 text-center text-zinc-500">Session not found</div>;

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Button variant="ghost" size="sm" onClick={() => router.push("/assignments")} className="mb-2">
            &larr; Back
          </Button>
          <h1 className="text-2xl font-bold">{detail.name}</h1>
          <p className="text-sm text-zinc-500">
            {new Date(detail.date).toLocaleDateString()} &middot; {detail.deliveries.length} deliveries
            &middot; {detail.agents.length} agents &middot; {detail.routes.length} routes
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant={detail.status === "completed" ? "default" : "secondary"}>
            {detail.status}
          </Badge>
          {detail.status !== "completed" && (
            <Button onClick={handleGenerate} disabled={generating}>
              {generating ? "Generating..." : "Generate Routes"}
            </Button>
          )}
          <ManualAddDialog sessionId={sessionId} onAdded={loadDetail} />
        </div>
      </div>

      {/* Unassigned deliveries */}
      {detail.status !== "completed" && detail.deliveries.filter((d) => !d.agent_id).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Unassigned ({detail.deliveries.filter((d) => !d.agent_id).length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DeliveryTable
              deliveries={detail.deliveries.filter((d) => !d.agent_id)}
            />
          </CardContent>
        </Card>
      )}

      {/* Per-agent cards */}
      <div className="grid gap-4">
        {detail.agents.length === 0 && detail.status === "completed" && (
          <Card>
            <CardContent className="p-8 text-center text-zinc-500">
              No agents were assigned during this session. All deliveries may have been unassigned.
            </CardContent>
          </Card>
        )}
        {detail.agents.length === 0 && detail.status !== "completed" && (
          <Card>
            <CardContent className="p-8 text-center text-zinc-500">
              Click "Generate Routes" to assign deliveries to agents.
            </CardContent>
          </Card>
        )}
        {detail.agents.map((agent) => (
          <AgentCard key={agent.agent_id} agent={agent} sessionId={sessionId} />
        ))}
      </div>

      {/* Routes summary */}
      {detail.routes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All Routes in Session</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-zinc-500">
                  <th className="pb-2 font-medium">Route</th>
                  <th className="pb-2 font-medium">Agent</th>
                  <th className="pb-2 font-medium">Distance</th>
                  <th className="pb-2 font-medium">Avg Risk</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Map</th>
                </tr>
              </thead>
              <tbody>
                {detail.routes.map((r) => (
                  <tr key={r.id} className="border-b last:border-0">
                    <td className="py-2 font-medium">{r.name}</td>
                    <td className="py-2">{detail.agents.find((a) => a.agent_id === r.agent_id)?.agent_name || `Agent #${r.agent_id}`}</td>
                    <td className="py-2">{r.total_distance ? `${r.total_distance.toFixed(1)} km` : "-"}</td>
                    <td className="py-2">{r.total_risk_score ? r.total_risk_score.toFixed(1) : "-"}</td>
                    <td className="py-2"><Badge variant="outline">{r.status}</Badge></td>
                    <td className="py-2">
                      <Button variant="link" size="sm" onClick={() => router.push(`/map?route_id=${r.id}`)}>
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function AgentCard({ agent, sessionId }: { agent: AgentGroupInfo; sessionId: number }) {
  const router = useRouter();
  const riskColor = (cat: string | undefined) => {
    if (cat === "HIGH") return "text-red-600";
    if (cat === "MEDIUM") return "text-yellow-600";
    return "text-green-600";
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base flex items-center gap-2">
            {agent.agent_name}
            <Badge variant="outline" className="text-xs">{agent.vehicle_type || "N/A"}</Badge>
          </CardTitle>
          <p className="text-xs text-zinc-500">
            Load: {agent.current_load}/{agent.max_load} &middot; Success rate: {(agent.success_rate * 100).toFixed(0)}%
          </p>
        </div>
        <div className="flex gap-2">
          {agent.route && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push(`/map?route_id=${agent.route!.id}`)}
            >
              View Route on Map
            </Button>
          )}
          {!agent.route && (
            <span className="text-xs text-zinc-400 italic">No route generated</span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {agent.deliveries.length === 0 ? (
          <p className="text-sm text-zinc-400">No deliveries assigned</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-zinc-500">
                <th className="pb-1 font-medium">Order</th>
                <th className="pb-1 font-medium">Customer</th>
                <th className="pb-1 font-medium">Risk</th>
                <th className="pb-1 font-medium">Score</th>
                <th className="pb-1 font-medium">Zone</th>
              </tr>
            </thead>
            <tbody>
              {agent.deliveries.map((d) => (
                <tr key={d.id} className="border-b last:border-0">
                  <td className="py-1 font-medium">#{d.order_id || d.delivery_id}</td>
                  <td className="py-1">{d.customer_name || "-"}</td>
                  <td className={`py-1 font-medium ${riskColor(d.risk_category)}`}>
                    {d.risk_category || "-"}
                  </td>
                  <td className="py-1">{d.risk_score?.toFixed(1) ?? "-"}</td>
                  <td className="py-1">{d.delivery_zone || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}

function ManualAddDialog({ sessionId, onAdded }: { sessionId: number; onAdded: () => void }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [pincode, setPincode] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [useCoords, setUseCoords] = useState(false);
  const [weight, setWeight] = useState("1.0");
  const [adding, setAdding] = useState(false);

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
      await api.assignments.addManual(sessionId, payload as Parameters<typeof api.assignments.addManual>[1]);
      setName(""); setStreet(""); setCity(""); setPincode("");
      setLat(""); setLon(""); setUseCoords(false); setWeight("1.0");
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
        Add Order
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
            <Label>Package Weight (kg)</Label>
            <Input value={weight} onChange={(e) => setWeight(e.target.value)} placeholder="1.0" type="number" step="0.1" />
          </div>
          <p className="text-xs text-zinc-400">
            Address will be geocoded automatically if coordinates are not provided.
          </p>
          <Button onClick={handleSubmit} disabled={adding || !name}>
            {adding ? "Adding..." : "Add Delivery"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function DeliveryTable({ deliveries }: { deliveries: Array<{ order_id?: string; customer_name?: string; risk_category?: string; risk_score?: number; delivery_zone?: string; delivery_id: number }> }) {
  const riskColor = (cat: string | undefined) => {
    if (cat === "HIGH") return "text-red-600";
    if (cat === "MEDIUM") return "text-yellow-600";
    return "text-green-600";
  };
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b text-left text-zinc-500">
          <th className="pb-1 font-medium">Order</th>
          <th className="pb-1 font-medium">Customer</th>
          <th className="pb-1 font-medium">Risk</th>
          <th className="pb-1 font-medium">Score</th>
          <th className="pb-1 font-medium">Zone</th>
        </tr>
      </thead>
      <tbody>
        {deliveries.map((d) => (
          <tr key={d.delivery_id} className="border-b last:border-0">
            <td className="py-1 font-medium">#{d.order_id || d.delivery_id}</td>
            <td className="py-1">{d.customer_name || "-"}</td>
            <td className={`py-1 font-medium ${riskColor(d.risk_category)}`}>
              {d.risk_category || "-"}
            </td>
            <td className="py-1">{d.risk_score?.toFixed(1) ?? "-"}</td>
            <td className="py-1">{d.delivery_zone || "-"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
