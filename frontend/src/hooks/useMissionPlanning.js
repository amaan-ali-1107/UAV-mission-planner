import { useState, useCallback } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function useMissionPlanning() {
  const [waypoints, setWaypoints] = useState([]);
  const [optimizedRoute, setOptimizedRoute] = useState([]);
  const [missionData, setMissionData] = useState(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [missionSettings, setMissionSettings] = useState({
    batteryCapacity: 100,
    maxSpeed: 15,
    altitude: 100
  });

  const startPlanning = useCallback(() => {
    setIsPlanning(true);
    setWaypoints([]);
    setOptimizedRoute([]);
    setMissionData(null);
  }, []);

  const stopPlanning = useCallback(() => {
    setIsPlanning(false);
  }, []);

  const clearWaypoints = useCallback(() => {
    setWaypoints([]);
    setOptimizedRoute([]);
    setMissionData(null);
  }, []);

  const planMission = useCallback(async () => {
    if (waypoints.length < 2) {
      alert('Please add at least 2 waypoints to plan a mission');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/missions/plan`, {
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
  }, [waypoints, missionSettings]);

  return {
    waypoints,
    optimizedRoute,
    missionData,
    isPlanning,
    loading,
    missionSettings,
    setWaypoints,
    setIsPlanning,
    setMissionSettings,
    startPlanning,
    stopPlanning,
    clearWaypoints,
    planMission
  };
}
