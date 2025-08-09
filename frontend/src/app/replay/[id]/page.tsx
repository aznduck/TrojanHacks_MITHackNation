"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { DeploymentInfo, AgentEvent } from "@/lib/types";
import ReactFlowTimeline from "@/components/ReactFlowTimeline";
import ReplayControls from "@/components/ReplayControls";
import {
  mockTimelineEvents,
  mockFailedTimelineEvents,
} from "@/lib/mock-timeline-data";

export default function ReplayViewer() {
  const params = useParams();
  const deploymentId = params.id as string;

  const [deployment, setDeployment] = useState<DeploymentInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<AgentEvent | null>(null);
  const [currentEventIndex, setCurrentEventIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    const fetchDeployment = async () => {
      try {
        setLoading(true);

        let events: AgentEvent[];

        // Use mock data for testing
        if (
          deploymentId === "mock-success" ||
          deploymentId === "sample-deployment-123"
        ) {
          events = mockTimelineEvents;
        } else if (deploymentId === "mock-failed") {
          events = mockFailedTimelineEvents;
        } else {
          // Try to fetch real data, fallback to mock on error
          try {
            events = await apiClient.getReplayEvents(deploymentId);
          } catch {
            events = mockTimelineEvents; // Fallback to mock data
          }
        }

        // Determine status from events
        const finalEvent = events.find((e) => e.stage === "final");
        const status =
          finalEvent && "status" in finalEvent
            ? (finalEvent as any).status || "succeeded"
            : "succeeded";

        const deploymentData: DeploymentInfo = {
          deployment_id: deploymentId,
          status: status as "running" | "succeeded" | "failed",
          created_at: Date.now(),
          events,
        };
        setDeployment(deploymentData);

        // Auto-select first event
        if (events.length > 0) {
          setSelectedEvent(events[0]);
          setCurrentEventIndex(0);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch deployment data"
        );
      } finally {
        setLoading(false);
      }
    };

    if (deploymentId) {
      fetchDeployment();
    }
  }, [deploymentId]);

  // Sync selected event with current replay index
  useEffect(() => {
    if (deployment?.events && currentEventIndex >= 0 && currentEventIndex < deployment.events.length) {
      setSelectedEvent(deployment.events[currentEventIndex]);
    }
  }, [currentEventIndex, deployment?.events]);

  // Handle event index changes from replay controls
  const handleEventIndexChange = (index: number) => {
    setCurrentEventIndex(index);
  };

  // Handle play state changes
  const handlePlayStateChange = (playing: boolean) => {
    setIsPlaying(playing);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500";
      case "running":
        return "bg-blue-500";
      case "failed":
        return "bg-red-500";
      default:
        return "bg-gray-400";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return "✓";
      case "running":
        return "⟳";
      case "failed":
        return "✗";
      default:
        return "○";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading deployment replay...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-4xl mb-4">⚠️</div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            Error Loading Replay
          </h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <Link
            href="/"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <Link
                href="/"
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                ← Back to Dashboard
              </Link>
              <h1 className="text-2xl font-bold text-gray-900 mt-2">
                Deployment Replay
              </h1>
              <p className="text-gray-600">
                Deployment ID:{" "}
                <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                  {deploymentId}
                </code>
              </p>
            </div>

            {deployment && (
              <div className="text-right">
                <div
                  className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    deployment.status === "succeeded"
                      ? "bg-green-100 text-green-800"
                      : deployment.status === "failed"
                      ? "bg-red-100 text-red-800"
                      : "bg-blue-100 text-blue-800"
                  }`}
                >
                  {deployment.status.charAt(0).toUpperCase() +
                    deployment.status.slice(1)}
                </div>
                {deployment.deployment_url && (
                  <div className="mt-2">
                    <a
                      href={deployment.deployment_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      View Deployment →
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Replay Controls */}
        <ReplayControls
          events={deployment?.events || []}
          currentEventIndex={currentEventIndex}
          onEventIndexChange={handleEventIndexChange}
          onPlayStateChange={handlePlayStateChange}
          className="mb-6"
        />

        {/* Full-width Timeline Section */}
        <div className="mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <ReactFlowTimeline
              events={deployment?.events || []}
              onEventSelect={setSelectedEvent}
              selectedEvent={selectedEvent}
              currentEventIndex={currentEventIndex}
              isPlaying={isPlaying}
            />
          </div>
        </div>

        {/* Event Details Section */}
        {selectedEvent && (
          <div className="mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl text-gray-900 font-semibold mb-6">
                Event Details
              </h2>
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
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Timestamp
                    </label>
                    <p className="text-sm text-gray-900">
                      {new Date(selectedEvent.ts * 1000).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Deployment ID
                    </label>
                    <p className="text-sm text-gray-900">
                      {selectedEvent.deployment_id || "N/A"}
                    </p>
                  </div>
                </div>

                {selectedEvent.type === "status" &&
                  "message" in selectedEvent && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Message
                      </label>
                      <p className="text-sm text-gray-900">
                        {selectedEvent.message}
                      </p>
                    </div>
                  )}

                {selectedEvent.type === "trace" && (
                  <div className="space-y-2">
                    {"model" in selectedEvent && selectedEvent.model && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Model
                        </label>
                        <p className="text-sm text-gray-900">
                          {selectedEvent.model}
                        </p>
                      </div>
                    )}
                    {"tool" in selectedEvent && selectedEvent.tool && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Tool
                        </label>
                        <p className="text-sm text-gray-900">
                          {selectedEvent.tool}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                <div>
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
        {!selectedEvent && (
          <div className="mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-center py-8 text-gray-500">
                <p>Select an event from the timeline above to view details.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
