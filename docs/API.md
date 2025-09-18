# API Documentation

## Overview

The UAV Mission Planning API provides endpoints for mission planning, risk assessment, route optimization, and simulation.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently no authentication is required for demo purposes.

## Endpoints

### Mission Planning

#### Plan Mission
```http
POST /api/missions/plan
```

**Request Body:**
```json
{
  "waypoints": [
    {
      "lat": 37.7749,
      "lng": -122.4194,
      "altitude": 100.0
    }
  ],
  "battery_capacity": 100.0,
  "max_speed": 15.0,
  "weather_conditions": {}
}
```

**Response:**
```json
{
  "mission_id": "mission_20240101_120000",
  "risk_score": 0.25,
  "estimated_duration": 480.5,
  "total_distance": 1200.0,
  "optimized_route": [...],
  "risk_breakdown": {
    "weather_risk": 0.1,
    "battery_risk": 0.05,
    "no_fly_risk": 0.3,
    "terrain_risk": 0.1,
    "route_risk": 0.2,
    "altitude_risk": 0.05
  },
  "warnings": [
    "Route passes near restricted airspace"
  ],
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### List Missions
```http
GET /api/missions/
```

#### Get Mission
```http
GET /api/missions/{mission_id}
```

### Simulation

#### Run Simulation
```http
POST /api/missions/simulate
```

**Request Body:**
```json
{
  "mission_id": "mission_20240101_120000",
  "speed_multiplier": 1.0
}
```

**Response:**
```json
{
  "mission_id": "mission_20240101_120000",
  "simulation_id": "sim_mission_20240101_120000_1234",
  "simulation_steps": [
    {
      "timestamp": 0.0,
      "position": {
        "lat": 37.7749,
        "lng": -122.4194,
        "altitude": 100.0
      },
      "velocity": [0.0, 0.0, 0.0],
      "battery": 100.0,
      "risk_level": 0.1,
      "speed": 12.0
    }
  ],
  "total_duration": 480.5,
  "success": true,
  "final_battery": 85.2
}
```

### Map Data

#### Risk Heatmap
```http
GET /api/map/risk-heatmap?north=37.8&south=37.7&east=-122.3&west=-122.5&zoom=10
```

#### No-Fly Zones
```http
GET /api/map/no-fly-zones?north=37.8&south=37.7&east=-122.3&west=-122.5
```

#### Weather Data
```http
GET /api/map/weather?lat=37.7749&lng=-122.4194
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

## Rate Limiting

Currently no rate limiting is implemented for demo purposes.

## Data Models

### Waypoint
```json
{
  "lat": 37.7749,
  "lng": -122.4194,
  "altitude": 100.0
}
```

### Mission Settings
```json
{
  "battery_capacity": 100.0,
  "max_speed": 15.0,
  "altitude": 100.0
}
```

### Risk Breakdown
```json
{
  "weather_risk": 0.1,
  "battery_risk": 0.05,
  "no_fly_risk": 0.3,
  "terrain_risk": 0.1,
  "route_risk": 0.2,
  "altitude_risk": 0.05
}
```
