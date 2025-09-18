import React from 'react';
import { Play, Square, AlertTriangle, Battery, Map } from 'lucide-react';

export default function MissionResults({ 
  missionData, 
  onStartSimulation, 
  isSimulating, 
  onStopSimulation 
}) {
  const getRiskColor = (riskScore) => {
    if (riskScore < 0.3) return '#22c55e'; // Green
    if (riskScore < 0.6) return '#eab308'; // Yellow
    return '#ef4444'; // Red
  };

  return (
    <div className="bg-gray-700 rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-3 flex items-center">
        Mission Analysis
        <div className="ml-2 px-2 py-1 rounded text-xs" style={{
          backgroundColor: getRiskColor(missionData.risk_score),
          color: 'white'
        }}>
          Risk: {(missionData.risk_score * 100).toFixed(0)}%
        </div>
      </h3>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="flex items-center">
            <Battery className="w-4 h-4 mr-2" />
            Duration:
          </span>
          <span>{(missionData.estimated_duration / 60).toFixed(1)} min</span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="flex items-center">
            <Map className="w-4 h-4 mr-2" />
            Distance:
          </span>
          <span>{(missionData.total_distance / 1000).toFixed(2)} km</span>
        </div>

        {/* Risk Breakdown */}
        <div className="mt-3">
          <h4 className="font-medium mb-2">Risk Breakdown:</h4>
          <div className="space-y-1 text-sm max-h-48 overflow-y-auto pr-1">
            {Object.entries(missionData.risk_breakdown).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="capitalize">{key.replace('_', ' ')}:</span>
                <span>{(value * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Warnings */}
        {missionData.warnings && missionData.warnings.length > 0 && (
          <div className="mt-3">
            <h4 className="font-medium mb-2 flex items-center text-yellow-400">
              <AlertTriangle className="w-4 h-4 mr-1" />
              Warnings:
            </h4>
            <div className="space-y-1 text-sm">
              {missionData.warnings.map((warning, index) => (
                <div key={index} className="text-yellow-300">
                  • {warning}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Simulation Controls */}
        <div className="mt-4 space-y-2">
          {!isSimulating ? (
            <button
              onClick={onStartSimulation}
              className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              <Play className="w-4 h-4" />
              <span>Run Simulation</span>
            </button>
          ) : (
            <button
              onClick={onStopSimulation}
              className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              <Square className="w-4 h-4" />
              <span>Stop Simulation</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
