# backend/app/core/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/uav_missions")

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database Models
class Mission(Base):
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    # Mission parameters
    waypoints = Column(JSON)  # List of waypoint dictionaries
    battery_capacity = Column(Float, default=100.0)
    max_speed = Column(Float, default=15.0)
    
    # Results
    risk_score = Column(Float, nullable=True)
    total_distance = Column(Float, nullable=True)
    estimated_duration = Column(Float, nullable=True)
    optimized_route = Column(JSON, nullable=True)
    risk_breakdown = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_completed = Column(Boolean, default=False)

class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(String, index=True)
    simulation_id = Column(String, unique=True, index=True)
    
    # Simulation parameters
    speed_multiplier = Column(Float, default=1.0)
    
    # Results
    simulation_data = Column(JSON)  # Complete simulation steps
    success = Column(Boolean, nullable=True)
    total_duration = Column(Float, nullable=True)
    final_battery = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(String, index=True)
    
    # Features used for prediction
    route_length_km = Column(Float)
    avg_altitude = Column(Float)
    max_altitude = Column(Float)
    min_distance_to_no_fly = Column(Float)
    wind_speed_avg = Column(Float)
    gust_max = Column(Float)
    battery_margin = Column(Float)
    waypoints_over_buildings = Column(Integer)
    line_of_sight_flag = Column(Boolean)
    terrain_roughness = Column(Float)
    weather_severity = Column(Float)
    route_complexity = Column(Float)
    
    # Prediction results
    risk_prediction = Column(Float)
    model_version = Column(String)
    
    # Risk breakdown
    weather_risk = Column(Float)
    battery_risk = Column(Float)
    no_fly_risk = Column(Float)
    terrain_risk = Column(Float)
    route_risk = Column(Float)
    altitude_risk = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# backend/app/api/weather.py
import aiohttp
import asyncio
from typing import List, Dict, Optional
import logging
from datetime import datetime

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
            import random
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

# backend/app/models/simulator.py
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
                    current_state = self._state_from_step(segment_steps[-1])
                
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
            wind_factor = 1.0 + wind_speed / 20.0  # Wind resistance
            
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

# Create a training script for the ML model
# backend/ml/train_model.py
"""
Training script for the UAV risk prediction model
Run this to create and train the XGBoost model
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.risk_model import RiskPredictor
import logging

def main():
    """Train and save the risk prediction model"""
    logging.basicConfig(level=logging.INFO)
    
    print("Training UAV Risk Prediction Model...")
    
    # Initialize risk predictor (this will trigger training)
    risk_predictor = RiskPredictor(model_path="ml/models/risk_xgb.json")
    
    if risk_predictor.is_loaded():
        print("✅ Model training completed successfully!")
        print(f"Model saved to: ml/models/risk_xgb.json")
        
        # Test the model with a sample mission
        from app.models.risk_model import Mission, Waypoint
        
        test_mission = Mission(
            waypoints=[
                Waypoint(lat=37.7749, lng=-122.4194, altitude=100),
                Waypoint(lat=37.7849, lng=-122.4094, altitude=120),
                Waypoint(lat=37.7949, lng=-122.3994, altitude=100)
            ],
            battery_capacity=80.0,
            max_speed=12.0
        )
        
        risk_score = risk_predictor.predict_mission_risk(test_mission)
        risk_explanation = risk_predictor.explain_risk(test_mission)
        
        print(f"\n🧪 Test Mission Results:")
        print(f"Risk Score: {risk_score:.3f}")
        print("Risk Breakdown:")
        for category, score in risk_explanation.items():
            print(f"  {category}: {score:.3f}")
        
    else:
        print("❌ Model training failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

# Docker configuration files
# backend/Dockerfile
"""
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for models and data
RUN mkdir -p ml/models ml/data

# Train the ML model
RUN python ml/train_model.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# frontend/package.json
frontend_package_json = '''
{
  "name": "uav-mission-planner-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "leaflet": "^1.9.4",
    "lucide-react": "^0.263.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-leaflet": "^4.2.1",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.24"
  }
}
'''

# frontend/Dockerfile
"""
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Use nginx to serve the built app
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
"""