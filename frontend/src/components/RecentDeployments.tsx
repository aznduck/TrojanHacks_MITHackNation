"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DeploymentInfo } from "@/lib/types";

// Mock data for recent deployments
const mockRecentDeployments: DeploymentInfo[] = [
  {
    deployment_id: "mock-success",
    status: "succeeded",
    created_at: Date.now() - 1000 * 60 * 30, // 30 minutes ago
    deployment_url: "https://app-deploy-001.vercel.app",
    events: [],
  },
  {
    deployment_id: "deploy-2024-002",
    status: "failed",
    created_at: Date.now() - 1000 * 60 * 60 * 2, // 2 hours ago
    deployment_url: undefined,
    events: [],
  },
  {
    deployment_id: "deploy-2024-003",
    status: "succeeded",
    created_at: Date.now() - 1000 * 60 * 60 * 4, // 4 hours ago
    deployment_url: "https://app-deploy-003.vercel.app",
    events: [],
  },
  {
    deployment_id: "deploy-2024-004",
    status: "running",
    created_at: Date.now() - 1000 * 60 * 60 * 6, // 6 hours ago
    deployment_url: undefined,
    events: [],
  },
  {
    deployment_id: "deploy-2024-005",
    status: "succeeded",
    created_at: Date.now() - 1000 * 60 * 60 * 24, // 1 day ago
    deployment_url: "https://app-deploy-005.vercel.app",
    events: [],
  },
];

interface RecentDeploymentsProps {
  className?: string;
}

export default function RecentDeployments({
  className = "",
}: RecentDeploymentsProps) {
  const [deployments, setDeployments] = useState<DeploymentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecentDeployments = async () => {
      try {
        setLoading(true);

        // TODO: Replace with actual API call
        // const response = await apiClient.getRecentDeployments();
        // setDeployments(response);

        // For now, use mock data
        await new Promise((resolve) => setTimeout(resolve, 500)); // Simulate API delay
        setDeployments(mockRecentDeployments);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to fetch recent deployments"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchRecentDeployments();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "succeeded":
        return "bg-green-100 text-green-800";
      case "failed":
        return "bg-red-100 text-red-800";
      case "running":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "succeeded":
        return "✅";
      case "failed":
        return "❌";
      case "running":
        return "🔄";
      default:
        return "⚪";
    }
  };

  const formatTimeAgo = (timestamp: number) => {
    const now = Date.now();
    const diffInSeconds = Math.floor((now - timestamp) / 1000);

    if (diffInSeconds < 60) {
      return `${diffInSeconds}s ago`;
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes}m ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours}h ago`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days}d ago`;
    }
  };

  const getSuccessRate = () => {
    if (deployments.length === 0) return 0;
    const succeeded = deployments.filter(
      (d) => d.status === "succeeded"
    ).length;
    return Math.round((succeeded / deployments.length) * 100);
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Recent Deployments
        </h2>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
          <span className="text-gray-600">Loading deployments...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Recent Deployments
        </h2>
        <div className="text-center py-8">
          <div className="text-red-500 text-2xl mb-2">⚠️</div>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Recent Deployments
        </h2>

        {/* Success Rate Badge */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => window.location.reload()}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium p-1 rounded hover:bg-blue-50 transition-colors"
            title="Refresh deployments"
          >
            🔄
          </button>
        </div>
      </div>

      {deployments.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          <div className="text-4xl mb-2">📭</div>
          <p>No recent deployments found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {deployments.map((deployment) => (
            <div
              key={deployment.deployment_id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="text-xl">
                  {getStatusIcon(deployment.status)}
                </div>

                <div>
                  <div className="flex items-center space-x-2">
                    <code className="text-sm font-mono bg-gray-100 text-gray-900 px-2 py-1 rounded">
                      {deployment.deployment_id}
                    </code>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                        deployment.status
                      )}`}
                    >
                      {deployment.status}
                    </span>
                  </div>

                  <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                    <span>{formatTimeAgo(deployment.created_at)}</span>

                    {deployment.deployment_url && (
                      <a
                        href={deployment.deployment_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 hover:underline"
                      >
                        View Live
                      </a>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {(deployment.status === "succeeded" ||
                  deployment.status === "failed") && (
                  <Link
                    href={`/replay/${deployment.deployment_id}`}
                    className="inline-flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  >
                    Replay
                  </Link>
                )}
                {deployment.status === "running" && (
                  <Link
                    href={`/monitor/${deployment.deployment_id}`}
                    className="inline-flex items-center px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                  >
                    Monitor
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
