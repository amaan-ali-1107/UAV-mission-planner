# Mission planning API endpoints
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime

from ..core.database import get_db
from ..models.schemas import MissionPlanRequest, MissionResponse, SimulationRequest
from ..services.mission_service import MissionService
from ..services.simulation_service import SimulationService

router = APIRouter(prefix="/api/missions", tags=["missions"])

# Initialize services
mission_service = MissionService()
simulation_service = SimulationService()

@router.post("/plan", response_model=MissionResponse)
async def plan_mission(request: MissionPlanRequest, db: Session = Depends(get_db)):
    """Plan a UAV mission with risk assessment and route optimization"""
    try:
        result = await mission_service.plan_mission(request, db)
        return result
    except Exception as e:
        logging.error(f"Mission planning error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Mission planning failed: {str(e)}")

@router.post("/simulate")
async def simulate_mission(request: SimulationRequest, db: Session = Depends(get_db)):
    """Simulate mission execution and return timeline"""
    try:
        result = await simulation_service.simulate_mission(request, db)
        return result
    except Exception as e:
        logging.error(f"Simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.get("/")
async def list_missions(db: Session = Depends(get_db)):
    """List all saved missions"""
    try:
        missions = mission_service.get_missions(db)
        return {"missions": missions}
    except Exception as e:
        logging.error(f"Failed to list missions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve missions")

@router.get("/{mission_id}")
async def get_mission(mission_id: str, db: Session = Depends(get_db)):
    """Get specific mission details"""
    try:
        mission = mission_service.get_mission(mission_id, db)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        return mission
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to get mission {mission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mission")
