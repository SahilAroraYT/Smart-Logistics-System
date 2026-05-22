"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { L } from "@/lib/leaflet";
import type { AgentDashboardData, Delivery } from "@/types";
import "leaflet/dist/leaflet.css";
import { CheckCircle, MapPin, Package, AlertCircle } from "lucide-react";

const MapContainer = dynamic(() => import("react-leaflet").then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then((m) => m.TileLayer), { ssr: false });
const Marker = dynamic(() => import("react-leaflet").then((m) => m.Marker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then((m) => m.Popup), { ssr: false });
const Polyline = dynamic(() => import("react-leaflet").then((m) => m.Polyline), { ssr: false });

const RISK_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#f59e0b",
  HIGH: "#ef4444",
};

function RiskIcon(color: string) {
  return L.divIcon({
    className: "custom-marker",
    html: `<div style="background:${color};width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3)"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

function LoadingState() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-zinc-300 border-t-blue-600" />
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <AlertCircle className="h-10 w-10 text-red-400" />
      <p className="text-zinc-600">{message}</p>
      <button
        onClick={onRetry}
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
      >
        Retry
      </button>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <MapPin className="h-10 w-10 text-zinc-300" />
      <p className="text-lg font-medium text-zinc-600">No route assigned</p>
      <p className="text-sm text-zinc-400">Check with your supervisor for assignments.</p>
    </div>
  );
}

function AllCompletedState() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <CheckCircle className="h-10 w-10 text-green-400" />
      <p className="text-lg font-medium text-zinc-600">All deliveries completed!</p>
      <p className="text-sm text-zinc-400">Great job. Check back later for new assignments.</p>
    </div>
  );
}

function DeliveryCard({
  delivery,
  completing,
  onComplete,
}: {
  delivery: Delivery;
  completing: boolean;
  onComplete: () => void;
}) {
  const riskColor = delivery.risk_category
    ? RISK_COLORS[delivery.risk_category] || "#888"
    : "#888";

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm transition-shadow hover:shadow-md">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-zinc-800">
            {delivery.order_id || `Order #${delivery.id}`}
          </p>
          <p className="text-sm text-zinc-500">{delivery.customer_name || "Unknown"}</p>
        </div>
        {delivery.risk_category && (
          <span
            className="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
            style={{ backgroundColor: riskColor }}
          >
            {delivery.risk_category}
          </span>
        )}
      </div>
      {delivery.delivery_street && (
        <p className="mb-3 truncate text-xs text-zinc-400">
          <MapPin className="mr-1 inline h-3 w-3" />
          {delivery.delivery_street}
          {delivery.delivery_city && `, ${delivery.delivery_city}`}
        </p>
      )}
      <div className="mb-3 flex items-center justify-between gap-2 text-xs text-zinc-400">
        {delivery.package_weight && (
          <span><Package className="mr-1 inline h-3 w-3" />{delivery.package_weight} kg</span>
        )}
        {delivery.distance_km && <span>{delivery.distance_km.toFixed(1)} km</span>}
      </div>
      <button
        onClick={onComplete}
        disabled={completing}
        className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {completing ? (
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
        ) : (
          <CheckCircle className="h-4 w-4" />
        )}
        {completing ? "Completing..." : "Mark Completed"}
      </button>
    </div>
  );
}

export default function AgentDashboardPage() {
  const [data, setData] = useState<AgentDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completing, setCompleting] = useState<Record<number, boolean>>({});
  const [center, setCenter] = useState<[number, number]>([28.65, 77.1]);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.agent.dashboard();
      setData(result);
      if (result.deliveries.length > 0) {
        const first = result.deliveries[0];
        if (first.customer_lat && first.customer_lon) {
          setCenter([first.customer_lat, first.customer_lon]);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleComplete = async (deliveryId: number) => {
    setCompleting((prev) => ({ ...prev, [deliveryId]: true }));
    try {
      await api.agent.completeDelivery(deliveryId);
      await fetchDashboard();
    } catch (err) {
      console.error("Failed to complete delivery:", err);
    } finally {
      setCompleting((prev) => ({ ...prev, [deliveryId]: false }));
    }
  };

  const geometryCoords: [number, number][] = [];
  if (data?.route?.geometry?.type === "LineString" && Array.isArray(data.route.geometry.coordinates)) {
    for (const c of data.route.geometry.coordinates) {
      if (Array.isArray(c) && c.length >= 2) {
        geometryCoords.push([c[1], c[0]]);
      }
    }
  }

  const routeOrderedDeliveries = data?.route?.stops
    ?.filter((s) => data.deliveries.some((d) => d.id === s.delivery_id))
    .sort((a, b) => a.stop_order - b.stop_order) ?? [];

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={fetchDashboard} />;
  if (!data) return null;

  const hasDeliveries = data.deliveries.length > 0;
  const allCompleted = !hasDeliveries && !data.route;
  const noRoute = !hasDeliveries && !allCompleted;

  if (allCompleted) return <AllCompletedState />;
  if (noRoute) return <EmptyState />;

  return (
    <div className="flex h-full flex-col lg:flex-row">
      <div className="h-[50vh] w-full shrink-0 lg:h-full lg:w-3/5">
        <MapContainer center={center} zoom={13} className="h-full w-full" key={data.deliveries.length}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="OpenStreetMap"
          />
          {geometryCoords.length > 1 && (
            <Polyline
              positions={geometryCoords}
              pathOptions={{ color: "#3b82f6", weight: 4, opacity: 0.7 }}
            />
          )}
          {routeOrderedDeliveries.map((stop) => {
            if (!stop.customer_lat || !stop.customer_lon) return null;
            const delivery = data.deliveries.find((d) => d.id === stop.delivery_id);
            const riskColor = stop.risk_category
              ? RISK_COLORS[stop.risk_category] || "#888"
              : "#888";
            return (
              <Marker
                key={stop.delivery_id}
                position={[stop.customer_lat, stop.customer_lon]}
                icon={RiskIcon(riskColor)}
              >
                <Popup>
                  <div className="min-w-[180px] text-sm">
                    <p className="font-semibold">
                      {stop.delivery_order_id || `Delivery #${stop.delivery_id}`}
                    </p>
                    <p className="mb-1 text-xs text-zinc-500">
                      Stop #{stop.stop_order}
                    </p>
                    {delivery?.customer_name && (
                      <p className="text-xs text-zinc-600">{delivery.customer_name}</p>
                    )}
                    {delivery?.delivery_street && (
                      <p className="text-xs text-zinc-400">{delivery.delivery_street}</p>
                    )}
                    {stop.risk_category && (
                      <p className="mt-1 text-xs" style={{ color: riskColor }}>
                        Risk: {stop.risk_category}
                        {stop.risk_score != null && ` (${stop.risk_score.toFixed(1)})`}
                      </p>
                    )}
                    {delivery?.package_weight && (
                      <p className="text-xs text-zinc-400">
                        Weight: {delivery.package_weight} kg
                      </p>
                    )}
                    <button
                      onClick={() => handleComplete(stop.delivery_id)}
                      disabled={completing[stop.delivery_id]}
                      className="mt-2 flex w-full items-center justify-center gap-1 rounded bg-green-600 px-2 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      {completing[stop.delivery_id] ? (
                        <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      ) : (
                        <CheckCircle className="h-3 w-3" />
                      )}
                      Mark Completed
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>

      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="border-b bg-zinc-50 px-4 py-3">
          <h2 className="text-sm font-semibold text-zinc-700">
            Deliveries ({data.deliveries.length})
          </h2>
        </div>
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {data.deliveries.length === 0 ? (
            <p className="py-8 text-center text-sm text-zinc-400">No pending deliveries.</p>
          ) : (
            routeOrderedDeliveries.length > 0
              ? routeOrderedDeliveries.map((stop) => {
                  const delivery = data.deliveries.find((d) => d.id === stop.delivery_id);
                  if (!delivery) return null;
                  return (
                    <DeliveryCard
                      key={delivery.id}
                      delivery={delivery}
                      completing={!!completing[delivery.id]}
                      onComplete={() => handleComplete(delivery.id)}
                    />
                  );
                })
              : data.deliveries.map((delivery) => (
                  <DeliveryCard
                    key={delivery.id}
                    delivery={delivery}
                    completing={!!completing[delivery.id]}
                    onComplete={() => handleComplete(delivery.id)}
                  />
                ))
          )}
        </div>
      </div>
    </div>
  );
}
