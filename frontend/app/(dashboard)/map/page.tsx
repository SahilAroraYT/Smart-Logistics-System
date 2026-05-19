"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import type { Delivery, RouteDetail, RouteStopDetail, Warehouse } from "@/types";
import { L } from "@/lib/leaflet";
import "leaflet/dist/leaflet.css";

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

const ROUTE_COLORS = [
  "#3b82f6", "#8b5cf6", "#ec4899", "#f97316",
  "#14b8a6", "#6366f1", "#f43f5e", "#84cc16",
];

function RiskIcon(color: string) {
  return L.divIcon({
    className: "custom-marker",
    html: `<div style="background:${color};width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

function NumberedIcon(num: number, color: string) {
  return L.divIcon({
    className: "custom-marker",
    html: `<div style="background:${color};width:22px;height:22px;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold">${num}</div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

function WarehouseIcon() {
  return L.divIcon({
    className: "custom-warehouse-marker",
    html: `<div style="display:flex;flex-direction:column;align-items:center;gap:0">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <path d="M3 9h18"/>
        <path d="M9 3v18"/>
        <path d="M15 3v18"/>
      </svg>
    </div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

export default function MapPage() {
  const searchParams = useSearchParams();
  const routeId = searchParams.get("route_id");

  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [routeCoords, setRouteCoords] = useState<[number, number][]>([]);
  const [routeStops, setRouteStops] = useState<RouteStopDetail[]>([]);
  const [routeGeometryCoords, setRouteGeometryCoords] = useState<[number, number][]>([]);
  const [routeName, setRouteName] = useState<string | null>(null);
  const [routeAgentId, setRouteAgentId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [center, setCenter] = useState<[number, number]>([28.65, 77.1]);

  useEffect(() => {
    api.warehouses.list()
      .then(setWarehouses)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (routeId) {
      const id = parseInt(routeId);
      api.routes.get(id).then((data: RouteDetail) => {
        setRouteName(data.name);
        setRouteAgentId(data.agent_id);

        const coords: [number, number][] = [];
        const stops: RouteStopDetail[] = [];
        data.stops.forEach((s) => {
          if (s.customer_lat && s.customer_lon) {
            coords.push([s.customer_lat, s.customer_lon]);
            stops.push(s);
          }
        });
        setRouteCoords(coords);
        setRouteStops(stops);

        const geomCoords: [number, number][] = [];
        if (data.geometry?.type === "LineString" && Array.isArray(data.geometry.coordinates)) {
          for (const c of data.geometry.coordinates) {
            if (Array.isArray(c) && c.length >= 2) {
              geomCoords.push([c[1], c[0]]);
            }
          }
        }
        setRouteGeometryCoords(geomCoords);

        if (coords.length > 0) {
          setCenter(coords[0]);
        }
        setLoading(false);
      }).catch(() => setLoading(false));
    } else {
      api.deliveries.list({ page: 1, page_size: 200 })
        .then((data: { deliveries: Delivery[] }) => {
          setDeliveries(data.deliveries.filter((d) => d.customer_lat && d.customer_lon));
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [routeId]);

  const routeColor = routeAgentId !== null ? ROUTE_COLORS[routeAgentId % ROUTE_COLORS.length] : "#3b82f6";

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading map...</div>;

  return (
    <div className="h-[calc(100vh-4rem)]">
      {routeName && (
        <div className="absolute top-4 left-72 z-[1000] rounded-lg bg-white px-4 py-2 shadow-md">
          <span className="text-sm font-semibold">{routeName}</span>
          <span className="ml-2 text-xs text-zinc-500">{routeCoords.length} stops</span>
          {routeAgentId !== null && (
            <span className="ml-2 text-xs" style={{ color: routeColor }}>
              ● Agent {routeAgentId}
            </span>
          )}
        </div>
      )}
      <MapContainer center={center} zoom={routeId ? 13 : 10} className="h-full w-full">
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="OpenStreetMap" />

        {warehouses.map((wh) => (
          <Marker key={`wh-${wh.id}`} position={[wh.lat, wh.lon]} icon={WarehouseIcon()}>
            <Popup>
              <div className="text-sm">
                <strong>🏭 {wh.name}</strong><br />
                {wh.street || ""} {wh.city || ""} {wh.pincode || ""}<br />
                Loc: {wh.lat.toFixed(4)}, {wh.lon.toFixed(4)}
              </div>
            </Popup>
          </Marker>
        ))}

        {routeGeometryCoords.length > 1 && (
          <Polyline
            positions={routeGeometryCoords}
            pathOptions={{ color: routeColor, weight: 4, opacity: 0.7 }}
          />
        )}
        {routeGeometryCoords.length <= 1 && routeCoords.length > 1 && (
          <Polyline
            positions={routeCoords}
            pathOptions={{ color: routeColor, weight: 3, opacity: 0.5, dashArray: "8 4" }}
          />
        )}

        {routeId && routeCoords.map((coord, idx) => {
          const stop = routeStops[idx];
          const riskColor = stop?.risk_category
            ? RISK_COLORS[stop.risk_category] || "#888"
            : routeColor;
          return (
            <Marker key={idx} position={coord} icon={NumberedIcon(idx + 1, riskColor)}>
              <Popup>
                <div className="text-sm">
                  <strong>Stop #{idx + 1}</strong>
                  {stop?.delivery_order_id && <><br />Order: {stop.delivery_order_id}</>}
                  {stop?.risk_category && (
                    <>
                      <br />Risk: <span style={{ color: riskColor }}>{stop.risk_category}</span>
                      {stop.risk_score != null && ` (${stop.risk_score.toFixed(1)})`}
                    </>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}

        {!routeId && deliveries.map((d) => {
          const color = d.risk_category ? RISK_COLORS[d.risk_category] || "#888" : "#888";
          return (
            <Marker key={d.id} position={[d.customer_lat!, d.customer_lon!]} icon={RiskIcon(color)}>
              <Popup>
                <div className="text-sm">
                  <strong>Order {d.order_id}</strong><br />
                  Risk: <span style={{ color }}>{d.risk_category || "N/A"}</span>
                  {d.risk_score && ` (${d.risk_score.toFixed(1)})`}<br />
                  Zone: {d.delivery_zone || "N/A"}<br />
                  Status: {d.status || "N/A"}<br />
                  {d.distance_km && `Distance: ${d.distance_km.toFixed(1)} km`}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}