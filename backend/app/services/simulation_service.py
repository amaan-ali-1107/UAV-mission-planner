# Mission simulation service
from typing import Dict, List
from sqlalchemy.orm import Session
import logging
import numpy as np

from ..models.schemas import SimulationRequest, SimulationResponse
from ..models.simulator import MissionSimulator
from ..core.database import Mission as DBMission, SimulationRun

class SimulationService:
    """Service for mission simulation"""
    
    def __init__(self):
        self.simulator = MissionSimulator()
    
    async def simulate_mission(self, request: SimulationRequest, db: Session) -> Dict:
        """Simulate mission execution and return timeline"""
        try:
            # Get mission from database if session provided
            mission = None
            if db:
                mission = db.query(DBMission).filter(DBMission.mission_id == request.mission_id).first()
                if not mission:
                    raise ValueError(f"Mission {request.mission_id} not found")
            
            # Convert database mission to internal format
            from ..models.risk_model import Mission, Waypoint
            
            # If no DB, we cannot reconstruct mission from storage; for demo,
            # create a minimal placeholder using a short straight route.
            if mission:
                waypoints = [
                    Waypoint(lat=wp["lat"], lng=wp["lng"], altitude=wp["altitude"])
                    for wp in mission.optimized_route
                ]
                battery_capacity = mission.battery_capacity
                max_speed = mission.max_speed
                weather_conditions = mission.weather_conditions
            else:
                # Fallback synthetic mission (demo headless mode)
                waypoints = [
                    Waypoint(37.7749, -122.4194, 100.0),
                    Waypoint(37.7849, -122.4094, 120.0)
                ]
                battery_capacity = 80.0
                max_speed = 12.0
                weather_conditions = {"wind_speed": 5.0, "gust_speed": 7.0}
            
            internal_mission = Mission(
                waypoints=waypoints,
                battery_capacity=battery_capacity,
                max_speed=max_speed,
                weather_conditions=weather_conditions
            )
            
            # Run simulation
            simulation_result = self.simulator.simulate_mission(internal_mission, request.speed_multiplier)
            
            if "error" in simulation_result:
                raise ValueError(simulation_result["error"])
            
            # Save simulation run to database if session provided
            simulation_id = f"sim_{request.mission_id}_{int(np.random.random() * 10000)}" if db else "sim_local"
            if db:
                db_simulation = SimulationRun(
                    mission_id=request.mission_id,
                    simulation_id=simulation_id,
                    speed_multiplier=request.speed_multiplier,
                    simulation_data=simulation_result["simulation_steps"],
                    success=simulation_result["success"],
                    total_duration=simulation_result["total_duration"],
                    final_battery=simulation_result["final_battery"]
                )
                db.add(db_simulation)
                db.commit()

            return {
                "mission_id": request.mission_id,
                "simulation_id": simulation_id,
                "simulation_steps": simulation_result["simulation_steps"],
                "total_duration": simulation_result["total_duration"],
                "success": simulation_result["success"],
                "final_battery": simulation_result["final_battery"]
            }
            
        except Exception as e:
            logging.error(f"Simulation error: {str(e)}")
            # Return a structured fallback so callers don't KeyError
            return {
                "mission_id": getattr(request, "mission_id", "unknown"),
                "simulation_id": "sim_error",
                "simulation_steps": [],
                "total_duration": 0.0,
                "success": False,
                "final_battery": 0.0,
                "error": str(e)
            }
