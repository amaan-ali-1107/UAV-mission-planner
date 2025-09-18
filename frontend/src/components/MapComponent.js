import React from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Polygon, useMapEvents } from 'react-leaflet';
import L, { Icon } from 'leaflet';
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

export default function MapComponent({ 
  waypoints, 
  optimizedRoute, 
  isPlanning, 
  onMapClick,
  simulationData,
  simulationStep 
}) {
  // San Francisco center
  const mapCenter = [37.7749, -122.4194];

  const getCurrentSimulationPosition = () => {
    if (!simulationData || !simulationData.simulation_steps) return null;
    
    const step = simulationData.simulation_steps[simulationStep];
    return step ? step.position : null;
  };

  return (
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
      
      <MapClickHandler onMapClick={onMapClick} isPlanning={isPlanning} />

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
  );
}
