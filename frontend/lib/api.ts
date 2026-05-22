import type { User, Delivery, Agent, Alert, AuditLog, Route, PredictionResult, AssignmentSession, AssignmentSessionDetail, RouteDetail, Warehouse, WarehouseCreate, WarehouseUpdate, AgentDashboardData } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchAPI<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      fetchAPI<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    me: () => fetchAPI<User>("/auth/me"),
  },
  deliveries: {
    list: (params?: { page?: number; page_size?: number; status?: string; risk_category?: string }) => {
      const qs = new URLSearchParams();
      if (params?.page) qs.set("page", String(params.page));
      if (params?.page_size) qs.set("page_size", String(params.page_size));
      if (params?.status) qs.set("status", params.status);
      if (params?.risk_category) qs.set("risk_category", params.risk_category);
      return fetchAPI<{ deliveries: Delivery[]; total: number; page: number; page_size: number }>(`/deliveries/?${qs}`);
    },
    get: (id: number) => fetchAPI<Delivery>(`/deliveries/${id}`),
    predict: (data: Record<string, unknown>) =>
      fetchAPI<PredictionResult>("/deliveries/predict", { method: "POST", body: JSON.stringify(data) }),
    addManual: (data: { customer_name: string; delivery_street?: string; delivery_city?: string; delivery_pincode?: string; customer_lat?: number; customer_lon?: number; session_id?: number; package_weight?: number }) =>
      fetchAPI<Delivery>("/deliveries/manual", { method: "POST", body: JSON.stringify(data) }),
  },
  agents: {
    list: () => fetchAPI<Agent[]>("/agents/"),
    get: (id: number) => fetchAPI<Agent>(`/agents/${id}`),
    update: (id: number, data: Record<string, unknown>) =>
      fetchAPI<Agent>(`/agents/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    autoAssign: () => fetchAPI("/agents/auto-assign", { method: "POST" }),
    setOffline: (id: number) =>
      fetchAPI<{ detail: string; redistributed_count: number }>(`/agents/${id}/offline`, { method: "POST" }),
  },
  warehouses: {
    list: () => fetchAPI<Warehouse[]>("/warehouses/"),
    get: (id: number) => fetchAPI<Warehouse>(`/warehouses/${id}`),
    create: (data: WarehouseCreate) =>
      fetchAPI<Warehouse>("/warehouses/", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: WarehouseUpdate) =>
      fetchAPI<Warehouse>(`/warehouses/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: number) =>
      fetchAPI<{ detail: string }>(`/warehouses/${id}`, { method: "DELETE" }),
  },
  routes: {
    list: () => fetchAPI<Route[]>("/routes/"),
    get: (id: number) => fetchAPI<RouteDetail>(`/routes/${id}`),
    generate: (data: { agent_id?: number; max_deliveries?: number }) =>
      fetchAPI("/routes/generate", { method: "POST", body: JSON.stringify(data) }),
  },
  alerts: {
    list: (params?: { acknowledged?: boolean; severity?: string }) => {
      const qs = new URLSearchParams();
      if (params?.acknowledged !== undefined) qs.set("acknowledged", String(params.acknowledged));
      if (params?.severity) qs.set("severity", params.severity);
      return fetchAPI<Alert[]>(`/alerts/?${qs}`);
    },
    acknowledge: (id: number) =>
      fetchAPI<Alert>(`/alerts/${id}/acknowledge`, { method: "POST" }),
  },
  agent: {
    me: () => fetchAPI<Agent>("/agent/me"),
    dashboard: () => fetchAPI<AgentDashboardData>("/agent/dashboard"),
    completeDelivery: (deliveryId: number) =>
      fetchAPI<Delivery>(`/agent/deliveries/${deliveryId}/complete`, { method: "POST" }),
  },
  assignments: {
    list: () => fetchAPI<AssignmentSession[]>("/assignments/"),
    get: (id: number) => fetchAPI<AssignmentSessionDetail>(`/assignments/${id}`),
    create: (data: { name?: string; delivery_ids?: number[] }) =>
      fetchAPI<AssignmentSession>("/assignments/", { method: "POST", body: JSON.stringify(data) }),
    addDeliveries: (id: number, delivery_ids: number[]) =>
      fetchAPI<{ added: number }>(`/assignments/${id}/deliveries`, { method: "POST", body: JSON.stringify({ delivery_ids }) }),
    removeDelivery: (sessionId: number, deliveryId: number) =>
      fetchAPI<void>(`/assignments/${sessionId}/deliveries/${deliveryId}`, { method: "DELETE" }),
    addManual: (sessionId: number, data: { customer_name: string; delivery_street?: string; delivery_city?: string; delivery_pincode?: string; customer_lat?: number; customer_lon?: number; package_weight?: number }) =>
      fetchAPI(`/assignments/${sessionId}/deliveries/manual`, { method: "POST", body: JSON.stringify(data) }),
    generateRoutes: (sessionId: number) =>
      fetchAPI<{ session_id: number; routes_created: number; unassigned_count: number; routes: Route[] }>(
        `/assignments/${sessionId}/generate`, { method: "POST" }
      ),
    delete: (id: number) => fetchAPI<void>(`/assignments/${id}`, { method: "DELETE" }),
  },
  audit: {
    list: (params?: { user_id?: number; action_type?: string; entity_type?: string }) => {
      const qs = new URLSearchParams();
      if (params?.user_id) qs.set("user_id", String(params.user_id));
      if (params?.action_type) qs.set("action_type", params.action_type);
      if (params?.entity_type) qs.set("entity_type", params.entity_type);
      return fetchAPI<AuditLog[]>(`/audit/?${qs}`);
    },
  },
};

export { API_BASE };
