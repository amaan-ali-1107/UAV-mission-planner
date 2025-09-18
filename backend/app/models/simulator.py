# Mission simulator for UAV flight simulation
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
import logging
from geopy.distance import geodesic
import math

from .risk_model import Mission, Waypoint

@dataclass
class SimulationState:
    timestamp: float
    position: Waypoint
    velocity: Tuple[float, float, float]  # vx, vy, vz in m/s
    battery: float  # Percentage
    risk_level: float  # Current risk 0-1
    speed: float  # Current speed m/s
    altitude: float  # Current altitude m

class MissionSimulator:
    """Physics-based UAV mission simulator"""
    
    def __init__(self):
        self.time_step = 0.5  # seconds
        self.battery_consumption_rate = 2.0  # %/km base rate
        self.wind_effect_factor = 0.3
        
    def simulate_mission(self, mission: Mission, speed_multiplier: float = 1.0) -> Dict:
        """
        Simulate complete mission execution
        Returns detailed simulation data
        """
        try:
            if len(mission.waypoints) < 2:
                return {"error": "Mission must have at least 2 waypoints"}
            
            simulation_steps = []
            current_state = self._initialize_simulation(mission)
            
            # Simulate flight between waypoints
            for i in range(len(mission.waypoints) - 1):
                start_wp = mission.waypoints[i]
                end_wp = mission.waypoints[i + 1]
                
                segment_steps = self._simulate_segment(
                    current_state, start_wp, end_wp, mission, speed_multiplier
                )
                
                simulation_steps.extend(segment_steps)
                
                # Update state for next segment
                if segment_steps:
                    # segment_steps items are SimulationState instances
                    current_state = segment_steps[-1]
                
                # Check for mission failure conditions
                if current_state.battery <= 0:
                    logging.warning("Mission failed: Battery depleted")
                    break
            
            # Calculate mission success
            final_battery = current_state.battery if simulation_steps else 0
            mission_success = final_battery > 10.0  # Need 10% safety margin
            
            return {
                "simulation_steps": [self._state_to_dict(step) for step in simulation_steps],
                "total_duration": len(simulation_steps) * self.time_step,
                "success": mission_success,
                "final_battery": final_battery,
                "total_distance": self._calculate_total_distance_flown(simulation_steps)
            }
            
        except Exception as e:
            logging.error(f"Simulation error: {e}")
            return {"error": str(e)}
    
    def _initialize_simulation(self, mission: Mission) -> SimulationState:
        """Initialize simulation state"""
        start_wp = mission.waypoints[0]
        
        return SimulationState(
            timestamp=0.0,
            position=start_wp,
            velocity=(0.0, 0.0, 0.0),
            battery=mission.battery_capacity,
            risk_level=0.0,
            speed=0.0,
            altitude=start_wp.altitude
        )
    
    def _simulate_segment(self, start_state: SimulationState, start_wp: Waypoint, 
                         end_wp: Waypoint, mission: Mission, speed_multiplier: float) -> List[SimulationState]:
        """Simulate flight segment between two waypoints"""
        
        steps = []
        current_state = start_state
        
        # Calculate segment parameters
        segment_distance = geodesic((start_wp.lat, start_wp.lng), (end_wp.lat, end_wp.lng)).meters
        altitude_change = end_wp.altitude - start_wp.altitude
        
        # Calculate flight path
        total_steps = max(10, int(segment_distance / (mission.max_speed * self.time_step * speed_multiplier)))
        
        for step in range(total_steps):
            progress = step / (total_steps - 1) if total_steps > 1 else 1.0
            
            # Interpolate position
            current_lat = start_wp.lat + (end_wp.lat - start_wp.lat) * progress
            current_lng = start_wp.lng + (end_wp.lng - start_wp.lng) * progress
            current_alt = start_wp.altitude + altitude_change * progress
            
            # Calculate current speed and velocity
            target_speed = mission.max_speed * speed_multiplier
            
            # Add wind effects
            wind_speed = mission.weather_conditions.get('wind_speed', 0) if mission.weather_conditions else 0
            effective_speed = max(0, target_speed - wind_speed * self.wind_effect_factor)
            
            # Calculate battery consumption
            distance_step = segment_distance / total_steps if total_steps > 0 else 0
            altitude_factor = 1.0 + abs(altitude_change) / 1000.0  # Penalty for altitude changes
            wind_factor = 1.0 + wind_speed / 10.0  # Wind resistance
            
            battery_consumption = (distance_step / 1000.0) * self.battery_consumption_rate * altitude_factor * wind_factor
            
            # Update state
            current_state = SimulationState(
                timestamp=current_state.timestamp + self.time_step,
                position=Waypoint(current_lat, current_lng, current_alt),
                velocity=self._calculate_velocity(start_wp, end_wp, effective_speed),
                battery=max(0, current_state.battery - battery_consumption),
                risk_level=self._calculate_current_risk(Waypoint(current_lat, current_lng, current_alt), mission),
                speed=effective_speed,
                altitude=current_alt
            )
            
            steps.append(current_state)
            
            # Check for failure conditions
            if current_state.battery <= 0:
                break
        
        return steps
    
    def _calculate_velocity(self, start_wp: Waypoint, end_wp: Waypoint, speed: float) -> Tuple[float, float, float]:
        """Calculate velocity vector between waypoints"""
        distance = geodesic((start_wp.lat, start_wp.lng), (end_wp.lat, end_wp.lng)).meters
        
        if distance == 0:
            return (0.0, 0.0, 0.0)
        
        # Simplified velocity calculation (not accounting for Earth curvature)
        dlat = (end_wp.lat - start_wp.lat) * 111000  # meters per degree lat
        dlng = (end_wp.lng - start_wp.lng) * 111000 * math.cos(math.radians(start_wp.lat))
        dalt = end_wp.altitude - start_wp.altitude
        
        total_distance = math.sqrt(dlat**2 + dlng**2 + dalt**2)
        
        if total_distance == 0:
            return (0.0, 0.0, 0.0)
        
        # Normalize and scale by speed
        vx = (dlat / total_distance) * speed
        vy = (dlng / total_distance) * speed
        vz = (dalt / total_distance) * speed
        
        return (vx, vy, vz)
    
    def _calculate_current_risk(self, position: Waypoint, mission: Mission) -> float:
        """Calculate risk at current position"""
        risk_factors = 0.0
        
        # Altitude risk
        if position.altitude > 200:
            risk_factors += 0.1
        if position.altitude < 80:
            risk_factors += 0.2
        
        # Weather risk
        if mission.weather_conditions:
            wind_speed = mission.weather_conditions.get('wind_speed', 0)
            if wind_speed > 12:
                risk_factors += 0.3
            elif wind_speed > 8:
                risk_factors += 0.1
        
        # Mock no-fly zone proximity risk
        no_fly_zones = [
            (37.621311, -122.378968),  # SFO Airport
            (37.759859, -122.447151),  # Mock military base
        ]
        
        min_distance = float('inf')
        for zone_lat, zone_lng in no_fly_zones:
            distance = geodesic((position.lat, position.lng), (zone_lat, zone_lng)).meters
            min_distance = min(min_distance, distance)
        
        if min_distance < 500:
            risk_factors += 0.5
        elif min_distance < 1000:
            risk_factors += 0.2
        
        return min(1.0, risk_factors)
    
    def _state_from_step(self, step_dict: Dict) -> SimulationState:
        """Convert step dictionary back to SimulationState"""
        pos = step_dict['position']
        return SimulationState(
            timestamp=step_dict['timestamp'],
            position=Waypoint(pos['lat'], pos['lng'], pos['altitude']),
            velocity=tuple(step_dict['velocity']),
            battery=step_dict['battery'],
            risk_level=step_dict['risk_level'],
            speed=step_dict['speed'],
            altitude=pos['altitude']
        )
    
    def _state_to_dict(self, state: SimulationState) -> Dict:
        """Convert SimulationState to dictionary for JSON serialization"""
        return {
            "timestamp": state.timestamp,
            "position": {
                "lat": state.position.lat,
                "lng": state.position.lng,
                "altitude": state.position.altitude
            },
            "velocity": list(state.velocity),
            "battery": state.battery,
            "risk_level": state.risk_level,
            "speed": state.speed
        }
    
    def _calculate_total_distance_flown(self, simulation_steps: List[SimulationState]) -> float:
        """Calculate total distance flown during simulation"""
        if len(simulation_steps) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(simulation_steps)):
            prev_pos = simulation_steps[i-1].position
            curr_pos = simulation_steps[i].position
            
            distance = geodesic((prev_pos.lat, prev_pos.lng), (curr_pos.lat, curr_pos.lng)).meters
            total_distance += distance
        
        return total_distance
