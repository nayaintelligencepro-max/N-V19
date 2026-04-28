/**
 * NAYA Mobile — Network Manager
 * Handles connectivity, offline queuing, and API resilience
 */
import { Network } from '@capacitor/network';

export type NetworkStatus = 'online' | 'offline' | 'weak';

let currentStatus: NetworkStatus = 'online';
const offlineQueue: Array<{ url: string; options: RequestInit; resolve: Function; reject: Function }> = [];
const listeners: Array<(status: NetworkStatus) => void> = [];

/** Initialize network monitoring */
export async function initNetwork(): Promise<void> {
  const status = await Network.getStatus();
  currentStatus = status.connected ? 'online' : 'offline';

  Network.addListener('networkStatusChange', (status) => {
    const prev = currentStatus;
    currentStatus = status.connected ? 'online' : 'offline';
    if (prev !== currentStatus) {
      listeners.forEach(fn => fn(currentStatus));
      if (currentStatus === 'online') processOfflineQueue();
    }
  });
}

/** Subscribe to network changes */
export function onNetworkChange(fn: (status: NetworkStatus) => void): () => void {
  listeners.push(fn);
  return () => { const idx = listeners.indexOf(fn); if (idx !== -1) listeners.splice(idx, 1); };
}

/** Get current network status */
export function getNetworkStatus(): NetworkStatus {
  return currentStatus;
}

/** Resilient fetch — queues requests when offline */
export async function nayaFetch(url: string, options: RequestInit = {}): Promise<Response> {
  if (currentStatus === 'offline') {
    return new Promise((resolve, reject) => {
      offlineQueue.push({ url, options, resolve, reject });
    });
  }
  try {
    const response = await fetch(url, { ...options, signal: AbortSignal.timeout(15000) });
    return response;
  } catch (err) {
    currentStatus = 'offline';
    return new Promise((resolve, reject) => {
      offlineQueue.push({ url, options, resolve, reject });
    });
  }
}

async function processOfflineQueue(): Promise<void> {
  while (offlineQueue.length > 0) {
    const item = offlineQueue.shift();
    if (!item) continue;
    try {
      const response = await fetch(item.url, item.options);
      item.resolve(response);
    } catch (err) {
      item.reject(err);
    }
  }
}

export function getQueueSize(): number {
  return offlineQueue.length;
}
