#!/usr/bin/env python3
"""
Run UAV mission simulations for testing and demonstration
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
import logging

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_dir))

from app.services.mission_service import MissionService
from app.services.simulation_service import SimulationService
from app.models.schemas import MissionPlanRequest, SimulationRequest
from scenarios.sample_missions import SAMPLE_MISSIONS, convert_to_api_format

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_mission_simulation(mission_name: str) -> Dict[str, Any]:
    """Run a complete mission simulation"""
    
    logger.info(f"Running simulation for mission: {mission_name}")
    
    # Get mission scenario
    mission_scenario = None
    for mission in SAMPLE_MISSIONS:
        if mission.name == mission_name:
            mission_scenario = mission
            break
    
    if not mission_scenario:
        raise ValueError(f"Mission '{mission_name}' not found")
    
    # Initialize services
    mission_service = MissionService()
    simulation_service = SimulationService()
    
    # Convert to API format
    mission_request = MissionPlanRequest(**convert_to_api_format(mission_scenario))
    
    # Plan mission
    logger.info("Planning mission...")
    mission_result = await mission_service.plan_mission(mission_request, None)  # No DB for demo
    
    # Run simulation
    logger.info("Running simulation...")
    simulation_request = SimulationRequest(
        mission_id=mission_result.mission_id,
        speed_multiplier=1.0
    )
    
    simulation_result = await simulation_service.simulate_mission(simulation_request, None)  # No DB for demo
    
    # Compile results
    results = {
        "mission_name": mission_name,
        "mission_scenario": {
            "name": mission_scenario.name,
            "description": mission_scenario.description,
            "expected_risk_level": mission_scenario.expected_risk_level,
            "expected_duration_minutes": mission_scenario.expected_duration_minutes
        },
        "planning_results": {
            "mission_id": mission_result.mission_id,
            "risk_score": mission_result.risk_score,
            "estimated_duration": mission_result.estimated_duration,
            "total_distance": mission_result.total_distance,
            "risk_breakdown": mission_result.risk_breakdown,
            "warnings": mission_result.warnings
        },
        "simulation_results": {
            "success": simulation_result["success"],
            "total_duration": simulation_result["total_duration"],
            "final_battery": simulation_result["final_battery"],
            "simulation_steps": len(simulation_result["simulation_steps"])
        }
    }
    
    return results

def print_simulation_results(results: Dict[str, Any]):
    """Print simulation results in a formatted way"""
    
    print("\n" + "="*60)
    print(f"SIMULATION RESULTS: {results['mission_name']}")
    print("="*60)
    
    # Mission scenario info
    scenario = results["mission_scenario"]
    print(f"Description: {scenario['description']}")
    print(f"Expected Risk Level: {scenario['expected_risk_level']}")
    print(f"Expected Duration: {scenario['expected_duration_minutes']} min")
    
    # Planning results
    planning = results["planning_results"]
    print(f"\nMission Planning Results:")
    print(f"  Risk Score: {planning['risk_score']:.3f}")
    print(f"  Estimated Duration: {planning['estimated_duration']/60:.1f} min")
    print(f"  Total Distance: {planning['total_distance']/1000:.2f} km")
    
    print(f"\nRisk Breakdown:")
    for category, score in planning['risk_breakdown'].items():
        print(f"  {category.replace('_', ' ').title()}: {score:.3f}")
    
    if planning['warnings']:
        print(f"\nWarnings:")
        for warning in planning['warnings']:
            print(f"  • {warning}")
    
    # Simulation results
    simulation = results["simulation_results"]
    print(f"\nSimulation Results:")
    print(f"  Success: {'✅' if simulation['success'] else '❌'}")
    print(f"  Actual Duration: {simulation['total_duration']:.1f} s")
    print(f"  Final Battery: {simulation['final_battery']:.1f}%")
    print(f"  Simulation Steps: {simulation['simulation_steps']}")
    
    print("="*60)

async def run_all_simulations():
    """Run simulations for all sample missions"""
    
    logger.info("Running simulations for all sample missions...")
    
    all_results = []
    
    for mission in SAMPLE_MISSIONS:
        try:
            results = await run_mission_simulation(mission.name)
            all_results.append(results)
            print_simulation_results(results)
        except Exception as e:
            logger.error(f"Failed to run simulation for {mission.name}: {e}")
            print(f"\n❌ Failed to run simulation for {mission.name}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("SIMULATION SUMMARY")
    print("="*60)
    
    successful_simulations = [r for r in all_results if r["simulation_results"]["success"]]
    failed_simulations = [r for r in all_results if not r["simulation_results"]["success"]]
    
    print(f"Total Missions: {len(all_results)}")
    print(f"Successful: {len(successful_simulations)}")
    print(f"Failed: {len(failed_simulations)}")
    
    if successful_simulations:
        avg_risk = sum(r["planning_results"]["risk_score"] for r in successful_simulations) / len(successful_simulations)
        print(f"Average Risk Score: {avg_risk:.3f}")
    
    if failed_simulations:
        print(f"\nFailed Missions:")
        for result in failed_simulations:
            print(f"  • {result['mission_name']}")
    
    print("="*60)

async def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        # Run specific mission
        mission_name = sys.argv[1]
        try:
            results = await run_mission_simulation(mission_name)
            print_simulation_results(results)
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            print(f"❌ Simulation failed: {e}")
    else:
        # Run all missions
        await run_all_simulations()

if __name__ == "__main__":
    asyncio.run(main())
