import math
from typing import Any


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_coords(d: Any) -> tuple[float, float] | None:
    lat = getattr(d, "customer_lat", None)
    lon = getattr(d, "customer_lon", None)
    if lat is not None and lon is not None:
        return (float(lat), float(lon))
    return None


def _build_distance_matrix(coords: list[tuple[float, float]]) -> list[list[float]]:
    n = len(coords)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            matrix[i][j] = dist
            matrix[j][i] = dist
    return matrix


def _find_densest_seed(dist_matrix: list[list[float]], radius: float, available: set[int]) -> int:
    best_idx = -1
    best_count = -1
    for i in available:
        count = sum(1 for j in available if j != i and dist_matrix[i][j] <= radius)
        if count > best_count:
            best_count = count
            best_idx = i
    return best_idx


def _get_neighbors(dist_matrix: list[list[float]], seed: int, radius: float, available: set[int]) -> list[int]:
    neighbors = [seed]
    for j in available:
        if j != seed and dist_matrix[seed][j] <= radius:
            neighbors.append(j)
    return neighbors


def _cluster_centroid(deliveries: list[Any]) -> tuple[float, float] | None:
    coords = [_get_coords(d) for d in deliveries]
    coords = [c for c in coords if c is not None]
    if not coords:
        return None
    avg_lat = sum(c[0] for c in coords) / len(coords)
    avg_lon = sum(c[1] for c in coords) / len(coords)
    return (avg_lat, avg_lon)


def cluster_deliveries(
    deliveries: list[Any],
    start_radius: float = 5.0,
    max_radius: float = 15.0,
    min_cluster_size: int = 2,
) -> list[list[Any]]:
    valid = [(i, d) for i, d in enumerate(deliveries) if _get_coords(d) is not None]
    if not valid:
        return []

    indices = [v[0] for v in valid]
    coord_list = [_get_coords(d) for _, d in valid]
    dist_matrix = _build_distance_matrix(coord_list)

    available = set(range(len(indices)))
    clusters: list[list[int]] = []

    while available:
        radius = start_radius
        best_cluster: list[int] | None = None

        while radius <= max_radius:
            seed = _find_densest_seed(dist_matrix, radius, available)
            if seed == -1:
                break
            neighbors = _get_neighbors(dist_matrix, seed, radius, available)
            if len(neighbors) >= min_cluster_size:
                best_cluster = neighbors
                break
            radius += 1.0

        if best_cluster is not None:
            clusters.append(best_cluster)
            for idx in best_cluster:
                available.discard(idx)
        else:
            remaining = list(available)
            if remaining:
                clusters.append(remaining)
            available.clear()

    result = []
    for cluster_indices in clusters:
        cluster_deliveries = [deliveries[indices[i]] for i in cluster_indices]
        result.append(cluster_deliveries)

    return result


def assign_clusters_to_warehouses(
    clusters: list[list[Any]],
    warehouses: list[Any],
) -> list[tuple[list[Any], Any]]:
    result: list[tuple[list[Any], Any]] = []
    for cluster in clusters:
        centroid = _cluster_centroid(cluster)
        if centroid is None or not warehouses:
            result.append((cluster, None))
            continue

        best_wh = min(
            warehouses,
            key=lambda w: haversine_km(centroid[0], centroid[1], w.lat, w.lon),
        )
        result.append((cluster, best_wh))

    return result
