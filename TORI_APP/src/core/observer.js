// src/core/observer.js — TORI V10 — Observer multi-sources avec reconnexion auto
import { SOURCES } from "./sources.js";

class Observer {
  constructor() {
    this.state = {
      sources: {},
      lastEvent: null,
      events: [],          // buffer 200 derniers events
      systemStatus: null,  // snapshot /status
      updatedAt: null
    };
    this.listeners = new Set();

    Object.values(SOURCES).forEach(s => {
      this.state.sources[s.id] = {
        status: "DISCONNECTED",
        lastSeen: null,
        lastMessage: null
      };
    });
  }

  start() {
    Object.values(SOURCES).forEach(src => this._connect(src));
    // Polling /status toutes les 15s pour la vue System
    this._pollStatus();
  }

  async _pollStatus() {
    while (true) {
      try {
        const r = await fetch("/status");
        if (r.ok) {
          this.state.systemStatus = await r.json();
          this._emit();
        }
      } catch (e) {}
      await new Promise(res => setTimeout(res, 15000));
    }
  }

  subscribe(fn) {
    this.listeners.add(fn);
    fn(this.getState());
  }

  getState() {
    return JSON.parse(JSON.stringify(this.state));
  }

  _emit() {
    this.state.updatedAt = Date.now();
    this.listeners.forEach(fn => fn(this.getState()));
  }

  _connect(source) {
    const ws = new WebSocket(source.url);
    const id = source.id;

    this.state.sources[id].status = "CONNECTING";
    this._emit();

    ws.onopen = () => {
      this.state.sources[id].status = "CONNECTED";
      this.state.sources[id].lastSeen = Date.now();
      this._emit();
    };

    ws.onmessage = e => {
      this.state.sources[id].lastSeen = Date.now();
      this.state.sources[id].lastMessage = e.data;

      // Parser le payload
      let parsed = null;
      try { parsed = JSON.parse(e.data); } catch (_) { parsed = { raw: e.data }; }

      const event = {
        source: id,
        payload: parsed,
        raw: e.data,
        timestamp: Date.now()
      };

      this.state.lastEvent = event;

      // Buffer events (200 max)
      this.state.events.unshift(event);
      if (this.state.events.length > 200) this.state.events = this.state.events.slice(0, 200);

      // Si c'est un snapshot system (ObsBus)
      if (parsed && parsed.payload && parsed.payload.type === "snapshot") {
        this.state.systemStatus = parsed.payload.data;
      }

      this._emit();
    };

    ws.onerror = () => {
      this.state.sources[id].status = "ERROR";
      this._emit();
    };

    ws.onclose = () => {
      this.state.sources[id].status = "DISCONNECTED";
      this._emit();
      setTimeout(() => this._connect(source), 3000);
    };
  }
}

export const observer = new Observer();
export default observer;
