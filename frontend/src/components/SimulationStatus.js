import React from 'react';

export default function SimulationStatus({ simulationData, simulationStep, isSimulating }) {
  const getRiskColor = (riskScore) => {
    if (riskScore < 0.3) return '#22c55e'; // Green
    if (riskScore < 0.6) return '#eab308'; // Yellow
    return '#ef4444'; // Red
  };

  if (!simulationData) return null;

  const currentStep = simulationData.simulation_steps[simulationStep];

  return (
    <div className="bg-gray-700 rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-3">Simulation Status</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span>Progress:</span>
          <span>{simulationStep} / {simulationData.simulation_steps.length}</span>
        </div>
        {currentStep && (
          <>
            <div className="flex justify-between">
              <span>Battery:</span>
              <span>{currentStep.battery.toFixed(0)}%</span>
            </div>
            <div className="flex justify-between">
              <span>Speed:</span>
              <span>{currentStep.speed.toFixed(1)} m/s</span>
            </div>
            <div className="flex justify-between">
              <span>Risk Level:</span>
              <span style={{color: getRiskColor(currentStep.risk_level)}}>
                {(currentStep.risk_level * 100).toFixed(0)}%
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
