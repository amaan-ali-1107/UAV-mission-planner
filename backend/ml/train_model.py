#!/usr/bin/env python3
"""
Training script for the UAV risk prediction model
Run this to create and train the XGBoost model
"""

import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.models.risk_model import RiskPredictor

def main():
    """Train and save the risk prediction model"""
    logging.basicConfig(level=logging.INFO)
    
    print("🚁 Training UAV Risk Prediction Model...")
    
    # Create models directory if it doesn't exist
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    # Initialize risk predictor (this will trigger training)
    model_path = str(models_dir / "risk_xgb.json")
    risk_predictor = RiskPredictor(model_path=model_path)
    
    if risk_predictor.is_loaded():
        print("✅ Model training completed successfully!")
        print(f"Model saved to: {model_path}")
        
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
