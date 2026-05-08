"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import type { Delivery, RouteDetail } from "@/types";
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

export default function MapPage() {
  const searchParams = useSearchParams();
  const routeId = searchParams.get("route_id");

  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [routeCoords, setRouteCoords] = useState<[number, number][]>([]);
  const [routeGeometryCoords, setRouteGeometryCoords] = useState<[number, number][]>([]);
  const [routeName, setRouteName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [center, setCenter] = useState<[number, number]>([28.65, 77.1]);

  useEffect(() => {
    if (routeId) {
      const id = parseInt(routeId);
      api.routes.get(id).then((data: RouteDetail) => {
        setRouteName(data.name);

        // Stop coordinates for numbered markers
        const coords: [number, number][] = [];
        data.stops.forEach((s) => {
          if (s.customer_lat && s.customer_lon) {
            coords.push([s.customer_lat, s.customer_lon]);
          }
        });
        setRouteCoords(coords);

        // Geometry coordinates for road-following polyline (from OSRM GeoJSON)
        const geomCoords: [number, number][] = [];
        if (data.geometry?.type === "LineString" && Array.isArray(data.geometry.coordinates)) {
          for (const c of data.geometry.coordinates) {
            if (Array.isArray(c) && c.length >= 2) {
              // OSRM returns [lon, lat] — flip to [lat, lon] for Leaflet
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

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading map...</div>;

  return (
    <div className="h-[calc(100vh-4rem)]">
      {routeName && (
        <div className="absolute top-4 left-72 z-[1000] rounded-lg bg-white px-4 py-2 shadow-md">
          <span className="text-sm font-semibold">{routeName}</span>
          <span className="ml-2 text-xs text-zinc-500">{routeCoords.length} stops</span>
        </div>
      )}
      <MapContainer center={center} zoom={routeId ? 13 : 10} className="h-full w-full">
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="OpenStreetMap" />

        {/* Route polyline — road-following from OSRM geometry, fallback to straight-line stops */}
        {routeGeometryCoords.length > 1 && (
          <Polyline
            positions={routeGeometryCoords}
            pathOptions={{ color: "#3b82f6", weight: 4, opacity: 0.7 }}
          />
        )}
        {routeGeometryCoords.length <= 1 && routeCoords.length > 1 && (
          <Polyline
            positions={routeCoords}
            pathOptions={{ color: "#3b82f6", weight: 3, opacity: 0.5, dashArray: "8 4" }}
          />
        )}

        {/* Route stops with numbered markers */}
        {routeId && routeCoords.map((coord, idx) => (
          <Marker key={idx} position={coord} icon={NumberedIcon(idx + 1, "#3b82f6")}>
            <Popup>
              <div className="text-sm">
                <strong>Stop #{idx + 1}</strong>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Regular delivery markers (when not viewing a route) */}
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
