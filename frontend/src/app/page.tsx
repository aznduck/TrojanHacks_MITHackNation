"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { HealthResponse } from "@/lib/types";
import DeploymentMonitor from "@/components/DeploymentMonitor";
import RecentDeployments from "@/components/RecentDeployments";

export default function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        setLoading(true);
        const healthData = await apiClient.getHealth();
        setHealth(healthData);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch health status"
        );
      } finally {
        setLoading(false);
      }
    };
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">AgentOps</h1>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-lg shadow mb-8 p-6">
          <h2 className="text-xl text-gray-900 font-semibold mb-4">
            System Status
          </h2>

          {loading && (
            <div className="flex items-center text-gray-700">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              Checking system health...
            </div>
          )}

          {error && (
            <div className="text-red-600 bg-red-50 p-3 rounded">
              Error: {error}
            </div>
          )}

          {health && (
            <div className="space-y-3">
              <div
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  health.ok
                    ? "bg-green-100 text-green-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                <div
                  className={`w-2 h-2 rounded-full mr-2 ${
                    health.ok ? "bg-green-500" : "bg-red-500"
                  }`}
                ></div>
                {health.ok ? "System Healthy" : "System Issues"}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mt-4">
                {Object.entries(health.env).map(([key, value]) => (
                  <div key={key} className="flex items-center space-x-2">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        value ? "bg-green-500" : "bg-gray-300"
                      }`}
                    ></div>
                    <span className="text-sm text-gray-800">{key}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Recent Deployments */}
        <RecentDeployments className="mb-8" />
      </div>
    </div>
  );
}
