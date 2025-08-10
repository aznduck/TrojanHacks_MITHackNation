import { useState, useEffect, useCallback } from 'react';
import { apiClient } from './api';

export interface DeploymentEvent {
  type: string;
  stage: string;
  message: string;
  ts: number;
  deployment_id: string;
  agent_outputs?: any;
}

export interface UseDeploymentEventsResult {
  events: DeploymentEvent[];
  agentOutputs: Record<string, any>;
  isConnected: boolean;
  error: string | null;
  registerCallback: () => Promise<void>;
}

export function useDeploymentEvents(deploymentId: string | null): UseDeploymentEventsResult {
  const [events, setEvents] = useState<DeploymentEvent[]>([]);
  const [agentOutputs, setAgentOutputs] = useState<Record<string, any>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const registerCallback = useCallback(async () => {
    if (!deploymentId) return;
    
    try {
      const callbackUrl = `${window.location.origin}/api/agent-events`;
      await apiClient.registerCallback(deploymentId, callbackUrl);
      console.log('✅ Callback registered:', callbackUrl);
      setIsConnected(true);
      setError(null);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to register callback';
      console.error('❌ Failed to register callback:', errorMsg);
      setError(errorMsg);
      setIsConnected(false);
    }
  }, [deploymentId]);

  const pollEvents = useCallback(async () => {
    if (!deploymentId || isPolling) return;
    
    setIsPolling(true);
    try {
      const response = await apiClient.getEventsFromCallback(deploymentId);
      
      if (response.ok) {
        setEvents(response.events || []);
        setAgentOutputs(response.agent_outputs || {});
        setError(null);
      } else {
        setError('Failed to fetch events');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch events';
      setError(errorMsg);
    } finally {
      setIsPolling(false);
    }
  }, [deploymentId, isPolling]);

  // Auto-register callback when deploymentId changes
  useEffect(() => {
    if (deploymentId) {
      registerCallback();
    } else {
      setEvents([]);
      setAgentOutputs({});
      setIsConnected(false);
      setError(null);
    }
  }, [deploymentId, registerCallback]);

  // Poll for events every 2 seconds
  useEffect(() => {
    if (!deploymentId || !isConnected) return;

    const interval = setInterval(pollEvents, 2000);
    
    // Initial poll
    pollEvents();

    return () => clearInterval(interval);
  }, [deploymentId, isConnected, pollEvents]);

  return {
    events,
    agentOutputs,
    isConnected,
    error,
    registerCallback
  };
}
