import math


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _compute_centroid(coords: list[tuple[float, float]]) -> tuple[float, float]:
    n = len(coords)
    if n == 0:
        return (0, 0)
    avg_lat = sum(c[0] for c in coords) / n
    avg_lon = sum(c[1] for c in coords) / n
    return (avg_lat, avg_lon)


def cluster_deliveries(
    coords: list[tuple[float, float]],
    start_radius_km: float = 5.0,
    max_radius_km: float = 15.0,
    radius_step_km: float = 1.0,
    min_cluster_size: int = 2,
) -> list[list[int]]:
    if not coords:
        return []

    n = len(coords)
    dist_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = _haversine_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            dist_matrix[i][j] = d
            dist_matrix[j][i] = d

    unclustered = set(range(n))
    clusters: list[list[int]] = []

    current_radius = start_radius_km

    while unclustered:
        if len(unclustered) <= 1:
            break

        best_idx = -1
        best_neighbors: list[int] = []

        for i in unclustered:
            neighbors = [
                j for j in unclustered
                if j != i and dist_matrix[i][j] <= current_radius
            ]
            if len(neighbors) > len(best_neighbors):
                best_neighbors = neighbors
                best_idx = i

        if len(best_neighbors) + 1 >= min_cluster_size:
            cluster = [best_idx] + best_neighbors
            for idx in cluster:
                unclustered.discard(idx)
            clusters.append(cluster)
            current_radius = start_radius_km
        else:
            current_radius += radius_step_km
            if current_radius > max_radius_km:
                break

    for remaining_idx in list(unclustered):
        best_cluster = -1
        best_dist = float("inf")
        for ci, cluster in enumerate(clusters):
            centroid = _compute_centroid([coords[idx] for idx in cluster])
            d = _haversine_km(
                centroid[0], centroid[1],
                coords[remaining_idx][0], coords[remaining_idx][1],
            )
            if d < best_dist:
                best_dist = d
                best_cluster = ci
        if best_cluster >= 0:
            clusters[best_cluster].append(remaining_idx)
        else:
            clusters.append([remaining_idx])
        unclustered.discard(remaining_idx)

    return clusters