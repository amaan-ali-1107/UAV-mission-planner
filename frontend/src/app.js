import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Polygon, useMapEvents } from 'react-leaflet';
import { Icon, LatLng } from 'leaflet';
import { Play, Square, Settings, AlertTriangle, Battery, Wind, Map, Target } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons
const startIcon = new Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
      <path d="M12.5 0C5.6 0 0 5.6 0 12.5S12.5 41 12.5 41 25 19.4 25 12.5 19.4 0 12.5 0z" fill="#22c55e"/>
      <circle cx="12.5" cy="12.5" r="8" fill="white"/>
    </svg>
  `),
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

const endIcon = new Icon({
  iconUrl: 'data:image/svg+xml;base64=' + btoa(`
    <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
      <path d="M12.5 0C5.6 0 0 5.6 0 12.5S12.5 41 12.5 41 25 19.4 25 12.5 19.4 0 12.5 0z" fill="#ef4444"/>
      <circle cx="12.5" cy="12.5" r="8" fill="white"/>
    </svg>
  `),
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

const waypointIcon = new Icon({
  iconUrl: 'data:image/svg+xml;base64=' + btoa(`
    <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
      <path d="M12.5 0C5.6 0 0 5.6 0 12.5S12.5 41 12.5 41 25 19.4 25 12.5 19.4 0 12.5 0z" fill="#3b82f6"/>
      <circle cx="12.5" cy="12.5" r="6" fill="white"/>
    </svg>
  `),
  iconSize: [20, 33],
  iconAnchor: [10, 33]
});

// Map click handler component
function MapClickHandler({ onMapClick, isPlanning }) {
  useMapEvents({
    click: (e) => {
      if (isPlanning) {
        onMapClick(e.latlng);
      }
    }
  });
  return null;
}

export default function UAVMissionPlanner() {
  // State management
  const [waypoints, setWaypoints] = useState([]);
  const [optimizedRoute, setOptimizedRoute] = useState([]);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [missionData, setMissionData] = useState(null);
  const [simulationData, setSimulationData] = useState(null);
  const [simulationStep, setSimulationStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showRiskHeatmap, setShowRiskHeatmap] = useState(false);
  const [riskHeatmapData, setRiskHeatmapData] = useState([]);
  const [noFlyZones, setNoFlyZones] = useState([]);
  const [missionSettings, setMissionSettings] = useState({
    batteryCapacity: 100,
    maxSpeed: 15,
    altitude: 100
  });

  // San Francisco center
  const mapCenter = [37.7749, -122.4194];

  // Load no-fly zones and risk data
  useEffect(() => {
    loadNoFlyZones();
  }, []);

  const loadNoFlyZones = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/no-fly-zones?north=37.8&south=37.7&east=-122.3&west=-122.5`);
      const data = await response.json();
      setNoFlyZones(data.no_fly_zones || []);
    } catch (error) {
      console.error('Failed to load no-fly zones:', error);
    }
  };

  const loadRiskHeatmap = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/map/risk-heatmap?north=37.8&south=37.7&east=-122.3&west=-122.5&zoom=10`);
      const data = await response.json();
      setRiskHeatmapData(data.heatmap_data || []);
      setShowRiskHeatmap(true);
    } catch (error) {
      console.error('Failed to load risk heatmap:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMapClick = useCallback((latlng) => {
    if (isPlanning) {
      const newWaypoint = {
        lat: latlng.lat,
        lng: latlng.lng,
        altitude: missionSettings.altitude
      };
      setWaypoints(prev => [...prev, newWaypoint]);
    }
  }, [isPlanning, missionSettings.altitude]);

  const startPlanning = () => {
    setIsPlanning(true);
    setWaypoints([]);
    setOptimizedRoute([]);
    setMissionData(null);
  };

  const stopPlanning = () => {
    setIsPlanning(false);
  };

  const clearWaypoints = () => {
    setWaypoints([]);
    setOptimizedRoute([]);
    setMissionData(null);
  };

  const planMission = async () => {
    if (waypoints.length < 2) {
      alert('Please add at least 2 waypoints to plan a mission');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/missions/plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          waypoints: waypoints,
          battery_capacity: missionSettings.batteryCapacity,
          max_speed: missionSettings.maxSpeed
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setMissionData(data);
      setOptimizedRoute(data.optimized_route);
      setIsPlanning(false);
    } catch (error) {
      console.error('Mission planning failed:', error);
      alert('Mission planning failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const startSimulation = async () => {
    if (!missionData) {
      alert('Please plan a mission first');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/missions/simulate', {
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
  };

  const playSimulation = (steps) => {
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
  };

  const stopSimulation = () => {
    setIsSimulating(false);
    setSimulationStep(0);
  };

  const getRiskColor = (riskScore) => {
    if (riskScore < 0.3) return '#22c55e'; // Green
    if (riskScore < 0.6) return '#eab308'; // Yellow
    return '#ef4444'; // Red
  };

  const getCurrentSimulationPosition = () => {
    if (!simulationData || !isSimulating) return null;
    
    const step = simulationData.simulation_steps[simulationStep];
    return step ? step.position : null;
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 px-6 py-4 border-b border-gray-700">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <Target className="w-8 h-8 text-blue-500" />
            <h1 className="text-2xl font-bold">UAV Mission Planner</h1>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadRiskHeatmap}
              className="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors flex items-center space-x-2"
              disabled={loading}
            >
              <Map className="w-4 h-4" />
              <span>Risk Heatmap</span>
            </button>
            <button
              onClick={() => setShowRiskHeatmap(false)}
              className="px-3 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
            >
              Clear Overlays
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Sidebar */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 p-4 overflow-y-auto">
          {/* Mission Planning Controls */}
          <div className="space-y-4">
            <div className="bg-gray-700 rounded-lg p-4">
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
                    onChange={(e) => setMissionSettings(prev => ({
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
                    onChange={(e) => setMissionSettings(prev => ({
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
                    onChange={(e) => setMissionSettings(prev => ({
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
                    onClick={startPlanning}
                    className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center justify-center space-x-2"
                  >
                    <Target className="w-4 h-4" />
                    <span>Start Planning</span>
                  </button>
                ) : (
                  <div className="space-y-2">
                    <button
                      onClick={stopPlanning}
                      className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center justify-center space-x-2"
                    >
                      <Square className="w-4 h-4" />
                      <span>Stop Planning</span>
                    </button>
                    <p className="text-sm text-gray-300 text-center">Click on map to add waypoints</p>
                  </div>
                )}
                
                <button
                  onClick={clearWaypoints}
                  className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors"
                  disabled={waypoints.length === 0}
                >
                  Clear Waypoints
                </button>
                
                <button
                  onClick={planMission}
                  className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50"
                  disabled={waypoints.length < 2 || loading}
                >
                  {loading ? 'Planning...' : 'Optimize Route'}
                </button>
              </div>
            </div>

            {/* Waypoints List */}
            {waypoints.length > 0 && (
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3">Waypoints ({waypoints.length})</h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {waypoints.map((wp, index) => (
                    <div key={index} className="flex items-center justify-between text-sm bg-gray-600 p-2 rounded">
                      <span>
                        {index === 0 ? '🟢' : index === waypoints.length - 1 ? '🔴' : '🔵'} 
                        {` ${wp.lat.toFixed(4)}, ${wp.lng.toFixed(4)}`}
                      </span>
                      <button
                        onClick={() => {
                          setWaypoints(prev => prev.filter((_, i) => i !== index));
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

            {/* Mission Results */}
            {missionData && (
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
                    <div className="space-y-1 text-sm">
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
                        onClick={startSimulation}
                        className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors flex items-center justify-center space-x-2"
                      >
                        <Play className="w-4 h-4" />
                        <span>Run Simulation</span>
                      </button>
                    ) : (
                      <button
                        onClick={stopSimulation}
                        className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center justify-center space-x-2"
                      >
                        <Square className="w-4 h-4" />
                        <span>Stop Simulation</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Simulation Status */}
            {simulationData && (
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-3">Simulation Status</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Progress:</span>
                    <span>{simulationStep} / {simulationData.simulation_steps.length}</span>
                  </div>
                  {simulationData.simulation_steps[simulationStep] && (
                    <>
                      <div className="flex justify-between">
                        <span>Battery:</span>
                        <span>{simulationData.simulation_steps[simulationStep].battery.toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Speed:</span>
                        <span>{simulationData.simulation_steps[simulationStep].speed.toFixed(1)} m/s</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Risk Level:</span>
                        <span style={{color: getRiskColor(simulationData.simulation_steps[simulationStep].risk_level)}}>
                          {(simulationData.simulation_steps[simulationStep].risk_level * 100).toFixed(0)}%
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Map */}
        <div className="flex-1 relative">
          <MapContainer
            center={mapCenter}
            zoom={12}
            className="h-full w-full"
            style={{ backgroundColor: '#1f2937' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            
            <MapClickHandler onMapClick={handleMapClick} isPlanning={isPlanning} />

            {/* Waypoint Markers */}
            {waypoints.map((waypoint, index) => (
              <Marker
                key={`waypoint-${index}`}
                position={[waypoint.lat, waypoint.lng]}
                icon={
                  index === 0 ? startIcon : 
                  index === waypoints.length - 1 ? endIcon : 
                  waypointIcon
                }
              />
            ))}

            {/* Original Route */}
            {waypoints.length > 1 && (
              <Polyline
                positions={waypoints.map(wp => [wp.lat, wp.lng])}
                color="#6b7280"
                weight={3}
                dashArray="10, 10"
                opacity={0.7}
              />
            )}

            {/* Optimized Route */}
            {optimizedRoute.length > 1 && (
              <Polyline
                positions={optimizedRoute.map(wp => [wp.lat, wp.lng])}
                color="#22c55e"
                weight={4}
                opacity={0.9}
              />
            )}

            {/* No-Fly Zones */}
            {noFlyZones.map((zone, index) => (
              <Polygon
                key={`no-fly-${index}`}
                positions={zone.coordinates.map(coord => [coord[1], coord[0]])}
                pathOptions={{
                  fillColor: zone.severity === 'critical' ? '#dc2626' : '#f59e0b',
                  fillOpacity: 0.3,
                  color: zone.severity === 'critical' ? '#dc2626' : '#f59e0b',
                  weight: 2
                }}
              />
            ))}

            {/* Risk Heatmap */}
            {showRiskHeatmap && riskHeatmapData.map((point, index) => (
              <circle
                key={`heatmap-${index}`}
                center={[point.lat, point.lng]}
                radius={100}
                fillColor={getRiskColor(point.risk)}
                fillOpacity={0.4}
                stroke={false}
              />
            ))}

            {/* Simulation Position */}
            {getCurrentSimulationPosition() && (
              <Marker
                position={[
                  getCurrentSimulationPosition().lat,
                  getCurrentSimulationPosition().lng
                ]}
                icon={new Icon({
                  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="15" cy="15" r="12" fill="#8b5cf6" stroke="white" stroke-width="3"/>
                      <circle cx="15" cy="15" r="6" fill="white"/>
                    </svg>
                  `),
                  iconSize: [30, 30],
                  iconAnchor: [15, 15]
                })}
              />
            )}
          </MapContainer>

          {/* Loading Overlay */}
          {loading && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-10">
              <div className="bg-gray-800 p-6 rounded-lg flex items-center space-x-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                <span>Processing...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}