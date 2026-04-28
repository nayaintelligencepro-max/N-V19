"""
NAYA V20 — Decision Graph Engine
══════════════════════════════════════════════════════════════════════════════
Maps OT decision-maker networks to find introduction paths.

DOCTRINE:
  A cold email converts at ~2%.  An introduced email converts at ~35%.
  This engine maps the professional graph of OT decision-makers so NAYA
  always finds the warmest possible path to each target.

ALGORITHM:
  Bidirectional BFS on a weighted adjacency list.
  Nodes  = persons (RSSI, DSI, CTO, Directeur Ops …)
  Edges  = professional connections with strength [0..1]
  Bridge = person connected to ≥ N unique companies

OUTPUT:
  Introduction paths sorted by accumulated strength.
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.DECISION_GRAPH")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "decision_graph_engine.json"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


class DecisionGraphEngine:
    """
    Maintains a weighted professional graph of OT decision-makers and finds
    optimal introduction paths between any two nodes.

    Storage format:
        {
          "persons": {person_id: {name, role, company, sector, linkedin_url, added_at}},
          "connections": [[id_a, id_b, strength, type], ...]
        }
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._persons: Dict[str, Dict] = {}
        # connections stored as list of [id_a, id_b, strength, type]
        self._connections: List[List] = []
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._persons = data.get("persons", {})
                    self._connections = data.get("connections", [])
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "persons": self._persons,
                        "connections": self._connections,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Graph operations
    # ──────────────────────────────────────────────────────────────────────

    def add_person(
        self,
        person_id: str,
        name: str,
        role: str,
        company: str,
        sector: str,
        linkedin_url: str = "",
    ) -> str:
        """
        Register a decision-maker in the graph.

        Args:
            person_id: Unique identifier (e.g. sha256 of name+company).
            name: Full name.
            role: Job title (e.g. "RSSI", "DSI").
            company: Employer name.
            sector: Industry sector.
            linkedin_url: Optional LinkedIn profile URL.

        Returns:
            person_id as stored.
        """
        with self._lock:
            self._persons[person_id] = {
                "name": name,
                "role": role,
                "company": company,
                "sector": sector,
                "linkedin_url": linkedin_url,
                "added_at": datetime.now(timezone.utc).isoformat(),
            }
        self._save()
        return person_id

    def add_connection(
        self,
        person_id_a: str,
        person_id_b: str,
        strength: float = 0.5,
        connection_type: str = "professional",
    ) -> bool:
        """
        Add a bidirectional edge between two persons.

        Args:
            person_id_a: Source person ID.
            person_id_b: Target person ID.
            strength: Edge weight in [0..1]; higher = warmer relationship.
            connection_type: Relationship label ("professional", "alumni", etc.).

        Returns:
            True if both persons exist and the connection was stored, False otherwise.
        """
        with self._lock:
            if person_id_a not in self._persons or person_id_b not in self._persons:
                return False
            # Avoid duplicates
            for conn in self._connections:
                if {conn[0], conn[1]} == {person_id_a, person_id_b}:
                    conn[2] = max(conn[2], strength)
                    self._save()
                    return True
            self._connections.append([person_id_a, person_id_b, strength, connection_type])
        self._save()
        return True

    def find_bridges(self, min_connections: int = 3) -> List[Dict]:
        """
        Find super-connectors: persons linked to >= min_connections unique companies.

        Args:
            min_connections: Minimum unique-company degree to qualify as bridge.

        Returns:
            List of dicts with person_id, name, company, bridge_score, connections.
        """
        adjacency: Dict[str, List[str]] = {}
        with self._lock:
            for conn in self._connections:
                adjacency.setdefault(conn[0], []).append(conn[1])
                adjacency.setdefault(conn[1], []).append(conn[0])

        bridges = []
        for pid, neighbours in adjacency.items():
            person = self._persons.get(pid)
            if person is None:
                continue
            unique_companies = {
                self._persons[n]["company"]
                for n in neighbours
                if n in self._persons and self._persons[n]["company"] != person["company"]
            }
            if len(unique_companies) >= min_connections:
                bridges.append({
                    "person_id": pid,
                    "name": person["name"],
                    "company": person["company"],
                    "bridge_score": len(unique_companies),
                    "connections": len(neighbours),
                })
        bridges.sort(key=lambda x: x["bridge_score"], reverse=True)
        return bridges

    def get_intro_path(self, from_person_id: str, to_company: str) -> List[Dict]:
        """
        BFS shortest path from a person to any decision-maker at a target company.

        Args:
            from_person_id: Starting node.
            to_company: Name of the destination company.

        Returns:
            Ordered list of person dicts representing the introduction chain.
            Empty list if no path found.
        """
        with self._lock:
            persons = dict(self._persons)
            connections = list(self._connections)

        adjacency: Dict[str, List[str]] = {}
        for conn in connections:
            adjacency.setdefault(conn[0], []).append(conn[1])
            adjacency.setdefault(conn[1], []).append(conn[0])

        if from_person_id not in persons:
            return []

        visited = {from_person_id}
        queue: deque = deque([[from_person_id]])

        while queue:
            path = queue.popleft()
            current = path[-1]
            for neighbour in adjacency.get(current, []):
                if neighbour in visited:
                    continue
                visited.add(neighbour)
                new_path = path + [neighbour]
                person = persons.get(neighbour, {})
                if person.get("company", "") == to_company:
                    return [
                        {"person_id": p, **persons[p]}
                        for p in new_path
                        if p in persons
                    ]
                queue.append(new_path)
        return []

    def get_stats(self) -> Dict:
        """
        Return graph-level statistics.

        Returns:
            Dict with total_persons, total_connections, companies.
        """
        with self._lock:
            companies = {p["company"] for p in self._persons.values()}
            return {
                "total_persons": len(self._persons),
                "total_connections": len(self._connections),
                "companies": len(companies),
            }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_graph: Optional[DecisionGraphEngine] = None


def get_decision_graph() -> DecisionGraphEngine:
    """Return the process-wide singleton DecisionGraphEngine instance."""
    global _graph
    if _graph is None:
        _graph = DecisionGraphEngine()
    return _graph
