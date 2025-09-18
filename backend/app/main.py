# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
import json
import os
import logging
from datetime import datetime

# Import our custom modules
from .models.risk_model import RiskPredictor, Mission, Waypoint
from .models.route_optimizer import RouteOptimizer
from .models.simulator import MissionSimulator
from .api.weather import WeatherService
from .core.database import SessionLocal, engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="UAV Mission Planning API",
    description="AI-powered UAV mission planning with risk assessment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
risk_predictor = RiskPredictor()
route_optimizer = RouteOptimizer()
mission_simulator = MissionSimulator()
weather_service = WeatherService()

# Pydantic models for API
class WaypointInput(BaseModel):
    lat: float
    lng: float
    altitude: float = 100.0
    
class MissionPlanRequest(BaseModel):
    waypoints: List[WaypointInput]
    battery_capacity: float = 100.0
    max_speed: float = 15.0  # m/s
    weather_conditions: Optional[Dict] = None
    
class MissionResponse(BaseModel):
    mission_id: str
    risk_score: float
    estimated_duration: float
    total_distance: float
    optimized_route: List[WaypointInput]
    risk_breakdown: Dict[str, float]
    warnings: List[str]

class SimulationRequest(BaseModel):
    mission_id: str
    speed_multiplier: float = 1.0

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {
        "message": "UAV Mission Planning API", 
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "risk_model": risk_predictor.is_loaded(),
            "route_optimizer": True,
            "weather_service": True
        }
    }

@app.post("/api/missions/plan", response_model=MissionResponse)
async def plan_mission(request: MissionPlanRequest):
    """Plan a UAV mission with risk assessment and route optimization"""
    try:
        # Convert waypoints to internal format
        waypoints = [
            Waypoint(lat=wp.lat, lng=wp.lng, altitude=wp.altitude)
            for wp in request.waypoints
        ]
        
        # Create mission object
        mission = Mission(
            waypoints=waypoints,
            battery_capacity=request.battery_capacity,
            max_speed=request.max_speed
        )
        
        # Get weather data for the route
        weather_data = await weather_service.get_weather_along_route(waypoints)
        mission.weather_conditions = weather_data
        
        # Calculate initial risk score
        risk_score = risk_predictor.predict_mission_risk(mission)
        
        # Optimize route for better safety
        optimized_waypoints = route_optimizer.optimize_route(mission, risk_predictor)
        
        # Calculate optimized risk
        optimized_mission = Mission(
            waypoints=optimized_waypoints,
            battery_capacity=request.battery_capacity,
            max_speed=request.max_speed,
            weather_conditions=weather_data
        )
        
        optimized_risk = risk_predictor.predict_mission_risk(optimized_mission)
        
        # Get risk breakdown and warnings
        risk_breakdown = risk_predictor.explain_risk(optimized_mission)
        warnings = _generate_warnings(optimized_mission, risk_breakdown)
        
        # Calculate mission metrics
        total_distance = _calculate_total_distance(optimized_waypoints)
        estimated_duration = total_distance / request.max_speed
        
        # Generate unique mission ID
        mission_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Convert optimized waypoints back to API format
        optimized_route = [
            WaypointInput(lat=wp.lat, lng=wp.lng, altitude=wp.altitude)
            for wp in optimized_waypoints
        ]
        
        return MissionResponse(
            mission_id=mission_id,
            risk_score=optimized_risk,
            estimated_duration=estimated_duration,
            total_distance=total_distance,
            optimized_route=optimized_route,
            risk_breakdown=risk_breakdown,
            warnings=warnings
        )
        
    except Exception as e:
        logging.error(f"Mission planning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Mission planning failed: {str(e)}")

@app.post("/api/missions/simulate")
async def simulate_mission(request: SimulationRequest):
    """Simulate mission execution and return timeline"""
    try:
        # For MVP, return mock simulation data
        # In full implementation, this would use the actual simulator
        
        simulation_steps = []
        total_steps = 100
        
        for i in range(total_steps):
            step = {
                "timestamp": i * 0.5,  # 0.5 second intervals
                "position": {
                    "lat": 37.7749 + (i / total_steps) * 0.01,  # Mock movement
                    "lng": -122.4194 + (i / total_steps) * 0.01,
                    "altitude": 100 + np.sin(i / 10) * 20
                },
                "battery": max(0, 100 - (i / total_steps) * 80),
                "speed": 12.0 + np.random.normal(0, 1),
                "risk_level": min(1.0, 0.2 + (i / total_steps) * 0.3)
            }
            simulation_steps.append(step)
        
        return {
            "mission_id": request.mission_id,
            "simulation_steps": simulation_steps,
            "total_duration": total_steps * 0.5,
            "success": simulation_steps[-1]["battery"] > 10
        }
        
    except Exception as e:
        logging.error(f"Simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@app.get("/api/map/risk-heatmap")
async def get_risk_heatmap(
    north: float, south: float, east: float, west: float, zoom: int = 10
):
    """Generate risk heatmap for map area"""
    try:
        # Generate grid points for the bounding box
        lat_points = np.linspace(south, north, 20)
        lng_points = np.linspace(west, east, 20)
        
        heatmap_data = []
        
        for lat in lat_points:
            for lng in lng_points:
                # Mock risk calculation based on location
                # In reality, this would use the risk model
                base_risk = 0.3
                
                # Add some realistic risk factors
                if _is_near_airport(lat, lng):
                    base_risk += 0.4
                if _is_urban_area(lat, lng):
                    base_risk += 0.2
                if _is_restricted_airspace(lat, lng):
                    base_risk += 0.5
                    
                risk_score = min(1.0, base_risk + np.random.normal(0, 0.1))
                
                heatmap_data.append({
                    "lat": lat,
                    "lng": lng,
                    "risk": risk_score,
                    "intensity": risk_score
                })
        
        return {"heatmap_data": heatmap_data}
        
    except Exception as e:
        logging.error(f"Heatmap generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Heatmap generation failed: {str(e)}")

@app.get("/api/no-fly-zones")
async def get_no_fly_zones(north: float, south: float, east: float, west: float):
    """Get no-fly zones in the specified area"""
    try:
        # Mock no-fly zones - in reality, this would query a real database
        no_fly_zones = [
            {
                "id": "airport_sfo",
                "name": "San Francisco International Airport",
                "type": "airport",
                "coordinates": [
                    [-122.4194, 37.7849],
                    [-122.3894, 37.7849], 
                    [-122.3894, 37.7549],
                    [-122.4194, 37.7549]
                ],
                "altitude_restriction": 400,  # feet
                "severity": "high"
            },
            {
                "id": "military_base_1",
                "name": "Restricted Military Area",
                "type": "military",
                "coordinates": [
                    [-122.45, 37.76],
                    [-122.44, 37.76],
                    [-122.44, 37.75],
                    [-122.45, 37.75]
                ],
                "altitude_restriction": 0,
                "severity": "critical"
            }
        ]
        
        return {"no_fly_zones": no_fly_zones}
        
    except Exception as e:
        logging.error(f"No-fly zones error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get no-fly zones: {str(e)}")

# Helper functions
def _calculate_total_distance(waypoints: List[Waypoint]) -> float:
    """Calculate total distance of waypoint sequence"""
    total = 0.0
    for i in range(len(waypoints) - 1):
        total += _haversine_distance(waypoints[i], waypoints[i + 1])
    return total

def _haversine_distance(wp1: Waypoint, wp2: Waypoint) -> float:
    """Calculate distance between two waypoints using Haversine formula"""
    from math import radians, cos, sin, asin, sqrt
    
    lat1, lng1, lat2, lng2 = map(radians, [wp1.lat, wp1.lng, wp2.lat, wp2.lng])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    return 2 * asin(sqrt(a)) * 6371000  # Earth radius in meters

def _generate_warnings(mission: Mission, risk_breakdown: Dict[str, float]) -> List[str]:
    """Generate human-readable warnings based on risk analysis"""
    warnings = []
    
    if risk_breakdown.get("weather_risk", 0) > 0.6:
        warnings.append("High wind conditions detected along route")
    
    if risk_breakdown.get("battery_risk", 0) > 0.7:
        warnings.append("Insufficient battery for safe return - consider shorter route")
    
    if risk_breakdown.get("no_fly_risk", 0) > 0.5:
        warnings.append("Route passes near restricted airspace")
    
    if risk_breakdown.get("terrain_risk", 0) > 0.6:
        warnings.append("Challenging terrain detected - maintain safe altitude")
    
    return warnings

def _is_near_airport(lat: float, lng: float) -> bool:
    """Mock function to check if location is near airport"""
    # Simple check for SF area airports
    return (37.60 < lat < 37.82) and (-122.50 < lng < -122.30)

def _is_urban_area(lat: float, lng: float) -> bool:
    """Mock function to check if location is urban"""
    # Simple check for SF urban area
    return (37.70 < lat < 37.80) and (-122.50 < lng < -122.35)

def _is_restricted_airspace(lat: float, lng: float) -> bool:
    """Mock function to check for restricted airspace"""
    # Mock restricted zones
    return (37.75 < lat < 37.77) and (-122.46 < lng < -122.44)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)