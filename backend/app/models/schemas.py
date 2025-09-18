# Pydantic schemas for API requests and responses
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class WaypointInput(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")
    altitude: float = Field(100.0, ge=0, le=400, description="Altitude in meters")

class MissionPlanRequest(BaseModel):
    waypoints: List[WaypointInput] = Field(..., min_items=2, description="List of waypoints")
    battery_capacity: float = Field(100.0, ge=0, le=100, description="Battery capacity percentage")
    max_speed: float = Field(15.0, ge=1, le=50, description="Maximum speed in m/s")
    weather_conditions: Optional[Dict] = Field(None, description="Weather conditions")

class MissionResponse(BaseModel):
    mission_id: str
    risk_score: float = Field(..., ge=0, le=1, description="Risk score (0-1)")
    estimated_duration: float = Field(..., ge=0, description="Estimated duration in seconds")
    total_distance: float = Field(..., ge=0, description="Total distance in meters")
    optimized_route: List[WaypointInput]
    risk_breakdown: Dict[str, float]
    warnings: List[str]
    created_at: datetime

class SimulationRequest(BaseModel):
    mission_id: str
    speed_multiplier: float = Field(1.0, ge=0.1, le=5.0, description="Simulation speed multiplier")

class SimulationResponse(BaseModel):
    mission_id: str
    simulation_steps: List[Dict]
    total_duration: float
    success: bool
    final_battery: float

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, bool]

class RiskHeatmapPoint(BaseModel):
    lat: float
    lng: float
    risk: float
    intensity: float

class NoFlyZone(BaseModel):
    id: str
    name: str
    type: str
    coordinates: List[List[float]]
    altitude_restriction: float
    severity: str
