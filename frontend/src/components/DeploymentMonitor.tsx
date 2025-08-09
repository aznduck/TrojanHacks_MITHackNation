'use client';

import { useState } from 'react';
import { useDeploymentWebSocket } from '../lib/websocket';

export default function DeploymentMonitor() {
  const [deploymentId, setDeploymentId] = useState<string>('');
  const [isMonitoring, setIsMonitoring] = useState(false);

  // Use the WebSocket hook for real-time updates
  const { 
    events, 
    connectionStatus, 
    connect, 
    disconnect, 
    clearEvents, 
    isConnected 
  } = useDeploymentWebSocket(isMonitoring ? deploymentId : null);

  const startMonitoring = () => {
    if (!deploymentId.trim()) return;
    setIsMonitoring(true);
    clearEvents();
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
    disconnect();
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const formatTimestamp = (ts: number) => {
    return new Date(ts).toLocaleTimeString();
  };

  const getEventIcon = (event: any) => {
    if (event.type === 'status') {
      switch (event.stage) {
        case 'clone': return '📥';
        case 'architect': return '🏗️';
        case 'deps': return '📦';
        case 'tests': return '🧪';
        case 'deployment': return '🚀';
        case 'incident_monitor': return '👀';
        case 'final': return event.status === 'succeeded' ? '✅' : '❌';
        default: return '⚙️';
      }
    }
    return '📡';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">🔴 Live Deployment Monitor</h2>
      
      {/* Connection Controls */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Monitor Deployment</h3>
        
        <div className="flex items-center gap-4 mb-4">
          <input
            type="text"
            value={deploymentId}
            onChange={(e) => setDeploymentId(e.target.value)}
            placeholder="Enter deployment ID (e.g., abc123-def456)"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isMonitoring}
          />
          
          {!isMonitoring ? (
            <button
              onClick={startMonitoring}
              disabled={!deploymentId.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Start Monitoring
            </button>
          ) : (
            <button
              onClick={stopMonitoring}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Stop Monitoring
            </button>
          )}
        </div>

        {/* Connection Status */}
        {isMonitoring && (
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
            <span className="text-sm font-medium text-gray-900 capitalize">{connectionStatus}</span>
            <span className="text-sm text-gray-700">
              Monitoring: {deploymentId}
            </span>
            {connectionStatus === 'error' && (
              <span className="text-sm text-red-600 ml-2">
                ⚠️ Check if backend is running on localhost:8000
              </span>
            )}
          </div>
        )}
      </div>

      {/* Real-time Events */}
      {isMonitoring && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Live Events ({events.length})</h3>
            <button
              onClick={clearEvents}
              className="px-3 py-1 text-sm bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
            >
              Clear
            </button>
          </div>
          
          <div className="max-h-96 overflow-y-auto space-y-2">
            {events.length === 0 ? (
              <div className="text-center py-8 text-gray-600">
                <div className="text-2xl mb-2">⏳</div>
                <p className="text-gray-800">Waiting for events...</p>
                <p className="text-sm mt-1 text-gray-600">
                  {isConnected ? 'Connected and listening' : 'Connecting...'}
                </p>
              </div>
            ) : (
              events.map((event, index) => (
                <div key={index} className="bg-white border rounded p-3 text-sm shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getEventIcon(event)}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        event.type === 'status' ? 'bg-blue-100 text-blue-800' :
                        'bg-purple-100 text-purple-800'
                      }`}>
                        {event.type} - {event.stage}
                      </span>
                    </div>
                    <span className="text-gray-600 text-xs">
                      {formatTimestamp(event.ts)}
                    </span>
                  </div>
                  
                  <p className="text-gray-800 mb-1">
                    {event.type === 'status' ? event.message : 
                     event.type === 'trace' ? `${event.subtype} - ${event.tool || event.model || 'agent'}` :
                     'Unknown event'}
                  </p>
                  
                  {event.type === 'status' && (event as any).status && (
                    <div className="flex items-center gap-2 mt-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        (event as any).status === 'succeeded' ? 'bg-green-100 text-green-800' :
                        (event as any).status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {(event as any).status}
                      </span>
                      
                      {(event as any).deployment_url && (
                        <a 
                          href={(event as any).deployment_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-700 hover:underline text-xs font-medium"
                        >
                          🔗 View Deployment
                        </a>
                      )}
                    </div>
                  )}
                  
                  {(event as any).error && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                      <p className="text-red-800 text-xs">
                        <strong>Error:</strong> {(event as any).error}
                      </p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
