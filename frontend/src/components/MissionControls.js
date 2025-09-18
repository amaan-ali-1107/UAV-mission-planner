import React from 'react';
import { Settings, Target, Square } from 'lucide-react';

export default function MissionControls({
  waypoints,
  isPlanning,
  missionSettings,
  onStartPlanning,
  onStopPlanning,
  onClearWaypoints,
  onPlanMission,
  onSettingsChange
}) {
  return (
    <div className="space-y-4">
      {/* Mission Settings */}
      <div className="bg-gray-700 rounded-lg p-4 sticky top-0 z-10">
        <h3 className="text-lg font-semibold mb-3 flex items-center">
          <Settings className="w-5 h-5 mr-2" />
          Mission Settings
        </h3>
        
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Battery Capacity (%)</label>
            <input
              type="number"
              value={missionSettings.batteryCapacity}
              onChange={(e) => onSettingsChange(prev => ({
                ...prev,
                batteryCapacity: parseInt(e.target.value)
              }))}
              className="w-full px-3 py-2 bg-gray-600 rounded border border-gray-500 focus:border-blue-500 focus:outline-none"
              min="0"
              max="100"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Max Speed (m/s)</label>
            <input
              type="number"
              value={missionSettings.maxSpeed}
              onChange={(e) => onSettingsChange(prev => ({
                ...prev,
                maxSpeed: parseInt(e.target.value)
              }))}
              className="w-full px-3 py-2 bg-gray-600 rounded border border-gray-500 focus:border-blue-500 focus:outline-none"
              min="1"
              max="30"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Altitude (m)</label>
            <input
              type="number"
              value={missionSettings.altitude}
              onChange={(e) => onSettingsChange(prev => ({
                ...prev,
                altitude: parseInt(e.target.value)
              }))}
              className="w-full px-3 py-2 bg-gray-600 rounded border border-gray-500 focus:border-blue-500 focus:outline-none"
              min="50"
              max="400"
            />
          </div>
        </div>
      </div>

      {/* Planning Controls */}
      <div className="bg-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3">Mission Planning</h3>
        
        <div className="space-y-2">
          {!isPlanning ? (
            <button
              onClick={onStartPlanning}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              <Target className="w-4 h-4" />
              <span>Start Planning</span>
            </button>
          ) : (
            <div className="space-y-2">
              <button
                onClick={onStopPlanning}
                className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                <Square className="w-4 h-4" />
                <span>Stop Planning</span>
              </button>
              <p className="text-sm text-gray-300 text-center">Click on map to add waypoints</p>
            </div>
          )}
          
          <button
            onClick={onClearWaypoints}
            className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors"
            disabled={waypoints.length === 0}
          >
            Clear Waypoints
          </button>
          
          <button
            onClick={onPlanMission}
            className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50"
            disabled={waypoints.length < 2}
          >
            Optimize Route
          </button>
        </div>
      </div>

      {/* Waypoints List */}
      {waypoints.length > 0 && (
        <div className="bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-3">Waypoints ({waypoints.length})</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
            {waypoints.map((wp, index) => (
              <div key={index} className="flex items-center justify-between text-sm bg-gray-600 p-2 rounded">
                <span>
                  {index === 0 ? '🟢' : index === waypoints.length - 1 ? '🔴' : '🔵'} 
                  {` ${wp.lat.toFixed(4)}, ${wp.lng.toFixed(4)}`}
                </span>
                <button
                  onClick={() => {
                    // Remove waypoint logic would go here
                  }}
                  className="text-red-400 hover:text-red-300"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
