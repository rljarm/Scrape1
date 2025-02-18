import { useEffect, useRef, useState, useCallback } from 'react';
import config, { log } from '../config';

// CRITICAL: This hook manages WebSocket connections
// TODO(future): Add message queuing
// CHECK(periodic): Monitor connection stability

interface UseWebSocketReturn {
  sendMessage: (message: string) => void;
  lastMessage: string | null;
  readyState: number;
  reconnect: () => void;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutId = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url);
      log.debug('Creating WebSocket connection to:', url);

      ws.current.onopen = () => {
        log.info('WebSocket Connected');
        setReadyState(WebSocket.OPEN);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        log.debug('WebSocket message received:', event.data);
        setLastMessage(event.data);
      };

      ws.current.onclose = () => {
        log.warn('WebSocket Disconnected');
        setReadyState(WebSocket.CLOSED);

        // Attempt reconnection if within limits
        if (reconnectAttempts.current < config.performance.wsReconnectAttempts) {
          reconnectAttempts.current += 1;
          log.info(`Reconnecting... Attempt ${reconnectAttempts.current}`);
          
          reconnectTimeoutId.current = setTimeout(() => {
            connect();
          }, config.performance.wsReconnectInterval);
        } else {
          log.error('Max reconnection attempts reached');
        }
      };

      ws.current.onerror = (error) => {
        log.error('WebSocket Error:', error);
        setReadyState(WebSocket.CLOSED);
      };
    } catch (error) {
      log.error('Failed to create WebSocket connection:', error);
    }
  }, [url]);

  // Initial connection
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutId.current) {
        clearTimeout(reconnectTimeoutId.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  // Manual reconnect function
  const reconnect = useCallback(() => {
    log.info('Manual reconnection requested');
    if (ws.current) {
      ws.current.close();
    }
    reconnectAttempts.current = 0;
    connect();
  }, [connect]);

  // Send message function with logging
  const sendMessage = useCallback((message: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      log.debug('Sending WebSocket message:', message);
      ws.current.send(message);
    } else {
      log.error('Cannot send message - WebSocket is not connected');
      if (reconnectAttempts.current < config.performance.wsReconnectAttempts) {
        log.info('Attempting to reconnect before sending message...');
        reconnect();
      }
    }
  }, [reconnect]);

  return { sendMessage, lastMessage, readyState, reconnect };
};
