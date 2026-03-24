// frontend/src/hooks/useWebSocket.ts
/**
 * Custom hook for WebSocket connection management.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { VideoProcessingStatus } from '../types';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onProcessingUpdate?: (update: VideoProcessingStatus) => void;
  onNotification?: (notification: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  const getWebSocketUrl = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.REACT_APP_WS_URL || 'localhost:8000';
    const token = localStorage.getItem('access_token');
    return `${protocol}//${host}/api/v1/ws/notifications?token=${token}`;
  };

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = getWebSocketUrl();
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      reconnectAttempts.current = 0;
      options.onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setLastMessage(message);
        
        // Handle different message types
        if (message.type === 'video_status') {
          options.onProcessingUpdate?.(message as VideoProcessingStatus);
        } else if (message.type === 'notification') {
          options.onNotification?.(message);
        }
        
        options.onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      options.onDisconnect?.();
      
      // Attempt to reconnect with exponential backoff
      if (reconnectAttempts.current < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, delay);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      options.onError?.(error);
    };
  }, [options]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const subscribeToVideo = useCallback((videoId: number) => {
    sendMessage({
      type: 'subscribe',
      video_id: videoId,
    });
  }, [sendMessage]);

  const unsubscribeFromVideo = useCallback((videoId: number) => {
    sendMessage({
      type: 'unsubscribe',
      video_id: videoId,
    });
  }, [sendMessage]);

  const sendPing = useCallback(() => {
    sendMessage({ type: 'ping' });
  }, [sendMessage]);

  useEffect(() => {
    connect();
    
    // Ping interval to keep connection alive
    const pingInterval = setInterval(() => {
      if (isConnected) {
        sendPing();
      }
    }, 30000);
    
    return () => {
      clearInterval(pingInterval);
      disconnect();
    };
  }, [connect, disconnect, sendPing, isConnected]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribeToVideo,
    unsubscribeFromVideo,
    sendPing,
  };
};