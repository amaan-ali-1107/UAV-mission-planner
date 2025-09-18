# Mission planning service
from typing import List, Dict
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from ..models.schemas import MissionPlanRequest, MissionResponse, WaypointInput
from ..models.risk_model import RiskPredictor, Mission, Waypoint
from ..models.route_optimizer import RouteOptimizer
from ..services.weather_service import WeatherService
from ..core.database import Mission as DBMission

class MissionService:
    """Service for mission planning and management"""
    
    def __init__(self):
        self.risk_predictor = RiskPredictor()
        self.route_optimizer = RouteOptimizer()
        self.weather_service = WeatherService()
    
    async def plan_mission(self, request: MissionPlanRequest, db: Session) -> MissionResponse:
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
            weather_data = await self.weather_service.get_weather_along_route(waypoints)
            mission.weather_conditions = weather_data
            
            # Calculate initial risk score
            risk_score = self.risk_predictor.predict_mission_risk(mission)
            
            # Optimize route for better safety
            optimized_waypoints = self.route_optimizer.optimize_route(mission, self.risk_predictor)
            
            # Calculate optimized risk
            optimized_mission = Mission(
                waypoints=optimized_waypoints,
                battery_capacity=request.battery_capacity,
                max_speed=request.max_speed,
                weather_conditions=weather_data
            )
            
            optimized_risk = self.risk_predictor.predict_mission_risk(optimized_mission)
            
            # Get risk breakdown and warnings
            risk_breakdown = self.risk_predictor.explain_risk(optimized_mission)
            warnings = self._generate_warnings(optimized_mission, risk_breakdown)
            
            # Calculate mission metrics
            total_distance = self._calculate_total_distance(optimized_waypoints)
            estimated_duration = total_distance / request.max_speed
            
            # Generate unique mission ID
            mission_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Convert optimized waypoints back to API format
            optimized_route = [
                WaypointInput(lat=wp.lat, lng=wp.lng, altitude=wp.altitude)
                for wp in optimized_waypoints
            ]
            
            # Save to database if a session is provided (allow headless/demo use without DB)
            created_at = datetime.utcnow()
            if db:
                db_mission = DBMission(
                    mission_id=mission_id,
                    waypoints=[{"lat": wp.lat, "lng": wp.lng, "altitude": wp.altitude} for wp in waypoints],
                    battery_capacity=request.battery_capacity,
                    max_speed=request.max_speed,
                    risk_score=optimized_risk,
                    total_distance=total_distance,
                    estimated_duration=estimated_duration,
                    optimized_route=[{"lat": wp.lat, "lng": wp.lng, "altitude": wp.altitude} for wp in optimized_waypoints],
                    risk_breakdown=risk_breakdown,
                    warnings=warnings
                )
                db.add(db_mission)
                db.commit()
                db.refresh(db_mission)
                created_at = db_mission.created_at
            
            return MissionResponse(
                mission_id=mission_id,
                risk_score=optimized_risk,
                estimated_duration=estimated_duration,
                total_distance=total_distance,
                optimized_route=optimized_route,
                risk_breakdown=risk_breakdown,
                warnings=warnings,
                created_at=created_at
            )
            
        except Exception as e:
            logging.error(f"Mission planning error: {str(e)}")
            raise
    
    def get_missions(self, db: Session) -> List[Dict]:
        """Get all missions from database"""
        missions = db.query(DBMission).all()
        return [
            {
                "mission_id": mission.mission_id,
                "created_at": mission.created_at,
                "risk_score": mission.risk_score,
                "total_distance": mission.total_distance,
                "estimated_duration": mission.estimated_duration
            }
            for mission in missions
        ]
    
    def get_mission(self, mission_id: str, db: Session) -> Dict:
        """Get specific mission from database"""
        mission = db.query(DBMission).filter(DBMission.mission_id == mission_id).first()
        if not mission:
            return None
        
        return {
            "mission_id": mission.mission_id,
            "waypoints": mission.waypoints,
            "battery_capacity": mission.battery_capacity,
            "max_speed": mission.max_speed,
            "risk_score": mission.risk_score,
            "total_distance": mission.total_distance,
            "estimated_duration": mission.estimated_duration,
            "optimized_route": mission.optimized_route,
            "risk_breakdown": mission.risk_breakdown,
            "warnings": mission.warnings,
            "created_at": mission.created_at
        }
    
    def _calculate_total_distance(self, waypoints: List[Waypoint]) -> float:
        """Calculate total distance of waypoint sequence"""
        from geopy.distance import geodesic
        
        total = 0.0
        for i in range(len(waypoints) - 1):
            coord1 = (waypoints[i].lat, waypoints[i].lng)
            coord2 = (waypoints[i + 1].lat, waypoints[i + 1].lng)
            total += geodesic(coord1, coord2).meters
        return total
    
    def _generate_warnings(self, mission: Mission, risk_breakdown: Dict[str, float]) -> List[str]:
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
