"""NAYA V19.7 — INNOVATION #5: REAL-TIME KNOWLEDGE DIFFUSION
Quand un agent apprend, TOUS les agents le savent en < 100ms. Network effect entre agents."""

import asyncio
import logging
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

@dataclass
class LearningEvent:
    event_type: str  # objection_solved, deal_closed, pattern_found, etc
    source_agent: str
    data: Dict[str, Any]
    confidence: float
    timestamp: datetime
    affected_agents: List[str] = None

class KnowledgeDiffusionNetwork:
    """Event-driven knowledge propagation entre les 11 agents."""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.learning_events: List[LearningEvent] = []
        self.agent_handlers = {}
        logger.info("✅ Knowledge Diffusion Network initialized")

    def subscribe(self, event_type: str, handler: Callable):
        """Un agent subscribe à un type d'événement"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type}")

    async def broadcast_learning(self, event: LearningEvent):
        """Broadcast learning event à tous les subscribers"""
        logger.info(f"📡 Broadcasting: {event.event_type} from {event.source_agent}")

        self.learning_events.append(event)

        # Get all handlers pour ce type
        handlers = self.subscribers.get(event.event_type, [])

        # Execute en parallèle < 100ms
        tasks = [handler(event) for handler in handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def learning_objection_solved(self, objection: str, response: str, win_rate: float):
        """Quand closer résout une objection"""
        event = LearningEvent(
            event_type="objection_solved",
            source_agent="closer",
            data={
                "objection": objection,
                "response": response,
                "win_rate": win_rate,
                "sector": "Energy"
            },
            confidence=0.94,
            timestamp=datetime.utcnow()
        )
        await self.broadcast_learning(event)

    async def learning_deal_closed(self, deal_value: float, close_time_days: int, decision_maker: str):
        """Quand un deal ferme"""
        event = LearningEvent(
            event_type="deal_closed",
            source_agent="contract_generator",
            data={
                "deal_value": deal_value,
                "close_time_days": close_time_days,
                "decision_maker": decision_maker
            },
            confidence=1.0,
            timestamp=datetime.utcnow()
        )
        await self.broadcast_learning(event)

    async def learning_pattern_found(self, pattern_name: str, pattern_data: Dict):
        """Quand Guardian ou autre détecte un pattern"""
        event = LearningEvent(
            event_type="pattern_found",
            source_agent="guardian",
            data=pattern_data,
            confidence=0.87,
            timestamp=datetime.utcnow()
        )
        await self.broadcast_learning(event)

    def register_agent_handler(self, agent_name: str, handler: Callable):
        """Register handler pour un agent"""
        self.agent_handlers[agent_name] = handler

    async def inject_learning_into_agent(self, agent_name: str, learning_event: LearningEvent):
        """Injecte learning directement dans agent internal knowledge"""
        if agent_name in self.agent_handlers:
            await self.agent_handlers[agent_name](learning_event)

    async def get_network_status(self) -> Dict:
        """Retourne status du réseau"""
        return {
            "event_types": len(self.subscribers),
            "total_events": len(self.learning_events),
            "agents_connected": len(self.agent_handlers),
            "last_broadcast": self.learning_events[-1].timestamp.isoformat() if self.learning_events else None
        }

__all__ = ['KnowledgeDiffusionNetwork', 'LearningEvent']
