// src/core/ws.js — WSStore réactif global V10
import observer from "./observer.js";

class WSStore {
  constructor() {
    this.state = observer.getState();
    this.subscribers = new Set();
    observer.subscribe(state => {
      this.state = state;
      this.subscribers.forEach(fn => fn(this.state));
    });
  }
  subscribe(fn) {
    this.subscribers.add(fn);
    fn(this.state);
    return () => this.subscribers.delete(fn);
  }
  getState() { return this.state; }
}

export const wsStore = new WSStore();
export default wsStore;

// Alias legacy — NOTE: use wsStore.getState() for a live snapshot;
// this getter ensures callers always get fresh state instead of a stale snapshot.
export const state = new Proxy({}, {
  get(_target, prop) { return wsStore.getState()[prop]; }
});
export function connectWS(statusEl) {
  observer.start();
  wsStore.subscribe(s => {
    const connected = Object.values(s.sources).filter(x => x.status === "CONNECTED").length;
    const total = Object.keys(s.sources).length;
    if (statusEl) {
      statusEl.textContent = connected > 0 ? `⚡ ${connected}/${total} WS` : "⏳ INIT";
      statusEl.style.color = connected >= 3 ? "#00ff88" : connected > 0 ? "#ffaa00" : "#ff4444";
    }
  });
}
