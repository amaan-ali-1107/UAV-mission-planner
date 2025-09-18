#!/usr/bin/env python3
"""
Advanced training script for UAV risk prediction model
Supports multiple algorithms and hyperparameter tuning
"""

import sys
import os
import logging
import json
import joblib
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import shap

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_dir))

def load_dataset(data_dir: str = "ml/data") -> Tuple[pd.DataFrame, np.ndarray]:
    """Load the generated dataset"""
    
    data_path = Path(data_dir)
    
    if not (data_path / "features.csv").exists():
        raise FileNotFoundError(f"Dataset not found in {data_path}. Run generate_synthetic_data.py first.")
    
    X = pd.read_csv(data_path / "features.csv")
    y = np.loadtxt(data_path / "labels.txt", dtype=int)
    
    with open(data_path / "metadata.json", 'r') as f:
        metadata = json.load(f)
    
    logging.info(f"Loaded dataset: {X.shape[0]} samples, {X.shape[1]} features")
    logging.info(f"High risk ratio: {metadata['high_risk_ratio']:.3f}")
    
    return X, y, metadata

def train_models(X: pd.DataFrame, y: np.ndarray) -> Dict[str, Any]:
    """Train multiple models and return results"""
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features for algorithms that need it
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = {
        'xgboost': xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        ),
        'lightgbm': lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        ),
        'random_forest': RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        ),
        'logistic_regression': LogisticRegression(
            random_state=42,
            max_iter=1000
        )
    }
    
    results = {}
    
    for name, model in models.items():
        logging.info(f"Training {name}...")
        
        # Use scaled data for algorithms that need it
        if name in ['logistic_regression']:
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        accuracy = (y_pred == y_test).mean()
        
        # Cross-validation score
        if name in ['logistic_regression']:
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='roc_auc')
        else:
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')
        
        results[name] = {
            'model': model,
            'auc_score': auc_score,
            'accuracy': accuracy,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba
        }
        
        logging.info(f"{name} - AUC: {auc_score:.3f}, Accuracy: {accuracy:.3f}, CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")
    
    return results, X_test, y_test, scaler

def hyperparameter_tuning(X: pd.DataFrame, y: np.ndarray) -> Dict[str, Any]:
    """Perform hyperparameter tuning for the best model"""
    
    logging.info("Performing hyperparameter tuning...")
    
    # XGBoost hyperparameter grid
    xgb_param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [4, 6, 8],
        'learning_rate': [0.05, 0.1, 0.15],
        'subsample': [0.8, 0.9, 1.0],
        'colsample_bytree': [0.8, 0.9, 1.0]
    }
    
    xgb_model = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
    
    # Use a smaller subset for faster tuning
    X_sample, _, y_sample, _ = train_test_split(X, y, test_size=0.7, random_state=42, stratify=y)
    
    grid_search = GridSearchCV(
        xgb_model, 
        xgb_param_grid, 
        cv=3, 
        scoring='roc_auc', 
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_sample, y_sample)
    
    logging.info(f"Best parameters: {grid_search.best_params_}")
    logging.info(f"Best CV score: {grid_search.best_score_:.3f}")
    
    return grid_search.best_estimator_, grid_search.best_params_

def create_shap_explainer(model, X_sample: pd.DataFrame) -> shap.TreeExplainer:
    """Create SHAP explainer for model interpretability"""
    
    logging.info("Creating SHAP explainer...")
    
    # Use a sample for SHAP (it can be slow with large datasets)
    X_shap_sample = X_sample.sample(min(1000, len(X_sample)), random_state=42)
    
    explainer = shap.TreeExplainer(model)
    return explainer

def save_model_and_metadata(model, scaler, feature_names: list, 
                          results: Dict, best_params: Dict, 
                          output_dir: str = "ml/models"):
    """Save the trained model and metadata"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = output_path / "risk_xgb.json"
    model.save_model(str(model_path))
    
    # Save scaler
    scaler_path = output_path / "scaler.pkl"
    joblib.dump(scaler, scaler_path)
    
    # Save metadata
    metadata = {
        'model_type': 'XGBoost',
        'feature_names': feature_names,
        'best_parameters': best_params,
        'performance': {
            'auc_score': float(results['xgboost']['auc_score']),
            'accuracy': float(results['xgboost']['accuracy']),
            'cv_mean': float(results['xgboost']['cv_mean']),
            'cv_std': float(results['xgboost']['cv_std'])
        },
        'training_info': {
            'n_features': len(feature_names),
            'feature_importance': model.feature_importances_.tolist()
        }
    }
    
    with open(output_path / "model_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logging.info(f"Model saved to {model_path}")
    logging.info(f"Scaler saved to {scaler_path}")
    logging.info(f"Metadata saved to {output_path / 'model_metadata.json'}")

def main():
    """Main training function"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting advanced model training...")
    
    try:
        # Load dataset
        X, y, metadata = load_dataset()
        feature_names = metadata['feature_names']
        
        # Train models
        results, X_test, y_test, scaler = train_models(X, y)
        
        # Hyperparameter tuning
        best_model, best_params = hyperparameter_tuning(X, y)
        
        # Update results with best model
        y_pred = best_model.predict(X_test)
        y_pred_proba = best_model.predict_proba(X_test)[:, 1]
        auc_score = roc_auc_score(y_test, y_pred_proba)
        accuracy = (y_pred == y_test).mean()
        
        results['xgboost_tuned'] = {
            'model': best_model,
            'auc_score': auc_score,
            'accuracy': accuracy,
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba
        }
        
        # Create SHAP explainer
        explainer = create_shap_explainer(best_model, X)
        
        # Save everything
        save_model_and_metadata(best_model, scaler, feature_names, results, best_params)
        
        # Print final results
        print("\n" + "="*50)
        print("FINAL MODEL PERFORMANCE")
        print("="*50)
        print(f"Best Model: XGBoost (Tuned)")
        print(f"AUC Score: {auc_score:.3f}")
        print(f"Accuracy: {accuracy:.3f}")
        print(f"Best Parameters: {best_params}")
        
        print("\nFeature Importance (Top 10):")
        feature_importance = list(zip(feature_names, best_model.feature_importances_))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        for i, (feature, importance) in enumerate(feature_importance[:10]):
            print(f"{i+1:2d}. {feature:20s}: {importance:.3f}")
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Low Risk', 'High Risk']))
        
        logger.info("Model training completed successfully!")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    main()
