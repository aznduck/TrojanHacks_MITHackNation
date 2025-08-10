"use client";

import { useState, useEffect } from "react";
import { useDeploymentWebSocket } from "../lib/websocket";

// Agent outputs display component (copied from replay viewer)
const AgentOutputsDisplay = ({
  stage,
  outputs,
}: {
  stage: string;
  outputs: any;
}) => {
  const renderOutputValue = (key: string, value: any) => {
    if (typeof value === "string" && value.length > 100) {
      // Long strings - show in code block
      return (
        <div key={key} className="mb-3">
          <label className="block text-xs font-medium text-gray-600 mb-1">
            {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
          </label>
          <pre className="text-xs bg-gray-50 p-2 rounded border overflow-auto max-h-32 text-gray-800">
            {value}
          </pre>
        </div>
      );
    } else if (typeof value === "object" && value !== null) {
      // Objects - show as JSON
      return (
        <div key={key} className="mb-3">
          <label className="block text-xs font-medium text-gray-600 mb-1">
            {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
          </label>
          <pre className="text-xs bg-gray-50 p-2 rounded border overflow-auto max-h-32 text-gray-800">
            {JSON.stringify(value, null, 2)}
          </pre>
        </div>
      );
    } else if (typeof value === "boolean") {
      // Booleans - show as badges
      return (
        <div key={key} className="mb-2">
          <label className="text-xs font-medium text-gray-600 mr-2">
            {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}:
          </label>
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${
              value ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
            }`}
          >
            {value ? "Yes" : "No"}
          </span>
        </div>
      );
    } else if (value && typeof value === "string" && value.startsWith("http")) {
      // URLs - show as links
      return (
        <div key={key} className="mb-2">
          <label className="text-xs font-medium text-gray-600 mr-2">
            {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}:
          </label>
          <a
            href={value}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 text-sm underline"
          >
            {value}
          </a>
        </div>
      );
    } else {
      // Simple values
      return (
        <div key={key} className="mb-2">
          <label className="text-xs font-medium text-gray-600 mr-2">
            {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}:
          </label>
          <span className="text-sm text-gray-900">{String(value)}</span>
        </div>
      );
    }
  };

  return (
    <div className="space-y-2">
      {Object.entries(outputs)
        .filter(
          ([_, value]) => value !== null && value !== undefined && value !== ""
        )
        .map(([key, value]) => renderOutputValue(key, value))}
      {Object.keys(outputs).filter(
        (key) =>
          outputs[key] !== null &&
          outputs[key] !== undefined &&
          outputs[key] !== ""
      ).length === 0 && (
        <p className="text-sm text-gray-500 italic">
          No outputs available for this agent.
        </p>
      )}
    </div>
  );
};

interface DeploymentMonitorProps {
  initialDeploymentId?: string;
  autoStart?: boolean;
  showHeader?: boolean;
  className?: string;
}

export default function DeploymentMonitor({
  initialDeploymentId = "",
  autoStart = false,
  showHeader = true,
  className = ""
}: DeploymentMonitorProps) {
  const [deploymentId, setDeploymentId] = useState(initialDeploymentId || '');
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<any>(null);

  // Use the WebSocket hook for real-time updates
  const {
    events,
    agentOutputs,
    connectionStatus,
    connect,
    disconnect,
    clearEvents,
    isConnected,
  } = useDeploymentWebSocket(isMonitoring ? deploymentId : null);

  // Auto-start monitoring if requested
  useEffect(() => {
    if (autoStart && initialDeploymentId && !isMonitoring) {
      setDeploymentId(initialDeploymentId);
      setIsMonitoring(true);
      clearEvents();
    }
  }, [autoStart, initialDeploymentId, isMonitoring, clearEvents]);

  const handleEventClick = (event: any) => {
    setSelectedEvent(event);
  };

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
      case "connected":
        return "bg-green-500";
      case "connecting":
        return "bg-yellow-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const formatTimestamp = (ts: number) => {
    return new Date(ts).toLocaleTimeString();
  };

  const getEventIcon = (event: any) => {
    if (event.type === "status") {
      switch (event.stage) {
        case "clone":
          return "📥";
        case "architect":
          return "🏗️";
        case "deps":
          return "📦";
        case "tests":
          return "🧪";
        case "deployment":
          return "🚀";
        case "incident_monitor":
          return "👀";
        case "final":
          return event.status === "succeeded" ? "✅" : "❌";
        default:
          return "⚙️";
      }
    }
    return "📡";
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      {showHeader && (
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          🔴 Live Deployment Monitor
        </h2>
      )}

      {/* Connection Controls */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Monitor Deployment
        </h3>

        <div className="flex text-gray-900 items-center gap-4 mb-4">
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
            <span className="text-sm font-medium text-gray-900 capitalize">
              {connectionStatus}
            </span>
            <span className="text-sm text-gray-700">
              Monitoring: {deploymentId}
            </span>
            {connectionStatus === "error" && (
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
            <h3 className="text-lg font-semibold text-gray-900">
              Live Events ({events.length})
            </h3>
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
                  {isConnected ? "Connected and listening" : "Connecting..."}
                </p>
              </div>
            ) : (
              events.map((event, index) => (
                <div
                  key={index}
                  className={`bg-white border rounded p-3 text-sm shadow-sm cursor-pointer transition-colors hover:bg-gray-50 ${
                    selectedEvent === event ? "ring-2 ring-blue-500 bg-blue-50" : ""
                  }`}
                  onClick={() => handleEventClick(event)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getEventIcon(event)}</span>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          event.type === "status"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-purple-100 text-purple-800"
                        }`}
                      >
                        {event.type} - {event.stage}
                      </span>
                    </div>
                    <span className="text-gray-600 text-xs">
                      {formatTimestamp(event.ts)}
                    </span>
                  </div>

                  <p className="text-gray-800 mb-1">
                    {event.type === "status"
                      ? event.message
                      : event.type === "trace"
                      ? `${event.subtype} - ${
                          event.tool || event.model || "agent"
                        }`
                      : "Unknown event"}
                  </p>

                  {event.type === "status" && (event as any).status && (
                    <div className="flex items-center gap-2 mt-2">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          (event as any).status === "succeeded"
                            ? "bg-green-100 text-green-800"
                            : (event as any).status === "failed"
                            ? "bg-red-100 text-red-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
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

      {/* Event Details Section */}
      {selectedEvent && (
        <div className="bg-gray-50 rounded-lg p-4 mt-6">
          <div className="bg-white rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Event Details
            </h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Stage
                  </label>
                  <p className="text-sm text-gray-900">
                    {selectedEvent.stage}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type
                  </label>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {selectedEvent.type}
                    {selectedEvent.type === "trace" &&
                      selectedEvent.subtype &&
                      ` - ${selectedEvent.subtype}`}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message
                </label>
                <p className="text-sm text-gray-900">
                  {selectedEvent.type === "status"
                    ? selectedEvent.message
                    : selectedEvent.type === "trace"
                    ? `${selectedEvent.subtype} - ${
                        selectedEvent.tool || selectedEvent.model || "agent"
                      }`
                    : "Unknown event"}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Timestamp
                </label>
                <p className="text-sm text-gray-900">
                  {new Date(selectedEvent.ts * 1000).toLocaleString()}
                </p>
              </div>

              {/* Agent Outputs Section */}
              {agentOutputs && agentOutputs[selectedEvent.stage] && (
                <div className="border-t pt-4">
                  <label className="block text-sm font-medium text-gray-900 mb-3">
                    Agent Outputs ({selectedEvent.stage})
                    <span className="ml-2 text-xs text-green-600">🔴 Live</span>
                  </label>
                  <AgentOutputsDisplay
                    stage={selectedEvent.stage}
                    outputs={agentOutputs[selectedEvent.stage]}
                  />
                </div>
              )}

              <div className="border-t pt-4">
                <label className="block text-sm font-medium text-gray-900 mb-1">
                  Raw Event Data
                </label>
                <pre className="text-xs text-gray-900 bg-gray-100 p-3 rounded overflow-auto max-h-40">
                  {JSON.stringify(selectedEvent, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Show message when no event is selected */}
      {!selectedEvent && isMonitoring && events.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4 mt-6">
          <div className="bg-white rounded-lg p-6">
            <div className="text-center py-8 text-gray-500">
              <p>Click on an event above to view details and agent outputs.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
