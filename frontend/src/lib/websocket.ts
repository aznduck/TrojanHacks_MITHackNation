import { useState, useEffect } from 'react';
import { AgentEvent } from './types';

export type WebSocketEventHandler = (event: AgentEvent) => void;
export type WebSocketStatusHandler = (status: 'connecting' | 'connected' | 'disconnected' | 'error') => void;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private eventHandlers: Set<WebSocketEventHandler> = new Set();
  private statusHandlers: Set<WebSocketStatusHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private isManualClose = false;

  constructor(url: string) {
    this.url = url;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    this.isManualClose = false;
    this.notifyStatus('connecting');

    try {
      this.ws = new WebSocket(this.url);
      this.setupEventListeners();
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.notifyStatus('error');
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.notifyStatus('disconnected');
  }

  onEvent(handler: WebSocketEventHandler): () => void {
    this.eventHandlers.add(handler);
    return () => this.eventHandlers.delete(handler);
  }

  onStatus(handler: WebSocketStatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.notifyStatus('connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const data: AgentEvent = JSON.parse(event.data);
        this.notifyEvent(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.ws = null;
      
      if (!this.isManualClose) {
        this.notifyStatus('disconnected');
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.notifyStatus('error');
    };
  }

  private scheduleReconnect(): void {
    if (this.isManualClose || this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached or manual close');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (!this.isManualClose) {
        this.connect();
      }
    }, delay);
  }

  private notifyEvent(event: AgentEvent): void {
    this.eventHandlers.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error('Error in event handler:', error);
      }
    });
  }

  private notifyStatus(status: 'connecting' | 'connected' | 'disconnected' | 'error'): void {
    this.statusHandlers.forEach(handler => {
      try {
        handler(status);
      } catch (error) {
        console.error('Error in status handler:', error);
      }
    });
  }

  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Hook for using WebSocket in React components
export function useWebSocket(url: string) {
  const [manager] = useState(() => new WebSocketManager(url));
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    const unsubscribeStatus = manager.onStatus(setStatus);
    const unsubscribeEvent = manager.onEvent((event) => {
      setEvents(prev => [...prev, event]);
    });

    manager.connect();

    return () => {
      unsubscribeStatus();
      unsubscribeEvent();
      manager.disconnect();
    };
  }, [manager]);

  return { status, events, manager };
}


