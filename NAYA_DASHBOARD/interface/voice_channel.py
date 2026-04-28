"""
NAYA Dashboard — Voice Channel
Canal de transmission des intentions humaines vocales.
Aucune reconnaissance, aucune synthèse, aucune décision.
"""
import logging
from typing import Optional, Dict, Any

log = logging.getLogger("NAYA.DASHBOARD.voice")

__all__ = ["VoiceChannel"]


class VoiceChannel:
    """
    Canal vocal Dashboard → Système NAYA.
    Pont entre l'interface vocale et le text channel sous-jacent.
    """

    def __init__(self, system=None) -> None:
        self._system = system
        self._session_active = False
        self._utterance_count = 0
        self._tts_available = self._check_tts()

    def _check_tts(self) -> bool:
        try:
            import pyttsx3  # noqa
            return True
        except ImportError:
            return False

    def start_session(self) -> Dict[str, Any]:
        """Démarre une session vocale."""
        self._session_active = True
        log.info("[VOICE_CHANNEL] Session vocale démarrée")
        return {"status": "session_started", "tts_available": self._tts_available}

    def end_session(self) -> Dict[str, Any]:
        """Termine la session vocale."""
        self._session_active = False
        log.info("[VOICE_CHANNEL] Session vocale terminée")
        return {"status": "session_ended", "utterances": self._utterance_count}

    def transmit(self, text: str) -> Dict[str, Any]:
        """
        Transmet un texte reconnu (ASR → système).
        Dans la pratique, délègue au TextChannel.
        """
        if not self._session_active:
            return {"status": "error", "message": "Aucune session active"}

        self._utterance_count += 1
        log.debug(f"[VOICE_CHANNEL] Utterance #{self._utterance_count}: {text[:60]}")

        # Déléguer au TextChannel
        try:
            from NAYA_DASHBOARD.interface.text_channel import TextChannel
            tc = TextChannel(system=self._system)
            result = tc.send(text, context={"source": "voice"})
            result["utterance_id"] = self._utterance_count
            return result
        except Exception as e:
            log.warning(f"[VOICE_CHANNEL] Erreur délégation: {e}")
            return {"status": "error", "message": str(e)}

    def speak(self, text: str) -> bool:
        """Synthèse vocale de la réponse (TTS)."""
        if not self._tts_available:
            log.debug(f"[VOICE_CHANNEL] TTS désactivé — texte: {text[:60]}")
            return False
        try:
            from NAYA_DASHBOARD.voice.tts import speak as tts_speak
            tts_speak(text)
            return True
        except Exception as e:
            log.warning(f"[VOICE_CHANNEL] Erreur TTS: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        return {
            "session_active": self._session_active,
            "utterances": self._utterance_count,
            "tts_available": self._tts_available,
            "system_connected": self._system is not None,
        }
