# Map service for risk heatmaps and no-fly zones
import numpy as np
from typing import List, Dict
import logging

class MapService:
    """Service for map-related operations"""
    
    def __init__(self):
        pass
    
    async def get_risk_heatmap(self, north: float, south: float, east: float, west: float, zoom: int) -> List[Dict]:
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
                    if self._is_near_airport(lat, lng):
                        base_risk += 0.4
                    if self._is_urban_area(lat, lng):
                        base_risk += 0.2
                    if self._is_restricted_airspace(lat, lng):
                        base_risk += 0.5
                        
                    risk_score = min(1.0, base_risk + np.random.normal(0, 0.1))
                    
                    heatmap_data.append({
                        "lat": lat,
                        "lng": lng,
                        "risk": risk_score,
                        "intensity": risk_score
                    })
            
            return heatmap_data
            
        except Exception as e:
            logging.error(f"Heatmap generation error: {str(e)}")
            raise
    
    async def get_no_fly_zones(self, north: float, south: float, east: float, west: float) -> List[Dict]:
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
            
            return no_fly_zones
            
        except Exception as e:
            logging.error(f"No-fly zones error: {str(e)}")
            raise
    
    async def get_weather_data(self, lat: float, lng: float) -> Dict:
        """Get current weather data for a specific location"""
        try:
            # Mock weather data - in production, would call real weather API
            import random
            
            weather_data = {
                "lat": lat,
                "lng": lng,
                "wind_speed": random.uniform(5, 15),
                "wind_direction": random.uniform(0, 360),
                "temperature": random.uniform(15, 25),
                "humidity": random.uniform(40, 80),
                "visibility": random.uniform(8, 15),
                "precipitation": random.choice([0, 0, 0, 0.1, 0.5]),
                "cloud_cover": random.uniform(20, 80),
                "timestamp": "2024-01-01T12:00:00Z"
            }
            
            return weather_data
            
        except Exception as e:
            logging.error(f"Weather data error: {str(e)}")
            raise
    
    def _is_near_airport(self, lat: float, lng: float) -> bool:
        """Mock function to check if location is near airport"""
        # Simple check for SF area airports
        return (37.60 < lat < 37.82) and (-122.50 < lng < -122.30)
    
    def _is_urban_area(self, lat: float, lng: float) -> bool:
        """Mock function to check if location is urban"""
        # Simple check for SF urban area
        return (37.70 < lat < 37.80) and (-122.50 < lng < -122.35)
    
    def _is_restricted_airspace(self, lat: float, lng: float) -> bool:
        """Mock function to check for restricted airspace"""
        # Mock restricted zones
        return (37.75 < lat < 37.77) and (-122.46 < lng < -122.44)
