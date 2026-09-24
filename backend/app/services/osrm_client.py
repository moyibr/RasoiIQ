import httpx
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

def get_osrm_matrices(coordinates: List[Tuple[float, float]]):
    """
    coordinates: list of (lat, lon)
    Returns: duration_matrix (seconds), distance_matrix (meters)
    """
    coords_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
    url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=distance,duration"
    
    try:
        with httpx.Client() as client:
            response = client.get(url, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                raise ValueError(f"OSRM returned non-Ok code: {data.get('code')}")
            
            durations = data.get("durations", [])
            distances = data.get("distances", [])
            
            # Replace nulls with 999999
            for i in range(len(durations)):
                for j in range(len(durations[i])):
                    if durations[i][j] is None:
                        durations[i][j] = 999999
                    if distances[i][j] is None:
                        distances[i][j] = 999999
            
            return durations, distances
    except httpx.TimeoutException:
        logger.error("OSRM matrix request timed out.")
    except Exception as e:
        logger.error(f"Error fetching OSRM matrices: {e}")
        
    # Fallback: Haversine distance matrix
    import math
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c * 1000 # in meters

    n = len(coordinates)
    fallback_durations = [[0.0]*n for _ in range(n)]
    fallback_distances = [[0.0]*n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                dist_m = haversine(coordinates[i][0], coordinates[i][1], coordinates[j][0], coordinates[j][1])
                fallback_distances[i][j] = dist_m
                fallback_durations[i][j] = (dist_m / 1000.0) / 20.0 * 3600.0 # Assuming 20 km/h average speed in urban
    return fallback_durations, fallback_distances

def get_osrm_route_geometry(coordinates: List[Tuple[float, float]]):
    coords_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?geometries=geojson&overview=full"
    
    try:
        with httpx.Client() as client:
            response = client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                return None
                
            routes = data.get("routes", [])
            if routes:
                return routes[0].get("geometry")
            return None
    except Exception as e:
        logger.error(f"Error fetching OSRM route geometry: {e}")
        return None
