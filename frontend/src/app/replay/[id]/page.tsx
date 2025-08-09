"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiClient, processEventsToTimeline } from "@/lib/api";
import { DeploymentInfo, TimelineItem } from "@/lib/types";

export default function ReplayViewer() {
  const params = useParams();
  const deploymentId = params.id as string;

  const [deployment, setDeployment] = useState<DeploymentInfo | null>(null);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<TimelineItem | null>(null);

  useEffect(() => {
    const fetchDeployment = async () => {
      try {
        setLoading(true);
        const deploymentData = await apiClient.getDeploymentInfo(deploymentId);
        setDeployment(deploymentData);

        const timelineData = processEventsToTimeline(deploymentData.events);
        setTimeline(timelineData);

        // Auto-select first event
        if (timelineData.length > 0) {
          setSelectedEvent(timelineData[0]);
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Timeline */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg text-gray-900 font-semibold mb-4">
                Timeline
              </h2>

              {timeline.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                  <p>No events found for this deployment.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {timeline.map((item, index) => (
                    <div
                      key={item.id}
                      className={`cursor-pointer p-3 rounded-lg border transition-colors ${
                        selectedEvent?.id === item.id
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                      }`}
                      onClick={() => setSelectedEvent(item)}
                    >
                      <div className="flex items-center space-x-3">
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold ${getStatusColor(
                            item.status
                          )}`}
                        >
                          {getStatusIcon(item.status)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {item.stage}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {item.message}
                          </p>
                          <p className="text-xs text-gray-400">
                            {new Date(
                              item.timestamp * 1000
                            ).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Event Details */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg text-gray-900 font-semibold mb-4">
                Event Details
              </h2>

              {selectedEvent ? (
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
                        Status
                      </label>
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          selectedEvent.status === "completed"
                            ? "bg-green-100 text-green-800"
                            : selectedEvent.status === "running"
                            ? "bg-blue-100 text-blue-800"
                            : selectedEvent.status === "failed"
                            ? "bg-red-100 text-red-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {selectedEvent.status}
                      </span>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Timestamp
                      </label>
                      <p className="text-sm text-gray-900">
                        {new Date(
                          selectedEvent.timestamp * 1000
                        ).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Type
                      </label>
                      <p className="text-sm text-gray-900">
                        {selectedEvent.type}
                      </p>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Message
                    </label>
                    <p className="text-sm text-gray-900">
                      {selectedEvent.message}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Raw Event Data
                    </label>
                    <pre className="bg-gray-100 p-4 rounded-lg text-xs overflow-x-auto">
                      {JSON.stringify(selectedEvent.event, null, 2)}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="text-gray-500 text-center py-8">
                  <p>Select an event from the timeline to view details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
