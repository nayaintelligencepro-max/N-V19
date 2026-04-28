"""NAYA V19 - Speech-to-Text - Reconnaissance vocale pour TORI."""
import logging
from typing import Dict, Optional
log = logging.getLogger("NAYA.VOICE.STT")

class SpeechToText:
    """Interface STT pour communication vocale avec NAYA via TORI."""

    SUPPORTED_LANGUAGES = ["fr-FR", "en-US", "en-GB"]

    def __init__(self):
        self._transcriptions: list = []
        self._active = False
        self._language = "fr-FR"

    def start_listening(self, language: str = "fr-FR") -> Dict:
        self._active = True
        self._language = language
        return {
            "status": "listening",
            "language": language,
            "note": "STT utilise l API Web Speech du navigateur dans TORI PWA"
        }

    def stop_listening(self) -> Dict:
        self._active = False
        return {"status": "stopped"}

    def process_audio(self, audio_data: bytes) -> Dict:
        """Placeholder pour traitement audio - dans TORI, le STT est cote navigateur."""
        return {
            "status": "browser_side",
            "message": "Le STT est gere cote navigateur via Web Speech API dans TORI PWA",
            "fallback": "Whisper API si disponible"
        }

    def add_transcription(self, text: str, confidence: float = 0.9) -> Dict:
        entry = {"text": text, "confidence": confidence, "language": self._language}
        self._transcriptions.append(entry)
        return entry

    def get_last_transcription(self) -> Optional[Dict]:
        return self._transcriptions[-1] if self._transcriptions else None

    def get_stats(self) -> Dict:
        return {
            "active": self._active, "language": self._language,
            "total_transcriptions": len(self._transcriptions),
            "supported_languages": self.SUPPORTED_LANGUAGES
        }
