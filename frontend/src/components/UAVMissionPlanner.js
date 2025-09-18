import React, { useState, useEffect, useCallback } from 'react';
import MapComponent from './MapComponent';
import MissionControls from './MissionControls';
import MissionResults from './MissionResults';
import SimulationStatus from './SimulationStatus';
import { useMissionPlanning } from '../hooks/useMissionPlanning';
import { useSimulation } from '../hooks/useSimulation';

export default function UAVMissionPlanner() {
  const {
    waypoints,
    optimizedRoute,
    missionData,
    isPlanning,
    missionSettings,
    setWaypoints,
    setIsPlanning,
    setMissionSettings,
    planMission,
    clearWaypoints
  } = useMissionPlanning();

  const {
    simulationData,
    simulationStep,
    isSimulating,
    startSimulation,
    stopSimulation
  } = useSimulation(missionData);

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 px-6 py-4 border-b border-gray-700">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold">UAV Mission Planner</h1>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {/* Load risk heatmap */}}
              className="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors flex items-center space-x-2"
            >
              <span>Risk Heatmap</span>
            </button>
            <button
              onClick={() => {/* Clear overlays */}}
              className="px-3 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
            >
              Clear Overlays
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-96 xl:w-[28rem] min-w-[22rem] bg-gray-800 border-r border-gray-700 p-4 h-full overflow-y-auto overscroll-contain pr-3">
          <MissionControls
            waypoints={waypoints}
            isPlanning={isPlanning}
            missionSettings={missionSettings}
            onStartPlanning={() => setIsPlanning(true)}
            onStopPlanning={() => setIsPlanning(false)}
            onClearWaypoints={clearWaypoints}
            onPlanMission={planMission}
            onSettingsChange={setMissionSettings}
          />

          {missionData && (
            <MissionResults
              missionData={missionData}
              onStartSimulation={startSimulation}
              isSimulating={isSimulating}
              onStopSimulation={stopSimulation}
            />
          )}

          {simulationData && (
            <SimulationStatus
              simulationData={simulationData}
              simulationStep={simulationStep}
              isSimulating={isSimulating}
            />
          )}
        </div>

        {/* Map */}
        <div className="flex-1 relative min-w-0">
          <MapComponent
            waypoints={waypoints}
            optimizedRoute={optimizedRoute}
            isPlanning={isPlanning}
            onMapClick={(latlng) => {
              if (isPlanning) {
                const newWaypoint = {
                  lat: latlng.lat,
                  lng: latlng.lng,
                  altitude: missionSettings.altitude
                };
                setWaypoints(prev => [...prev, newWaypoint]);
              }
            }}
            simulationData={simulationData}
            simulationStep={simulationStep}
          />
        </div>
      </div>
    </div>
  );
}
