"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Warehouse } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Pencil, Trash2 } from "lucide-react";

export default function WarehousesPage() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.warehouses.list()
      .then(setWarehouses)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this warehouse?")) return;
    try {
      await api.warehouses.delete(id);
      load();
    } catch (err) {
      alert((err as Error).message);
    }
  };

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading warehouses...</div>;

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Warehouses</h1>
        <AddWarehouseDialog onAdded={load} />
      </div>
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Coordinates</TableHead>
                <TableHead>City</TableHead>
                <TableHead>Pincode</TableHead>
                <TableHead className="w-32 text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {warehouses.map((w) => (
                <TableRow key={w.id}>
                  <TableCell className="font-medium">{w.name}</TableCell>
                  <TableCell>{w.street || "-"}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{w.lat.toFixed(4)}, {w.lon.toFixed(4)}</Badge>
                  </TableCell>
                  <TableCell>{w.city || "-"}</TableCell>
                  <TableCell>{w.pincode || "-"}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <EditWarehouseDialog warehouse={w} onSaved={load} />
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => handleDelete(w.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {warehouses.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-zinc-400 py-8">
                    No warehouses yet
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function WarehouseForm({
  initial,
  onSave,
  saving,
}: {
  initial?: Warehouse;
  onSave: (data: { name: string; street?: string; city?: string; pincode?: string; lat: number; lon: number }) => Promise<void>;
  saving: boolean;
}) {
  const [name, setName] = useState(initial?.name || "");
  const [street, setStreet] = useState(initial?.street || "");
  const [city, setCity] = useState(initial?.city || "");
  const [pincode, setPincode] = useState(initial?.pincode || "");
  const [lat, setLat] = useState(initial?.lat.toString() || "");
  const [lon, setLon] = useState(initial?.lon.toString() || "");

  const handleSubmit = async () => {
    if (!name || !lat || !lon) return;
    await onSave({
      name,
      street: street || undefined,
      city: city || undefined,
      pincode: pincode || undefined,
      lat: parseFloat(lat),
      lon: parseFloat(lon),
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <Label>Name *</Label>
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Delhi North Hub" />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label>Street</Label>
          <Input value={street} onChange={(e) => setStreet(e.target.value)} placeholder="GT Karnal Road" />
        </div>
        <div>
          <Label>City</Label>
          <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Delhi" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label>Pincode</Label>
          <Input value={pincode} onChange={(e) => setPincode(e.target.value)} placeholder="110033" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label>Latitude *</Label>
          <Input value={lat} onChange={(e) => setLat(e.target.value)} placeholder="28.72" type="number" step="0.0001" />
        </div>
        <div>
          <Label>Longitude *</Label>
          <Input value={lon} onChange={(e) => setLon(e.target.value)} placeholder="77.12" type="number" step="0.0001" />
        </div>
      </div>
      <Button onClick={handleSubmit} disabled={saving || !name || !lat || !lon} className="w-full">
        {saving ? "Saving..." : initial ? "Update Warehouse" : "Create Warehouse"}
      </Button>
    </div>
  );
}

function AddWarehouseDialog({ onAdded }: { onAdded: () => void }) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSave = async (data: { name: string; street?: string; city?: string; pincode?: string; lat: number; lon: number }) => {
    setSaving(true);
    try {
      await api.warehouses.create(data);
      setOpen(false);
      onAdded();
    } catch (err) {
      alert((err as Error).message);
    }
    setSaving(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button><Plus className="h-4 w-4 mr-1" />Add Warehouse</Button>} />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Warehouse</DialogTitle>
        </DialogHeader>
        <WarehouseForm onSave={handleSave} saving={saving} />
      </DialogContent>
    </Dialog>
  );
}

function EditWarehouseDialog({ warehouse, onSaved }: { warehouse: Warehouse; onSaved: () => void }) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSave = async (data: { name: string; street?: string; city?: string; pincode?: string; lat: number; lon: number }) => {
    setSaving(true);
    try {
      await api.warehouses.update(warehouse.id, data);
      setOpen(false);
      onSaved();
    } catch (err) {
      alert((err as Error).message);
    }
    setSaving(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="ghost" size="icon-sm"><Pencil className="h-4 w-4" /></Button>} />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Warehouse</DialogTitle>
        </DialogHeader>
        <WarehouseForm initial={warehouse} onSave={handleSave} saving={saving} />
      </DialogContent>
    </Dialog>
  );
}
