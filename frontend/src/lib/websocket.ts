import { useState, useEffect, useRef } from 'react';
import { AgentEvent } from './types';

// Simple WebSocket hook for real-time deployment updates
export function useDeploymentWebSocket(deploymentId: string | null) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = () => {
    if (!deploymentId) return;
    
    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `ws://localhost:8000/ws/status?deployment_id=${deploymentId}`;
    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected for deployment:', deploymentId);
        setConnectionStatus('connected');
      };

      ws.onmessage = (event) => {
        try {
          const data: AgentEvent = JSON.parse(event.data);
          setEvents(prev => [...prev, data]);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        wsRef.current = null;
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionStatus('error');
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionStatus('disconnected');
  };

  const clearEvents = () => {
    setEvents([]);
  };

  // Auto-connect when deploymentId changes
  useEffect(() => {
    if (deploymentId) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [deploymentId]);

  return {
    events,
    connectionStatus,
    connect,
    disconnect,
    clearEvents,
    isConnected: connectionStatus === 'connected'
  };
}
