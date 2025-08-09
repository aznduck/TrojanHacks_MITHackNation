// Core event types based on the backend structure
export interface BaseEvent {
  type: 'status' | 'trace';
  stage: string;
  ts: number;
  deployment_id?: string;
}

export interface StatusEvent extends BaseEvent {
  type: 'status';
  message: string;
  stage: 'clone' | 'architect' | 'deps' | 'tests' | 'deployment' | 'incident_monitor' | 'final' | 'replay';
  error?: string;
  workdir?: string;
  status?: 'running' | 'succeeded' | 'failed';
  deployment_url?: string;
}

export interface TraceEvent extends BaseEvent {
  type: 'trace';
  subtype: 'llm_start' | 'llm_end' | 'tool_start' | 'tool_end' | 'agent_delta';
  // LLM events
  model?: string;
  input?: string[];
  output?: string[];
  // Tool events
  tool?: string;
  // Agent delta events
  delta?: Record<string, any>;
}

export type AgentEvent = StatusEvent | TraceEvent;

// Deployment status
export interface DeploymentInfo {
  deployment_id: string;
  status: 'running' | 'succeeded' | 'failed';
  repo_url?: string;
  commit_sha?: string;
  deployment_url?: string;
  created_at: number;
  events: AgentEvent[];
}

// React Flow types
export interface FlowNode {
  id: string;
  type: 'agent' | 'tool' | 'llm';
  position: { x: number; y: number };
  data: {
    label: string;
    stage: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    event: AgentEvent;
    details?: any;
  };
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  data?: {
    context_change?: Record<string, any>;
  };
}

// Timeline types
export interface TimelineItem {
  id: string;
  timestamp: number;
  type: 'status' | 'trace';
  stage: string;
  message: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  event: AgentEvent;
}

// API response types
export interface HealthResponse {
  ok: boolean;
  env: Record<string, boolean>;
  hint: string;
}

export interface WebhookResponse {
  ok: boolean;
  deployment_id: string;
}
