export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Delivery {
  id: number;
  order_id?: string;
  customer_id: number;
  customer_name?: string;
  delivery_street?: string;
  delivery_city?: string;
  delivery_pincode?: string;
  customer_lat?: number;
  customer_lon?: number;
  warehouse_lat?: number;
  warehouse_lon?: number;
  distance_km?: number;
  delivery_zone?: string;
  time_slot?: string;
  day_of_week?: string;
  location_type?: string;
  building_type?: string;
  floor_number?: number;
  lift_available?: boolean;
  payment_type?: string;
  package_weight?: number;
  package_size?: string;
  weather?: string;
  traffic_level?: string;
  past_success_rate?: number;
  customer_cancellation_rate?: number;
  customer_return_rate?: number;
  agent_daily_load?: number;
  previous_failed_attempt_same_order?: number;
  agent_id?: number;
  warehouse_id?: number;
  status?: string;
  risk_score?: number;
  risk_category?: string;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: number;
  name: string;
  phone?: string;
  vehicle_type?: string;
  warehouse_id?: number;
  current_lat?: number;
  current_lon?: number;
  current_load: number;
  max_load: number;
  success_rate: number;
  is_available: boolean;
  status?: string;
}

export interface Warehouse {
  id: number;
  name: string;
  street?: string;
  city?: string;
  pincode?: string;
  lat: number;
  lon: number;
  created_at: string;
}

export interface WarehouseCreate {
  name: string;
  street?: string;
  city?: string;
  pincode?: string;
  lat: number;
  lon: number;
}

export interface WarehouseUpdate {
  name?: string;
  street?: string;
  city?: string;
  pincode?: string;
  lat?: number;
  lon?: number;
}

export interface Alert {
  id: number;
  delivery_id?: number;
  agent_id?: number;
  alert_type: string;
  severity: string;
  message: string;
  is_acknowledged: boolean;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id?: number;
  action_type: string;
  entity_type?: string;
  entity_id?: number;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface Route {
  id: number;
  name: string;
  agent_id: number;
  status: string;
  total_distance?: number;
  total_risk_score?: number;
  created_at: string;
}

export interface RouteStopDetail {
  stop_order: number;
  delivery_id: number;
  delivery_order_id?: string;
  customer_lat?: number;
  customer_lon?: number;
}

export interface RouteDetail {
  id: number;
  name: string;
  agent_id: number;
  status: string;
  total_distance?: number;
  total_risk_score?: number;
  geometry?: Record<string, unknown>;
  created_at: string;
  completed_at?: string;
  stops: RouteStopDetail[];
}

export interface PredictionResult {
  order_id?: string;
  probability: number;
  risk_score: number;
  risk_category: string;
  confidence: string;
  explanation: { factor: string; value: number; description: string }[];
}

export interface KPICards {
  total_deliveries: number;
  pending: number;
  delivered: number;
  failed: number;
  avg_risk_score: number;
  active_alerts: number;
}

// Assignment Session types
export interface AssignmentSession {
  id: number;
  name: string;
  date: string;
  status: string;
  created_at: string;
  updated_at: string;
  delivery_count: number;
  agent_count: number;
  routes_count: number;
}

export interface SessionDeliveryInfo {
  id: number;
  delivery_id: number;
  agent_id?: number;
  status: string;
  order_id?: string;
  customer_name?: string;
  delivery_street?: string;
  delivery_city?: string;
  delivery_pincode?: string;
  customer_lat?: number;
  customer_lon?: number;
  risk_score?: number;
  risk_category?: string;
  delivery_zone?: string;
  distance_km?: number;
}

export interface RouteInSession {
  id: number;
  name: string;
  agent_id: number;
  status: string;
  total_distance?: number;
  total_risk_score?: number;
}

export interface AgentGroupInfo {
  agent_id: number;
  agent_name: string;
  vehicle_type?: string;
  success_rate: number;
  current_load: number;
  max_load: number;
  deliveries: SessionDeliveryInfo[];
  route?: RouteInSession | null;
}

export interface AssignmentSessionDetail {
  id: number;
  name: string;
  date: string;
  status: string;
  created_at: string;
  updated_at: string;
  deliveries: SessionDeliveryInfo[];
  agents: AgentGroupInfo[];
  routes: RouteInSession[];
}
