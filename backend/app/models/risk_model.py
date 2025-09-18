# backend/app/models/risk_model.py
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
import shap
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from geopy.distance import geodesic
import logging

@dataclass
class Waypoint:
    lat: float
    lng: float
    altitude: float = 100.0

@dataclass 
class Mission:
    waypoints: List[Waypoint]
    battery_capacity: float = 100.0
    max_speed: float = 15.0
    weather_conditions: Optional[Dict] = None

class RiskPredictor:
    """ML-based risk prediction for UAV missions"""
    
    def __init__(self, model_path: str = "ml/models/risk_xgb.json"):
        self.model_path = model_path
        self.model = None
        self.explainer = None
        self.feature_names = [
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
        
        # Load or create model
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create and train a new one"""
        try:
            if os.path.exists(self.model_path):
                self.model = xgb.XGBClassifier()
                self.model.load_model(self.model_path)
                logging.info(f"Loaded existing model from {self.model_path}")
            else:
                logging.info("No existing model found. Creating and training new model...")
                self._create_and_train_model()
        except Exception as e:
            logging.error(f"Model loading failed: {e}")
            self._create_and_train_model()
    
    def _create_and_train_model(self):
        """Create synthetic dataset and train XGBoost model"""
        try:
            # Generate synthetic training data
            X_train, y_train = self._generate_synthetic_dataset(n_samples=10000)
            
            # Train XGBoost model
            self.model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
            
            self.model.fit(X_train, y_train)
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save_model(self.model_path)
            
            # Initialize SHAP explainer
            self.explainer = shap.TreeExplainer(self.model)
            
            logging.info("Model training completed successfully")
            
        except Exception as e:
            logging.error(f"Model training failed: {e}")
            # Fallback to simple rule-based model
            self.model = None
    
    def _generate_synthetic_dataset(self, n_samples: int = 10000) -> Tuple[pd.DataFrame, np.ndarray]:
        """Generate synthetic training dataset with realistic UAV mission scenarios"""
        
        np.random.seed(42)
        data = []
        
        for i in range(n_samples):
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
            risk_factors = []
            
            # Weather risk
            if wind_speed > 12:
                risk_factors.append(0.4)
            if gust_max > 18:
                risk_factors.append(0.3)
            
            # Battery risk  
            if battery_margin < 10:
                risk_factors.append(0.5)
            if route_length > 8 and battery_margin < 20:
                risk_factors.append(0.3)
            
            # Airspace risk
            if min_distance_to_no_fly < 200:
                risk_factors.append(0.6)
            if min_distance_to_no_fly < 500:
                risk_factors.append(0.2)
            
            # Altitude risk
            if max_altitude > 200:
                risk_factors.append(0.3)
            
            # Terrain and complexity
            if terrain_roughness > 1.0:
                risk_factors.append(0.2)
            if not line_of_sight:
                risk_factors.append(0.3)
                
            # Calculate final risk probability
            total_risk = min(1.0, sum(risk_factors) + np.random.normal(0, 0.1))
            is_high_risk = total_risk > 0.5
            
            data.append(features)
        
        X = pd.DataFrame(data, columns=self.feature_names)
        
        # Generate labels based on combined risk factors
        y = []
        for idx, row in X.iterrows():
            risk_score = 0.0
            
            # Weather contribution
            risk_score += min(0.3, row['wind_speed_avg'] / 20)
            risk_score += min(0.2, row['gust_max'] / 25) 
            
            # Distance to no-fly zones
            if row['min_distance_to_no_fly'] < 500:
                risk_score += 0.4
            elif row['min_distance_to_no_fly'] < 1000:
                risk_score += 0.2
                
            # Battery margin
            if row['battery_margin'] < 15:
                risk_score += 0.3
            
            # Route length vs battery
            if row['route_length_km'] > 6 and row['battery_margin'] < 25:
                risk_score += 0.2
                
            # Add random noise
            risk_score += np.random.normal(0, 0.1)
            
            # Convert to binary classification
            y.append(1 if risk_score > 0.5 else 0)
        
        return X, np.array(y)
    
    def predict_mission_risk(self, mission: Mission) -> float:
        """Predict risk score for a mission (0=safe, 1=high risk)"""
        try:
            if self.model is None:
                return self._fallback_risk_calculation(mission)
            
            features = self._extract_features(mission)
            risk_prob = self.model.predict_proba([features])[0][1]  # Probability of high risk
            return float(risk_prob)
        
        except Exception as e:
            logging.error(f"Risk prediction error: {e}")
            return self._fallback_risk_calculation(mission)
    
    def explain_risk(self, mission: Mission) -> Dict[str, float]:
        """Provide detailed risk breakdown with SHAP explanations"""
        try:
            if self.model is None or self.explainer is None:
                return self._fallback_risk_explanation(mission)
            
            features = self._extract_features(mission)
            shap_values = self.explainer.shap_values([features])[0]
            
            # Create risk breakdown
            risk_breakdown = {}
            feature_contributions = dict(zip(self.feature_names, shap_values))
            
            # Group related features into categories
            risk_breakdown['weather_risk'] = max(0, (
                feature_contributions.get('wind_speed_avg', 0) +
                feature_contributions.get('gust_max', 0) +
                feature_contributions.get('weather_severity', 0)
            )) / 3
            
            risk_breakdown['battery_risk'] = abs(feature_contributions.get('battery_margin', 0))
            
            risk_breakdown['no_fly_risk'] = abs(feature_contributions.get('min_distance_to_no_fly', 0))
            
            risk_breakdown['terrain_risk'] = max(0, (
                feature_contributions.get('terrain_roughness', 0) +
                feature_contributions.get('waypoints_over_buildings', 0)
            )) / 2
            
            risk_breakdown['route_risk'] = max(0, (
                feature_contributions.get('route_length_km', 0) +
                feature_contributions.get('route_complexity', 0)
            )) / 2
            
            risk_breakdown['altitude_risk'] = max(0, (
                feature_contributions.get('avg_altitude', 0) +
                feature_contributions.get('max_altitude', 0)
            )) / 2
            
            # Normalize to 0-1 range
            max_val = max(risk_breakdown.values()) if risk_breakdown.values() else 1
            if max_val > 0:
                risk_breakdown = {k: min(1.0, max(0.0, v/max_val)) 
                                for k, v in risk_breakdown.items()}
            
            return risk_breakdown
            
        except Exception as e:
            logging.error(f"Risk explanation error: {e}")
            return self._fallback_risk_explanation(mission)
    
    def _extract_features(self, mission: Mission) -> List[float]:
        """Extract feature vector from mission for ML model"""
        try:
            # Route metrics
            route_length = self._calculate_route_length(mission.waypoints)
            altitudes = [wp.altitude for wp in mission.waypoints]
            avg_altitude = np.mean(altitudes)
            max_altitude = max(altitudes)
            
            # Weather features
            weather = mission.weather_conditions or {}
            wind_speed_avg = weather.get('wind_speed', 5.0)
            gust_max = weather.get('gust_speed', wind_speed_avg * 1.5)
            weather_severity = min(1.0, wind_speed_avg / 15)
            
            # Safety features
            min_distance_to_no_fly = self._min_distance_to_restricted_areas(mission.waypoints)
            battery_margin = self._calculate_battery_margin(mission)
            waypoints_over_buildings = self._count_waypoints_over_buildings(mission.waypoints)
            line_of_sight_flag = self._check_line_of_sight(mission.waypoints)
            terrain_roughness = self._calculate_terrain_roughness(mission.waypoints)
            route_complexity = self._calculate_route_complexity(mission)
            
            return [
                route_length,
                avg_altitude,
                max_altitude,
                min_distance_to_no_fly,
                wind_speed_avg,
                gust_max,
                battery_margin,
                waypoints_over_buildings,
                int(line_of_sight_flag),
                terrain_roughness,
                weather_severity,
                route_complexity
            ]
            
        except Exception as e:
            logging.error(f"Feature extraction error: {e}")
            # Return default safe values
            return [1.0, 100.0, 100.0, 1000.0, 5.0, 7.0, 50.0, 0, 1, 0.1, 0.2, 0.1]
    
    def _calculate_route_length(self, waypoints: List[Waypoint]) -> float:
        """Calculate total route length in kilometers"""
        total_distance = 0.0
        for i in range(len(waypoints) - 1):
            coord1 = (waypoints[i].lat, waypoints[i].lng)
            coord2 = (waypoints[i + 1].lat, waypoints[i + 1].lng)
            total_distance += geodesic(coord1, coord2).kilometers
        return total_distance
    
    def _min_distance_to_restricted_areas(self, waypoints: List[Waypoint]) -> float:
        """Calculate minimum distance to known restricted areas"""
        # Mock restricted areas (airports, military zones)
        restricted_zones = [
            (37.621311, -122.378968),  # SFO Airport
            (37.759859, -122.447151),  # Mock military base
        ]
        
        min_distance = float('inf')
        for wp in waypoints:
            for zone_lat, zone_lng in restricted_zones:
                coord1 = (wp.lat, wp.lng)
                coord2 = (zone_lat, zone_lng)
                distance = geodesic(coord1, coord2).meters
                min_distance = min(min_distance, distance)
        
        return min_distance if min_distance != float('inf') else 10000.0
    
    def _calculate_battery_margin(self, mission: Mission) -> float:
        """Calculate estimated battery margin for mission"""
        route_length = self._calculate_route_length(mission.waypoints)
        
        # Simple energy consumption model
        base_consumption = 2.0  # %/km
        altitude_factor = max(mission.waypoints, key=lambda w: w.altitude).altitude / 100.0
        wind_factor = 1.0
        
        if mission.weather_conditions:
            wind_speed = mission.weather_conditions.get('wind_speed', 0)
            wind_factor = 1.0 + (wind_speed / 10.0) * 0.3
        
        total_consumption = route_length * base_consumption * altitude_factor * wind_factor
        battery_margin = mission.battery_capacity - total_consumption
        
        return max(0.0, battery_margin)
    
    def _count_waypoints_over_buildings(self, waypoints: List[Waypoint]) -> int:
        """Count waypoints over urban/building areas (mock implementation)"""
        count = 0
        for wp in waypoints:
            # Mock urban area detection (SF downtown area)
            if (37.77 < wp.lat < 37.79) and (-122.42 < wp.lng < -122.40):
                count += 1
        return count
    
    def _check_line_of_sight(self, waypoints: List[Waypoint]) -> bool:
        """Check if route maintains line of sight (simplified)"""
        if len(waypoints) < 2:
            return True
        
        # Check if any waypoint is too far from others
        max_segment_length = 5.0  # km
        for i in range(len(waypoints) - 1):
            coord1 = (waypoints[i].lat, waypoints[i].lng)
            coord2 = (waypoints[i + 1].lat, waypoints[i + 1].lng)
            if geodesic(coord1, coord2).kilometers > max_segment_length:
                return False
        
        return True
    
    def _calculate_terrain_roughness(self, waypoints: List[Waypoint]) -> float:
        """Calculate terrain roughness along route (mock implementation)"""
        # Mock terrain data based on location
        roughness_sum = 0.0
        for wp in waypoints:
            # Higher roughness near mountains/hills (mock SF hills)
            if (37.75 < wp.lat < 37.78) and (-122.45 < wp.lng < -122.42):
                roughness_sum += 0.8
            else:
                roughness_sum += 0.2
        
        return roughness_sum / len(waypoints) if waypoints else 0.0
    
    def _calculate_route_complexity(self, mission: Mission) -> float:
        """Calculate route complexity based on turns and waypoint density"""
        waypoints = mission.waypoints
        if len(waypoints) < 3:
            return 0.1
        
        # Calculate turn angles
        total_turn_angle = 0.0
        for i in range(1, len(waypoints) - 1):
            # Simplified turn angle calculation
            prev_wp = waypoints[i - 1]
            curr_wp = waypoints[i]
            next_wp = waypoints[i + 1]
            
            # Calculate vectors
            vec1_lat = curr_wp.lat - prev_wp.lat
            vec1_lng = curr_wp.lng - prev_wp.lng
            vec2_lat = next_wp.lat - curr_wp.lat
            vec2_lng = next_wp.lng - curr_wp.lng
            
            # Simple turn detection (change in direction)
            turn_factor = abs(vec1_lat - vec2_lat) + abs(vec1_lng - vec2_lng)
            total_turn_angle += turn_factor
        
        route_length = self._calculate_route_length(waypoints)
        complexity = (total_turn_angle * 100 + len(waypoints)) / max(1.0, route_length)
        
        return min(1.0, complexity)
    
    def _fallback_risk_calculation(self, mission: Mission) -> float:
        """Simple rule-based risk calculation when ML model is not available"""
        risk_score = 0.0
        
        # Route length risk
        route_length = self._calculate_route_length(mission.waypoints)
        if route_length > 10:
            risk_score += 0.3
        elif route_length > 5:
            risk_score += 0.1
        
        # Battery risk
        battery_margin = self._calculate_battery_margin(mission)
        if battery_margin < 10:
            risk_score += 0.4
        elif battery_margin < 20:
            risk_score += 0.2
        
        # Weather risk
        if mission.weather_conditions:
            wind_speed = mission.weather_conditions.get('wind_speed', 0)
            if wind_speed > 15:
                risk_score += 0.3
            elif wind_speed > 10:
                risk_score += 0.1
        
        # Restricted area risk
        min_distance = self._min_distance_to_restricted_areas(mission.waypoints)
        if min_distance < 500:
            risk_score += 0.4
        elif min_distance < 1000:
            risk_score += 0.2
        
        return min(1.0, risk_score)
    
    def _fallback_risk_explanation(self, mission: Mission) -> Dict[str, float]:
        """Fallback risk explanation when SHAP is not available"""
        route_length = self._calculate_route_length(mission.waypoints)
        battery_margin = self._calculate_battery_margin(mission)
        min_distance = self._min_distance_to_restricted_areas(mission.waypoints)
        
        wind_speed = 0
        if mission.weather_conditions:
            wind_speed = mission.weather_conditions.get('wind_speed', 0)
        
        return {
            'weather_risk': min(1.0, wind_speed / 20),
            'battery_risk': max(0.0, (30 - battery_margin) / 30),
            'no_fly_risk': max(0.0, (1000 - min_distance) / 1000),
            'terrain_risk': 0.2,  # Mock value
            'route_risk': min(1.0, route_length / 15),
            'altitude_risk': 0.1   # Mock value
        }
    
    def is_loaded(self) -> bool:
        """Check if model is properly loaded"""
        return self.model is not None