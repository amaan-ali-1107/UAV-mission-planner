# Map-related API endpoints
from fastapi import APIRouter, HTTPException
from typing import List, Dict
import logging

from ..services.map_service import MapService

router = APIRouter(prefix="/api/map", tags=["map"])

# Initialize service
map_service = MapService()

@router.get("/risk-heatmap")
async def get_risk_heatmap(
    north: float, south: float, east: float, west: float, zoom: int = 10
):
    """Generate risk heatmap for map area"""
    try:
        heatmap_data = await map_service.get_risk_heatmap(north, south, east, west, zoom)
        return {"heatmap_data": heatmap_data}
    except Exception as e:
        logging.error(f"Heatmap generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Heatmap generation failed: {str(e)}")

@router.get("/no-fly-zones")
async def get_no_fly_zones(north: float, south: float, east: float, west: float):
    """Get no-fly zones in the specified area"""
    try:
        no_fly_zones = await map_service.get_no_fly_zones(north, south, east, west)
        return {"no_fly_zones": no_fly_zones}
    except Exception as e:
        logging.error(f"No-fly zones error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get no-fly zones: {str(e)}")

@router.get("/weather")
async def get_weather_data(lat: float, lng: float):
    """Get current weather data for a location"""
    try:
        weather_data = await map_service.get_weather_data(lat, lng)
        return weather_data
    except Exception as e:
        logging.error(f"Weather data error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get weather data: {str(e)}")
