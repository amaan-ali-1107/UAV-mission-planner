# Weather service for fetching weather data
import aiohttp
import asyncio
from typing import List, Dict, Optional
import logging
from datetime import datetime
import random

class WeatherService:
    """Service for fetching weather data along flight routes"""
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        
    async def get_weather_along_route(self, waypoints: List) -> Dict:
        """
        Fetch weather conditions along the route
        For MVP, returns mock data. In production, would call real weather API
        """
        try:
            # For hackathon demo, return realistic mock weather data
            # In production, this would make actual API calls to weather services
            
            # Calculate average position for weather lookup
            if not waypoints:
                return self._get_default_weather()
            
            avg_lat = sum(wp.lat for wp in waypoints) / len(waypoints)
            avg_lng = sum(wp.lng for wp in waypoints) / len(waypoints)
            
            # Mock weather based on SF conditions
            base_wind_speed = 8.0  # m/s
            base_gust_speed = 12.0  # m/s
            
            # Add some realistic variation
            wind_variation = random.uniform(-3, 5)
            
            weather_data = {
                "wind_speed": max(0, base_wind_speed + wind_variation),
                "gust_speed": max(0, base_gust_speed + wind_variation * 1.5),
                "wind_direction": random.uniform(0, 360),
                "temperature": random.uniform(15, 25),  # Celsius
                "humidity": random.uniform(40, 80),     # Percentage
                "visibility": random.uniform(8, 15),    # km
                "precipitation": random.choice([0, 0, 0, 0.1, 0.5]),  # mm/hr
                "cloud_cover": random.uniform(20, 80),  # Percentage
                "timestamp": datetime.now().isoformat(),
                "source": "mock_weather_service"
            }
            
            return weather_data
            
        except Exception as e:
            logging.error(f"Weather service error: {e}")
            return self._get_default_weather()
    
    def _get_default_weather(self) -> Dict:
        """Return default safe weather conditions"""
        return {
            "wind_speed": 5.0,
            "gust_speed": 7.0,
            "wind_direction": 180,
            "temperature": 20.0,
            "humidity": 60.0,
            "visibility": 10.0,
            "precipitation": 0.0,
            "cloud_cover": 30.0,
            "timestamp": datetime.now().isoformat(),
            "source": "default_conditions"
        }
    
    async def get_forecast_along_route(self, waypoints: List, hours_ahead: int = 2) -> List[Dict]:
        """
        Get weather forecast for the next few hours along route
        Returns list of forecast data points
        """
        forecasts = []
        
        for hour in range(hours_ahead):
            forecast = await self.get_weather_along_route(waypoints)
            
            # Add some progression for demonstration
            forecast["forecast_hour"] = hour + 1
            forecast["wind_speed"] *= (1.0 + hour * 0.1)  # Slight increase over time
            
            forecasts.append(forecast)
        
        return forecasts
