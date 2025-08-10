"use client";

import { useState, useEffect } from "react";
import { useDeploymentEvents } from "@/lib/useDeploymentEvents";

// Agent outputs display component
const AgentOutputsDisplay = ({
  stage,
  outputs,
}: {
  stage: string;
  outputs: any;
}) => {
  const renderOutputValue = (key: string, value: any) => {
    if (typeof value === "string" && value.length > 100) {
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
    } else {
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

export default function DeploymentMonitorHTTP({
  initialDeploymentId = "",
  autoStart = false,
  showHeader = true,
  className = "",
}: DeploymentMonitorProps) {
  const [deploymentId, setDeploymentId] = useState(initialDeploymentId || "");
  const [isMonitoring, setIsMonitoring] = useState(autoStart);
  const [selectedEvent, setSelectedEvent] = useState<any>(null);

  // Use HTTP events hook for real-time events
  const { events, agentOutputs, isConnected, error } = useDeploymentEvents(
    isMonitoring ? deploymentId : null
  );

  // Debug logging for agent outputs
  useEffect(() => {
    console.log('🔍 DeploymentMonitor - Agent Outputs Updated:', {
      deploymentId,
      agentOutputs,
      agentOutputsKeys: Object.keys(agentOutputs || {}),
      eventsCount: events.length
    });
  }, [agentOutputs, deploymentId, events.length]);

  // Auto-start monitoring if requested
  useEffect(() => {
    if (autoStart && initialDeploymentId) {
      setIsMonitoring(true);
    }
  }, [autoStart, initialDeploymentId]);

  const handleEventClick = (event: any) => {
    setSelectedEvent(event);
  };

  const startMonitoring = () => {
    if (deploymentId.trim()) {
      setIsMonitoring(true);
      setSelectedEvent(null);
    }
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
  };

  const getStatusColor = () => {
    if (error) return "text-red-600";
    if (isConnected) return "text-green-600";
    return "text-yellow-600";
  };

  const formatTimestamp = (ts: number) => {
    return new Date(ts * 1000).toLocaleTimeString();
  };

  const getEventIcon = (event: any) => {
    switch (event.type) {
      case "status":
        return "📊";
      case "trace":
        return "🔍";
      case "error":
        return "❌";
      default:
        return "📝";
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {showHeader && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            🔴 Live Deployment Monitor (HTTP)
          </h2>

          <div className="flex gap-4 items-end mb-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Deployment ID
              </label>
              <input
                type="text"
                value={deploymentId}
                onChange={(e) => setDeploymentId(e.target.value)}
                placeholder="Enter deployment ID to monitor..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isMonitoring}
              />
            </div>
            <div>
              {!isMonitoring ? (
                <button
                  onClick={startMonitoring}
                  disabled={!deploymentId.trim()}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Start Monitoring
                </button>
              ) : (
                <button
                  onClick={stopMonitoring}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                >
                  Stop Monitoring
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? "bg-green-500" : "bg-red-500"
                }`}
              ></div>
              <span className={getStatusColor()}>
                {error
                  ? `Error: ${error}`
                  : isConnected
                  ? "Connected (HTTP Polling)"
                  : "Disconnected"}
              </span>
            </div>
            {isMonitoring && (
              <div className="text-gray-600">
                Monitoring:{" "}
                <span className="font-mono text-sm">{deploymentId}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Events List */}
      {isMonitoring && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Live Events ({events.length})
            </h3>
            <div className="text-sm text-gray-500">
              Updates every 2 seconds via HTTP polling
            </div>
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {events.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>
                  No events yet. Events will appear here as the deployment
                  progresses...
                </p>
              </div>
            ) : (
              events.map((event, index) => (
                <div
                  key={index}
                  onClick={() => handleEventClick(event)}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedEvent === event
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <span className="text-lg">{getEventIcon(event)}</span>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-gray-900">
                            {event.stage}
                          </span>
                          <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            {event.type}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{event.message}</p>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatTimestamp(event.ts)}
                    </div>
                  </div>

                  {/* Show agent outputs indicator if available */}
                  {agentOutputs && agentOutputs[event.stage] && (
                    <div className="mt-2 text-xs text-green-600">
                      🔴 Agent outputs available
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
        <div className="bg-gray-50 rounded-lg p-4">
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
                  <p className="text-sm text-gray-900">{selectedEvent.stage}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type
                  </label>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {selectedEvent.type}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message
                </label>
                <p className="text-sm text-gray-900">{selectedEvent.message}</p>
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
              {(() => {
                const stageOutputs = agentOutputs?.[selectedEvent.stage];
                console.log('🎯 Event Details - Agent Outputs Check:', {
                  selectedStage: selectedEvent.stage,
                  hasAgentOutputs: !!agentOutputs,
                  availableStages: Object.keys(agentOutputs || {}),
                  stageOutputs,
                  hasStageOutputs: !!stageOutputs
                });
                
                if (stageOutputs) {
                  return (
                    <div className="border-t pt-4">
                      <label className="block text-sm font-medium text-gray-900 mb-3">
                        Agent Outputs ({selectedEvent.stage})
                        <span className="ml-2 text-xs text-green-600">🔴 Live</span>
                      </label>
                      <AgentOutputsDisplay
                        stage={selectedEvent.stage}
                        outputs={stageOutputs}
                      />
                    </div>
                  );
                } else {
                  return (
                    <div className="border-t pt-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Agent Outputs ({selectedEvent.stage})
                      </label>
                      <p className="text-sm text-gray-500 italic">
                        No agent outputs available for this stage yet.
                        {agentOutputs && Object.keys(agentOutputs).length > 0 && (
                          <span className="block mt-1">
                            Available stages: {Object.keys(agentOutputs).join(', ')}
                          </span>
                        )}
                      </p>
                    </div>
                  );
                }
              })()}

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
        <div className="bg-gray-50 rounded-lg p-4">
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
