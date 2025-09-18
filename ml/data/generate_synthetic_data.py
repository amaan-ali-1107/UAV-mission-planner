#!/usr/bin/env python3
"""
Generate synthetic training data for UAV risk prediction model
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from geopy.distance import geodesic
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_synthetic_dataset(n_samples: int = 10000) -> Tuple[pd.DataFrame, np.ndarray]:
    """Generate synthetic training dataset with realistic UAV mission scenarios"""
    
    np.random.seed(42)
    random.seed(42)
    
    feature_names = [
        'route_length_km',
        'avg_altitude',
        'max_altitude', 
        'min_distance_to_no_fly',
        'wind_speed_avg',
        'gust_max',
        'battery_margin',
        'waypoints_over_buildings',
        'line_of_sight_flag',
        'terrain_roughness',
        'weather_severity',
        'route_complexity'
    ]
    
    data = []
    labels = []
    
    logger.info(f"Generating {n_samples} synthetic mission scenarios...")
    
    for i in range(n_samples):
        if i % 1000 == 0:
            logger.info(f"Generated {i}/{n_samples} samples...")
        
        # Generate random mission parameters
        route_length = np.random.exponential(5.0)  # km
        avg_altitude = np.random.normal(120, 30)   # meters
        max_altitude = avg_altitude + np.random.exponential(50)
        
        # Environmental factors
        wind_speed = np.random.exponential(8)      # m/s
        gust_max = wind_speed + np.random.exponential(5)
        weather_severity = min(1.0, wind_speed / 15 + np.random.uniform(0, 0.3))
        
        # Safety factors
        min_distance_to_no_fly = np.random.exponential(1000)  # meters
        battery_margin = np.random.normal(20, 10)   # percentage
        waypoints_over_buildings = np.random.poisson(2)
        line_of_sight = np.random.random() > 0.3
        terrain_roughness = np.random.exponential(0.5)
        route_complexity = min(1.0, route_length / 10 + waypoints_over_buildings / 10)
        
        # Create feature vector
        features = [
            route_length,
            avg_altitude, 
            max_altitude,
            min_distance_to_no_fly,
            wind_speed,
            gust_max,
            battery_margin,
            waypoints_over_buildings,
            int(line_of_sight),
            terrain_roughness,
            weather_severity,
            route_complexity
        ]
        
        # Calculate risk label based on realistic failure conditions
        risk_score = 0.0
        
        # Weather contribution
        risk_score += min(0.3, wind_speed / 20)
        risk_score += min(0.2, gust_max / 25) 
        
        # Distance to no-fly zones
        if min_distance_to_no_fly < 500:
            risk_score += 0.4
        elif min_distance_to_no_fly < 1000:
            risk_score += 0.2
            
        # Battery margin
        if battery_margin < 15:
            risk_score += 0.3
        
        # Route length vs battery
        if route_length > 6 and battery_margin < 25:
            risk_score += 0.2
            
        # Altitude risk
        if max_altitude > 200:
            risk_score += 0.2
        if avg_altitude < 80:
            risk_score += 0.1
            
        # Terrain and complexity
        if terrain_roughness > 1.0:
            risk_score += 0.2
        if not line_of_sight:
            risk_score += 0.3
            
        # Add random noise
        risk_score += np.random.normal(0, 0.1)
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Convert to binary classification (high risk vs low risk)
        is_high_risk = risk_score > 0.5
        
        data.append(features)
        labels.append(1 if is_high_risk else 0)
    
    X = pd.DataFrame(data, columns=feature_names)
    y = np.array(labels)
    
    logger.info(f"Generated dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"High risk samples: {np.sum(y)} ({np.sum(y)/len(y)*100:.1f}%)")
    
    return X, y

def save_dataset(X: pd.DataFrame, y: np.ndarray, output_dir: str = "ml/data"):
    """Save the generated dataset to files"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save features
    X.to_csv(output_path / "features.csv", index=False)
    
    # Save labels
    np.savetxt(output_path / "labels.txt", y, fmt='%d')
    
    # Save metadata
    metadata = {
        "n_samples": len(X),
        "n_features": len(X.columns),
        "feature_names": list(X.columns),
        "high_risk_ratio": float(np.sum(y) / len(y)),
        "generation_method": "synthetic_realistic_scenarios"
    }
    
    with open(output_path / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Dataset saved to {output_path}")
    logger.info(f"Features: {output_path / 'features.csv'}")
    logger.info(f"Labels: {output_path / 'labels.txt'}")
    logger.info(f"Metadata: {output_path / 'metadata.json'}")

def main():
    """Main function to generate and save synthetic dataset"""
    
    logger.info("Starting synthetic dataset generation...")
    
    # Generate dataset
    X, y = generate_synthetic_dataset(n_samples=10000)
    
    # Save dataset
    save_dataset(X, y)
    
    logger.info("Dataset generation completed successfully!")
    
    # Print some statistics
    print("\nDataset Statistics:")
    print(f"Total samples: {len(X)}")
    print(f"Features: {len(X.columns)}")
    print(f"High risk samples: {np.sum(y)} ({np.sum(y)/len(y)*100:.1f}%)")
    print(f"Low risk samples: {len(y) - np.sum(y)} ({(len(y) - np.sum(y))/len(y)*100:.1f}%)")
    
    print("\nFeature Statistics:")
    print(X.describe())

if __name__ == "__main__":
    main()
