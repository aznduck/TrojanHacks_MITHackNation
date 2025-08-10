"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import DeploymentMonitor from "@/components/DeploymentMonitor";

export default function MonitorPage() {
  const params = useParams();
  const deploymentId = params.id as string;

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
                🔴 Live Deployment Monitor
              </h1>
              <p className="text-gray-600">
                Monitoring Deployment ID:{" "}
                <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                  {deploymentId}
                </code>
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Link
                href={`/replay/${deploymentId}`}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                🎬 View Replay
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Use the existing DeploymentMonitor component */}
        <DeploymentMonitor
          initialDeploymentId={deploymentId}
          autoStart={true}
          showHeader={false}
        />
      </div>
    </div>
  );
}
