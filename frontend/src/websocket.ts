import type { ConnectionStatus } from './types';

let ws: WebSocket | null = null;
let pingInterval: ReturnType<typeof setInterval> | null = null;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let reconnectAttempts = 0;
let messageHandler: ((data: any) => void) | null = null;
let statusHandler: ((status: ConnectionStatus) => void) | null = null;
let onOpenCallback: (() => void) | null = null;

const MAX_RECONNECT_DELAY = 10000;

function getWSUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws`;
}

function cleanup() {
  if (pingInterval) {
    clearInterval(pingInterval);
    pingInterval = null;
  }
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }
}

function scheduleReconnect() {
  if (reconnectTimeout) return;
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
  reconnectAttempts++;
  statusHandler?.('connecting');
  reconnectTimeout = setTimeout(() => {
    reconnectTimeout = null;
    if (messageHandler) {
      connect(messageHandler, statusHandler, onOpenCallback);
    }
  }, delay);
}

function connect(
  onMessage: (data: any) => void,
  onStatus?: ((status: ConnectionStatus) => void) | null,
  onOpen?: (() => void) | null,
) {
  cleanup();
  if (ws) {
    ws.onclose = null;
    ws.onerror = null;
    ws.onmessage = null;
    ws.close();
    ws = null;
  }

  messageHandler = onMessage;
  statusHandler = onStatus ?? null;
  onOpenCallback = onOpen ?? null;
  statusHandler?.('connecting');

  const url = getWSUrl();
  ws = new WebSocket(url);

  ws.onopen = () => {
    reconnectAttempts = 0;
    statusHandler?.('connected');

    // Keepalive ping every 25s
    pingInterval = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 25000);

    onOpenCallback?.();
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      // Ignore pong responses
      if (data.type === 'pong') return;
      messageHandler?.(data);
    } catch {
      // Ignore non-JSON messages
    }
  };

  ws.onclose = () => {
    cleanup();
    ws = null;
    statusHandler?.('disconnected');
    scheduleReconnect();
  };

  ws.onerror = () => {
    // onclose will fire after onerror, so reconnect is handled there
  };
}

export function connectWS(
  onMessage: (data: any) => void,
  onStatus?: ((status: ConnectionStatus) => void) | null,
  onOpen?: (() => void) | null,
) {
  reconnectAttempts = 0;
  connect(onMessage, onStatus, onOpen);
}

export function sendWS(data: object) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

export function disconnectWS() {
  messageHandler = null;
  statusHandler = null;
  onOpenCallback = null;
  cleanup();
  if (ws) {
    ws.onclose = null;
    ws.close();
    ws = null;
  }
}
