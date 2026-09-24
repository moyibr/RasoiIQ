import logging
from typing import List

logger = logging.getLogger(__name__)

def solve_vrptw(duration_matrix, distance_matrix, time_windows_seconds):
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp

    num_locations = len(duration_matrix)
    manager = pywrapcp.RoutingIndexManager(num_locations, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(duration_matrix[from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    time = "Time"
    routing.AddDimension(
        transit_callback_index,
        3600,  # allow waiting time (1 hour)
        24 * 3600,  # maximum time per vehicle
        False,  # Don't force start cumul to zero
        time,
    )
    time_dimension = routing.GetDimensionOrDie(time)
    
    print(f"DEBUG: num_locations={num_locations}, len(time_windows)={len(time_windows_seconds)}")
    print(f"DEBUG: time_windows={time_windows_seconds}")
    for i in range(num_locations):
        index = manager.NodeToIndex(i)
        start, end = time_windows_seconds[i]
        time_dimension.CumulVar(index).SetRange(int(start), int(end))

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)
    
    if solution:
        ordered_indices = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            ordered_indices.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        ordered_indices.append(manager.IndexToNode(index))
        
        # Calculate real distance and duration
        total_dist = 0.0
        total_dur = 0.0
        for i in range(len(ordered_indices) - 1):
            u = ordered_indices[i]
            v = ordered_indices[i+1]
            total_dist += distance_matrix[u][v]
            total_dur += duration_matrix[u][v]
            
        return ordered_indices, total_dist, total_dur
    else:
        return None, 0.0, 0.0

def optimize_route_nearest_neighbor(duration_matrix, distance_matrix):
    num_locations = len(duration_matrix)
    unvisited = set(range(1, num_locations))
    current_node = 0
    route = [0]
    total_dist = 0.0
    total_dur = 0.0
    
    while unvisited:
        next_node = min(unvisited, key=lambda n: duration_matrix[current_node][n])
        route.append(next_node)
        total_dist += distance_matrix[current_node][next_node]
        total_dur += duration_matrix[current_node][next_node]
        current_node = next_node
        unvisited.remove(next_node)
    
    route.append(0) # return to depot
    total_dist += distance_matrix[current_node][0]
    total_dur += duration_matrix[current_node][0]
    
    return route, total_dist, total_dur

def optimize_route_engine(duration_matrix: List[List[float]], distance_matrix: List[List[float]], time_windows_seconds: List[tuple]):
    try:
        from ortools.constraint_solver import routing_enums_pb2
        from ortools.constraint_solver import pywrapcp
        ortools_available = True
    except ImportError:
        ortools_available = False
        
    if ortools_available:
        try:
            route, dist, dur = solve_vrptw(duration_matrix, distance_matrix, time_windows_seconds)
            if route:
                return route, dist, dur, "vrptw"
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"VRPTW failed: {e}. Falling back to Nearest Neighbor.")
            pass
            
    # Fallback to NN
    route, dist, dur = optimize_route_nearest_neighbor(duration_matrix, distance_matrix)
    return route, dist, dur, "nearest_neighbor"
