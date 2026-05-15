VEHICLE_CONFIG = {
    "bike": {"max_weight_kg": 15, "max_size": "medium", "max_range_km": 15},
    "car": {"max_weight_kg": 30, "max_size": "large", "max_range_km": 50},
    "van": {"max_weight_kg": 200, "max_size": "xl", "max_range_km": 500},
}

SIZE_TIER = {"small": 0, "medium": 1, "large": 2, "xl": 3}


def get_required_vehicle(package_weight: float, package_size: str) -> str:
    weight_tier = "van"
    for vtype, spec in VEHICLE_CONFIG.items():
        if package_weight <= spec["max_weight_kg"]:
            weight_tier = vtype
            break

    size_tier = "van"
    pkg_size_tier = SIZE_TIER.get(package_size, 0)
    for vtype, spec in VEHICLE_CONFIG.items():
        spec_tier = SIZE_TIER.get(spec["max_size"], 3)
        if pkg_size_tier <= spec_tier:
            size_tier = vtype
            break

    tier_order = ["bike", "car", "van"]
    weight_idx = tier_order.index(weight_tier)
    size_idx = tier_order.index(size_tier)
    return tier_order[max(weight_idx, size_idx)]


def is_vehicle_compatible(vehicle_type: str, required: str) -> bool:
    tier_order = ["bike", "car", "van"]
    return tier_order.index(vehicle_type) >= tier_order.index(required)