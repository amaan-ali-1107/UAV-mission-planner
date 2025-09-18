#!/usr/bin/env python3
"""
Sample mission scenarios for testing and demonstration
"""

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Waypoint:
    lat: float
    lng: float
    altitude: float

@dataclass
class MissionScenario:
    name: str
    description: str
    waypoints: List[Waypoint]
    battery_capacity: float
    max_speed: float
    expected_risk_level: str  # "low", "medium", "high"
    expected_duration_minutes: float

# Sample mission scenarios
SAMPLE_MISSIONS = [
    MissionScenario(
        name="Safe Urban Delivery",
        description="Short delivery mission in safe urban area",
        waypoints=[
            Waypoint(37.7749, -122.4194, 100),  # Start
            Waypoint(37.7849, -122.4094, 120),  # Waypoint 1
            Waypoint(37.7949, -122.3994, 100)   # End
        ],
        battery_capacity=80.0,
        max_speed=12.0,
        expected_risk_level="low",
        expected_duration_minutes=8.5
    ),
    
    MissionScenario(
        name="High-Risk Airport Proximity",
        description="Mission near restricted airspace - should trigger high risk",
        waypoints=[
            Waypoint(37.6200, -122.3800, 150),  # Start near SFO
            Waypoint(37.6300, -122.3700, 180),  # Closer to airport
            Waypoint(37.6400, -122.3600, 120)   # End
        ],
        battery_capacity=60.0,
        max_speed=15.0,
        expected_risk_level="high",
        expected_duration_minutes=12.0
    ),
    
    MissionScenario(
        name="Long Range Survey",
        description="Extended mission with multiple waypoints",
        waypoints=[
            Waypoint(37.7500, -122.4500, 100),  # Start
            Waypoint(37.7600, -122.4400, 120),  # Waypoint 1
            Waypoint(37.7700, -122.4300, 140),  # Waypoint 2
            Waypoint(37.7800, -122.4200, 160),  # Waypoint 3
            Waypoint(37.7900, -122.4100, 100)   # End
        ],
        battery_capacity=90.0,
        max_speed=10.0,
        expected_risk_level="medium",
        expected_duration_minutes=25.0
    ),
    
    MissionScenario(
        name="Emergency Response",
        description="High-speed emergency mission",
        waypoints=[
            Waypoint(37.7000, -122.5000, 80),   # Start
            Waypoint(37.7200, -122.4800, 100),  # Waypoint 1
            Waypoint(37.7400, -122.4600, 120)   # End
        ],
        battery_capacity=70.0,
        max_speed=20.0,
        expected_risk_level="medium",
        expected_duration_minutes=6.0
    ),
    
    MissionScenario(
        name="Mountain Survey",
        description="Mission in challenging terrain",
        waypoints=[
            Waypoint(37.8000, -122.4000, 200),  # Start at high altitude
            Waypoint(37.8100, -122.3900, 250),  # Higher altitude
            Waypoint(37.8200, -122.3800, 180)   # End
        ],
        battery_capacity=85.0,
        max_speed=8.0,
        expected_risk_level="high",
        expected_duration_minutes=18.0
    )
]

def get_mission_by_name(name: str) -> MissionScenario:
    """Get a specific mission scenario by name"""
    for mission in SAMPLE_MISSIONS:
        if mission.name == name:
            return mission
    raise ValueError(f"Mission '{name}' not found")

def get_all_missions() -> List[MissionScenario]:
    """Get all available mission scenarios"""
    return SAMPLE_MISSIONS

def get_missions_by_risk_level(risk_level: str) -> List[MissionScenario]:
    """Get missions filtered by expected risk level"""
    return [m for m in SAMPLE_MISSIONS if m.expected_risk_level == risk_level]

def convert_to_api_format(mission: MissionScenario) -> Dict[str, Any]:
    """Convert mission scenario to API request format"""
    return {
        "waypoints": [
            {"lat": wp.lat, "lng": wp.lng, "altitude": wp.altitude}
            for wp in mission.waypoints
        ],
        "battery_capacity": mission.battery_capacity,
        "max_speed": mission.max_speed
    }

if __name__ == "__main__":
    # Print all available missions
    print("Available Mission Scenarios:")
    print("=" * 50)
    
    for i, mission in enumerate(SAMPLE_MISSIONS, 1):
        print(f"{i}. {mission.name}")
        print(f"   Description: {mission.description}")
        print(f"   Waypoints: {len(mission.waypoints)}")
        print(f"   Expected Risk: {mission.expected_risk_level}")
        print(f"   Expected Duration: {mission.expected_duration_minutes} min")
        print()
