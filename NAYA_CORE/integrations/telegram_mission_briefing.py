"""Telegram Mission Briefing — envoi quotidien du plan et du lien TORI_APP."""

from __future__ import annotations

from typing import Dict, Any

from NAYA_CORE.integrations.telegram_notifier import get_notifier
from NAYA_PROJECT_ENGINE.mission_10_days_engine import mission_10_days_engine


class TelegramMissionBriefing:
    """Envoie le briefing matinal mission 10 jours sur Telegram."""

    def send_morning_briefing(self, tori_url: str = "http://localhost:8080/tori/mission10d/report") -> Dict[str, Any]:
        notifier = get_notifier()
        message = mission_10_days_engine.morning_briefing_text(tori_url=tori_url)
        notifier.send(message)
        return {
            "sent": True,
            "channel": "telegram",
            "tori_url": tori_url,
            "day": mission_10_days_engine.current_day(),
        }


telegram_mission_briefing = TelegramMissionBriefing()
