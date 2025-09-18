# backend/app/models/route_optimizer.py
import numpy as np
import heapq
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import logging
from geopy.distance import geodesic
import math

from .risk_model import Mission, Waypoint, RiskPredictor

@dataclass
class Node:
    lat: float
    lng: float
    altitude: float
    g_cost: float = float('inf')  # Cost from start
    h_cost: float = 0.0           # Heuristic cost to goal
    f_cost: float = float('inf')  # Total cost
    parent: Optional['Node'] = None
    
    def __hash__(self):
        return hash((round(self.lat, 6), round(self.lng, 6), round(self.altitude, 1)))
    
    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return (round(self.lat, 6) == round(other.lat, 6) and 
                round(self.lng, 6) == round(other.lng, 6) and
                round(self.altitude, 1) == round(other.altitude, 1))
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost

class RouteOptimizer:
    """A* based route optimizer with risk-aware costs"""
    
    def __init__(self):
        self.grid_resolution = 0.001  # degrees (~100m at equator)
        self.altitude_resolution = 20  # meters
        self.risk_weight = 2.0  # How much to weight risk vs distance
        
    def optimize_route(self, mission: Mission, risk_predictor: RiskPredictor) -> List[Waypoint]:
        """
        Optimize route using A* algorithm with risk-aware costs
        Returns optimized waypoint list
        """
        try:
            if len(mission.waypoints) < 2:
                return mission.waypoints
            
            # For MVP, we'll optimize segment by segment
            optimized_waypoints = [mission.waypoints[0]]  # Start with first waypoint
            
            for i in range(len(mission.waypoints) - 1):
                start = mission.waypoints[i]
                goal = mission.waypoints[i + 1]
                
                # Find optimal path between consecutive waypoints
                optimal_segment = self._find_optimal_path(
                    start, goal, mission, risk_predictor
                )
                
                # Add intermediate waypoints (skip the start as it's already added)
                optimized_waypoints.extend(optimal_segment[1:])
            
            logging.info(f"Route optimized: {len(mission.waypoints)} -> {len(optimized_waypoints)} waypoints")
            return optimized_waypoints
            
        except Exception as e:
            logging.error(f"Route optimization failed: {e}")
            return mission.waypoints  # Return original route on failure
    
    def _find_optimal_path(self, start: Waypoint, goal: Waypoint, 
                          mission: Mission, risk_predictor: RiskPredictor) -> List[Waypoint]:
        """Find optimal path between two waypoints using A*"""
        
        # Convert to nodes
        start_node = Node(start.lat, start.lng, start.altitude)
        goal_node = Node(goal.lat, goal.lng, goal.altitude)
        
        # Initialize costs
        start_node.g_cost = 0
        start_node.h_cost = self._heuristic_cost(start_node, goal_node)
        start_node.f_cost = start_node.h_cost
        
        # A* algorithm
        open_set = [start_node]
        closed_set: Set[Node] = set()
        
        max_iterations = 1000  # Prevent infinite loops
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # Get node with lowest f_cost
            current = heapq.heappop(open_set)
            
            # Check if we reached the goal
            if self._is_goal_reached(current, goal_node):
                path = self._reconstruct_path(current)
                return [Waypoint(node.lat, node.lng, node.altitude) for node in path]
            
            closed_set.add(current)
            
            # Explore neighbors
            neighbors = self._get_neighbors(current, goal_node)
            
            for neighbor in neighbors:
                if neighbor in closed_set:
                    continue
                
                # Calculate costs
                tentative_g_cost = current.g_cost + self._calculate_edge_cost(
                    current, neighbor, mission, risk_predictor
                )
                
                if neighbor not in [node for node in open_set]:
                    neighbor.h_cost = self._heuristic_cost(neighbor, goal_node)
                    heapq.heappush(open_set, neighbor)
                elif tentative_g_cost >= neighbor.g_cost:
                    continue
                
                # This path to neighbor is better
                neighbor.parent = current
                neighbor.g_cost = tentative_g_cost
                neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
        
        # If no path found, return direct path
        logging.warning("A* failed to find optimal path, using direct route")
        return [start, goal]
    
    def _get_neighbors(self, node: Node, goal: Node) -> List[Node]:
        """Generate neighboring nodes for exploration"""
        neighbors = []
        
        # Define movement directions (8-directional + altitude changes)
        directions = [
            (-1, -1, 0), (-1, 0, 0), (-1, 1, 0),
            (0, -1, 0),              (0, 1, 0),
            (1, -1, 0),  (1, 0, 0),  (1, 1, 0),
            # Altitude changes
            (0, 0, -1), (0, 0, 1)
        ]
        
        # Adaptive step size based on distance to goal
        distance_to_goal = geodesic((node.lat, node.lng), (goal.lat, goal.lng)).meters
        
        if distance_to_goal > 5000:  # > 5km, use larger steps
            step_multiplier = 5.0
        elif distance_to_goal > 1000:  # > 1km, use medium steps
            step_multiplier = 2.0
        else:  # < 1km, use fine steps
            step_multiplier = 1.0
        
        lat_step = self.grid_resolution * step_multiplier
        lng_step = self.grid_resolution * step_multiplier
        alt_step = self.altitude_resolution * step_multiplier
        
        for dlat, dlng, dalt in directions:
            new_lat = node.lat + dlat * lat_step
            new_lng = node.lng + dlng * lng_step
            new_alt = max(50, node.altitude + dalt * alt_step)  # Min altitude 50m
            
            neighbor = Node(new_lat, new_lng, new_alt)
            neighbors.append(neighbor)
        
        # Also add direct path to goal if close enough
        if distance_to_goal < 2000:  # Within 2km
            goal_neighbor = Node(goal.lat, goal.lng, goal.altitude)
            neighbors.append(goal_neighbor)
        
        return neighbors
    
    def _calculate_edge_cost(self, from_node: Node, to_node: Node, 
                           mission: Mission, risk_predictor: RiskPredictor) -> float:
        """Calculate cost of moving from one node to another"""
        
        # Physical distance cost
        coord1 = (from_node.lat, from_node.lng)
        coord2 = (to_node.lat, to_node.lng)
        distance = geodesic(coord1, coord2).meters
        
        # Altitude change cost
        altitude_change = abs(to_node.altitude - from_node.altitude)
        altitude_cost = altitude_change * 0.1  # Penalty for altitude changes
        
        # Risk cost - create a mini mission for this segment
        segment_waypoints = [
            Waypoint(from_node.lat, from_node.lng, from_node.altitude),
            Waypoint(to_node.lat, to_node.lng, to_node.altitude)
        ]
        
        segment_mission = Mission(
            waypoints=segment_waypoints,
            battery_capacity=mission.battery_capacity,
            max_speed=mission.max_speed,
            weather_conditions=mission.weather_conditions
        )
        
        try:
            risk_score = risk_predictor.predict_mission_risk(segment_mission)
        except Exception as e:
            logging.warning(f"Risk prediction failed for segment: {e}")
            risk_score = 0.3  # Default moderate risk
        
        risk_cost = risk_score * distance * self.risk_weight
        
        # Additional penalties
        terrain_penalty = self._calculate_terrain_penalty(to_node)
        no_fly_penalty = self._calculate_no_fly_penalty(to_node)
        
        total_cost = distance + altitude_cost + risk_cost + terrain_penalty + no_fly_penalty
        
        return total_cost
    
    def _calculate_terrain_penalty(self, node: Node) -> float:
        """Calculate penalty for difficult terrain"""
        # Mock terrain difficulty based on location
        # In real implementation, this would use DEM data
        
        # Higher penalty for urban areas (more obstacles)
        if (37.77 < node.lat < 37.79) and (-122.42 < node.lng < -122.40):
            return 100.0  # San Francisco downtown
        
        # Moderate penalty for hills
        if (37.75 < node.lat < 37.78) and (-122.45 < node.lng < -122.42):
            return 50.0
        
        return 0.0
    
    def _calculate_no_fly_penalty(self, node: Node) -> float:
        """Calculate penalty for proximity to no-fly zones"""
        # Mock no-fly zones
        no_fly_zones = [
            (37.621311, -122.378968, 2000),  # SFO Airport, 2km radius
            (37.759859, -122.447151, 1000),  # Mock military base, 1km radius
        ]
        
        min_distance = float('inf')
        for zone_lat, zone_lng, zone_radius in no_fly_zones:
            distance = geodesic((node.lat, node.lng), (zone_lat, zone_lng)).meters
            
            if distance < zone_radius:
                # Inside no-fly zone - very high penalty
                return 10000.0
            elif distance < zone_radius * 2:
                # Near no-fly zone - moderate penalty
                penalty = 500.0 * (1 - (distance - zone_radius) / zone_radius)
                min_distance = min(min_distance, penalty)
        
        return min_distance if min_distance != float('inf') else 0.0
    
    def _heuristic_cost(self, node: Node, goal: Node) -> float:
        """Heuristic cost function (straight-line distance to goal)"""
        coord1 = (node.lat, node.lng)
        coord2 = (goal.lat, goal.lng)
        horizontal_distance = geodesic(coord1, coord2).meters
        
        # Add altitude difference
        altitude_distance = abs(goal.altitude - node.altitude)
        
        return horizontal_distance + altitude_distance * 0.5
    
    def _is_goal_reached(self, node: Node, goal: Node) -> bool:
        """Check if we've reached the goal within tolerance"""
        distance = geodesic((node.lat, node.lng), (goal.lat, goal.lng)).meters
        altitude_diff = abs(node.altitude - goal.altitude)
        
        return distance < 100 and altitude_diff < 50  # 100m horizontal, 50m vertical tolerance
    
    def _reconstruct_path(self, goal_node: Node) -> List[Node]:
        """Reconstruct path from goal to start using parent pointers"""
        path = []
        current = goal_node
        
        while current is not None:
            path.append(current)
            current = current.parent
        
        path.reverse()
        return path
    
    def calculate_route_metrics(self, original_route: List[Waypoint], 
                              optimized_route: List[Waypoint],
                              risk_predictor: RiskPredictor,
                              mission: Mission) -> Dict[str, float]:
        """Calculate metrics comparing original vs optimized routes"""
        
        def route_distance(waypoints):
            total = 0.0
            for i in range(len(waypoints) - 1):
                coord1 = (waypoints[i].lat, waypoints[i].lng)
                coord2 = (waypoints[i + 1].lat, waypoints[i + 1].lng)
                total += geodesic(coord1, coord2).kilometers
            return total
        
        def route_risk(waypoints):
            test_mission = Mission(
                waypoints=waypoints,
                battery_capacity=mission.battery_capacity,
                max_speed=mission.max_speed,
                weather_conditions=mission.weather_conditions
            )
            return risk_predictor.predict_mission_risk(test_mission)
        
        original_distance = route_distance(original_route)
        optimized_distance = route_distance(optimized_route)
        
        original_risk = route_risk(original_route)
        optimized_risk = route_risk(optimized_route)
        
        return {
            'original_distance_km': original_distance,
            'optimized_distance_km': optimized_distance,
            'distance_increase_pct': ((optimized_distance - original_distance) / original_distance * 100) if original_distance > 0 else 0,
            'original_risk_score': original_risk,
            'optimized_risk_score': optimized_risk,
            'risk_reduction_pct': ((original_risk - optimized_risk) / original_risk * 100) if original_risk > 0 else 0,
            'efficiency_ratio': optimized_risk / optimized_distance if optimized_distance > 0 else 0  # Lower is better
        }