import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "vehicle_tiers": ["bike", "car", "van"],
    "vehicles": {
        "bike": {"max_weight_kg": 5, "max_size": "small", "max_range_km": 15},
        "car": {"max_weight_kg": 20, "max_size": "medium", "max_range_km": 50},
        "van": {"max_weight_kg": 100, "max_size": "xl", "max_range_km": 200},
    },
    "size_order": ["small", "medium", "large", "xl"],
}

_config: dict | None = None


def _load_config() -> dict:
    global _config
    if _config is not None:
        return _config

    config_path = os.environ.get("VEHICLE_CONFIG_PATH")
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            _config = json.load(f)
    else:
        _config = DEFAULT_CONFIG.copy()

    return _config


def reload_config():
    global _config
    _config = None
    _load_config()


def get_vehicle_tier_index(vehicle_type: str) -> int:
    cfg = _load_config()
    tiers = cfg.get("vehicle_tiers", DEFAULT_CONFIG["vehicle_tiers"])
    try:
        return tiers.index(vehicle_type.lower())
    except ValueError:
        return -1


def get_required_vehicle(weight_kg: float, package_size: str) -> str:
    cfg = _load_config()
    vehicles = cfg.get("vehicles", DEFAULT_CONFIG["vehicles"])
    size_order = cfg.get("size_order", DEFAULT_CONFIG["size_order"])

    size_idx = size_order.index(package_size.lower()) if package_size.lower() in size_order else 0

    for vtype in cfg.get("vehicle_tiers", DEFAULT_CONFIG["vehicle_tiers"]):
        v = vehicles.get(vtype, {})
        v_max_weight = v.get("max_weight_kg", 0)
        v_max_size = v.get("max_size", "small")
        v_size_idx = size_order.index(v_max_size.lower()) if v_max_size.lower() in size_order else 0

        if weight_kg <= v_max_weight and size_idx <= v_size_idx:
            return vtype

    return "van"


def is_vehicle_compatible(agent_vehicle: str, required_vehicle: str) -> bool:
    agent_tier = get_vehicle_tier_index(agent_vehicle)
    required_tier = get_vehicle_tier_index(required_vehicle)
    return agent_tier >= required_tier >= 0
