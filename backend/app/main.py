# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

# Import API routers
from .api.missions import router as missions_router
from .api.map import router as map_router

# Import database setup
from .core.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=logging.INFO)

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

# Include API routers
app.include_router(missions_router)
app.include_router(map_router)

@app.get("/")
async def root():
    return {
        "message": "UAV Mission Planning API", 
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    from .models.risk_model import RiskPredictor
    
    # Initialize risk predictor to check if model is loaded
    risk_predictor = RiskPredictor()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "risk_model": risk_predictor.is_loaded(),
            "route_optimizer": True,
            "weather_service": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)