import { useState, useCallback, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function useSimulation(missionData) {
  const [simulationData, setSimulationData] = useState(null);
  const [simulationStep, setSimulationStep] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);
  const [loading, setLoading] = useState(false);

  const startSimulation = useCallback(async () => {
    if (!missionData) {
      alert('Please plan a mission first');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/missions/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mission_id: missionData.mission_id,
          speed_multiplier: 1.0
        })
      });

      const data = await response.json();
      setSimulationData(data);
      setSimulationStep(0);
      setIsSimulating(true);
      
      // Start simulation playback
      playSimulation(data.simulation_steps);
    } catch (error) {
      console.error('Simulation failed:', error);
      alert('Simulation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [missionData]);

  const playSimulation = useCallback((steps) => {
    const totalSteps = steps.length;
    let currentStep = 0;

    const interval = setInterval(() => {
      setSimulationStep(currentStep);
      currentStep++;

      if (currentStep >= totalSteps) {
        clearInterval(interval);
        setIsSimulating(false);
      }
    }, 100); // 100ms per step
  }, []);

  const stopSimulation = useCallback(() => {
    setIsSimulating(false);
    setSimulationStep(0);
  }, []);

  return {
    simulationData,
    simulationStep,
    isSimulating,
    loading,
    startSimulation,
    stopSimulation
  };
}
