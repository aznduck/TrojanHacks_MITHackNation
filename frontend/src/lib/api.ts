import { AgentEvent, HealthResponse, DeploymentInfo, WebhookResponse } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Response types for new endpoints
export interface ReplayBroadcastResponse {
  ok: boolean;
  replayed: number;
  speed: number;
}

export interface SandboxReplayResponse {
  ok: boolean;
  deployment_id: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // Health check endpoint
  async getHealth(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  // Get replay events for a deployment
  async getReplayEvents(deploymentId: string): Promise<AgentEvent[]> {
    const response = await fetch(`${this.baseUrl}/replay/${deploymentId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch replay events: ${response.statusText}`);
    }
    return response.json();
  }

  // Trigger GitHub webhook (for testing purposes)
  async triggerWebhook(payload: any): Promise<WebhookResponse> {
    const response = await fetch(`${this.baseUrl}/webhook/github`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Note: In production, this would need proper GitHub signature
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Webhook trigger failed: ${response.statusText}`);
    }
    return response.json();
  }

  // Replay broadcast with speed control
  async replayBroadcast(deploymentId: string, speed: number = 1.0): Promise<ReplayBroadcastResponse> {
    const response = await fetch(`${this.baseUrl}/replay/${deploymentId}/broadcast?speed=${speed}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error(`Replay broadcast failed: ${response.statusText}`);
    }
    return response.json();
  }

  // Sandbox replay - deterministic replay using recorded data
  async sandboxReplay(deploymentId: string): Promise<SandboxReplayResponse> {
    const response = await fetch(`${this.baseUrl}/replay/${deploymentId}/sandbox`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error(`Sandbox replay failed: ${response.statusText}`);
    }
    return response.json();
  }

  // Process raw events into structured deployment info
  async getDeploymentInfo(deploymentId: string): Promise<DeploymentInfo> {
    const events = await this.getReplayEvents(deploymentId);
    
    // Extract deployment metadata from events
    const firstEvent = events[0];
    const finalEvent = events.find(e => e.type === 'status' && e.stage === 'final');
    
    let status: 'running' | 'succeeded' | 'failed' = 'running';
    let deployment_url: string | undefined;
    let repo_url: string | undefined;
    let commit_sha: string | undefined;

    if (finalEvent && finalEvent.type === 'status') {
      status = (finalEvent as any).status || 'running';
      deployment_url = (finalEvent as any).deployment_url;
    }

    // Try to extract repo info from clone events
    const cloneEvent = events.find(e => e.type === 'status' && e.stage === 'clone');
    if (cloneEvent && cloneEvent.type === 'status') {
      // These would be in the context in a real implementation
      // For now, we'll leave them undefined
    }

    return {
      deployment_id: deploymentId,
      status,
      deployment_url,
      created_at: firstEvent?.ts || Date.now(),
      events,
      repo_url,
      commit_sha,
    };
  }

  // Get WebSocket URL for real-time updates
  getWebSocketUrl(deploymentId: string): string {
    const wsProtocol = this.baseUrl.startsWith('https') ? 'wss' : 'ws';
    const wsBaseUrl = this.baseUrl.replace(/^https?/, wsProtocol);
    return `${wsBaseUrl}/ws/status?deployment_id=${deploymentId}`;
  }

  // Helper method to check if deployment exists
  async deploymentExists(deploymentId: string): Promise<boolean> {
    try {
      const events = await this.getReplayEvents(deploymentId);
      return events.length > 0;
    } catch {
      return false;
    }
  }
}

// Default API client instance
export const apiClient = new ApiClient();

// Utility functions for event processing
export function processEventsToTimeline(events: AgentEvent[]) {
  return events
    .map((event, index) => ({
      id: `${event.ts}-${index}`,
      timestamp: event.ts,
      type: event.type,
      stage: event.stage,
      message: event.type === 'status' ? (event as any).message : `${event.stage} - ${(event as any).subtype}`,
      status: getEventStatus(event),
      event,
    }))
    .sort((a, b) => a.timestamp - b.timestamp);
}

export function getEventStatus(event: AgentEvent): 'pending' | 'running' | 'completed' | 'failed' {
  if (event.type === 'status') {
    const statusEvent = event as any;
    if (statusEvent.error) return 'failed';
    if (statusEvent.status === 'failed') return 'failed';
    if (statusEvent.status === 'succeeded') return 'completed';
    if (statusEvent.message?.toLowerCase().includes('starting')) return 'running';
    if (statusEvent.message?.toLowerCase().includes('completed')) return 'completed';
    return 'running';
  }
  
  if (event.type === 'trace') {
    const traceEvent = event as any;
    if (traceEvent.subtype?.includes('end')) return 'completed';
    if (traceEvent.subtype?.includes('start')) return 'running';
    return 'running';
  }
  
  return 'pending';
}
