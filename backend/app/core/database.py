# backend/app/core/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./uav_missions.db")

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
    weather_conditions = Column(JSON, nullable=True)
    
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

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()