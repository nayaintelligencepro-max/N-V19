"""
NAYA V20 — Local LLM Trainer
══════════════════════════════════════════════════════════════════════════════
Data collection pipeline for fine-tuning on won OT contracts.
No actual GPU training happens here; this module collects, stores and exports
the labeled dataset (contracts, emails, objections, offers) that will be fed
to a fine-tuning job once a GPU node is available.

DOCTRINE:
  Every won contract, every successful email, every defeated objection becomes
  a training sample.  Over time NAYA's local model surpasses generic LLMs on
  OT/IEC-62443 domain tasks.

OUTPUT:
  JSONL export compatible with OpenAI fine-tuning format and HuggingFace
  datasets.
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.LOCAL_LLM_TRAINER")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "local_llm_trainer.json"

VALID_SAMPLE_TYPES = ("contract", "email", "objection", "offer")


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class TrainingSample:
    """A single labeled training example."""

    sample_id: str
    sample_type: str          # contract | email | objection | offer
    content: str
    outcome: str              # won | lost | converted | ignored
    sector: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LocalLLMTrainer:
    """
    Collects and manages the dataset used to fine-tune NAYA's local LLM.

    All samples are persisted to DATA_FILE as a flat list of dicts.
    Export via export_jsonl() for actual fine-tuning jobs.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._samples: List[Dict] = []
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._samples = data.get("samples", [])
            except Exception:
                pass  # start fresh on corrupt file

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"samples": self._samples,
                     "updated_at": datetime.now(timezone.utc).isoformat()},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def add_training_sample(
        self,
        sample_type: str,
        content: str,
        outcome: str,
        sector: str,
    ) -> str:
        """
        Add a labeled training sample to the dataset.

        Args:
            sample_type: One of "contract", "email", "objection", "offer".
            content: Raw text content of the sample.
            outcome: Result label ("won", "lost", "converted", "ignored").
            sector: Business sector (e.g. "transport", "energie").

        Returns:
            sample_id — first 12 hex chars of SHA-256(content+sample_type).
        """
        if sample_type not in VALID_SAMPLE_TYPES:
            raise ValueError(
                f"Invalid sample_type '{sample_type}'. "
                f"Must be one of {VALID_SAMPLE_TYPES}."
            )
        sample_id = _sha256(content + sample_type)[:12]
        sample = TrainingSample(
            sample_id=sample_id,
            sample_type=sample_type,
            content=content,
            outcome=outcome,
            sector=sector,
        )
        with self._lock:
            # Avoid exact duplicates
            existing_ids = {s["sample_id"] for s in self._samples}
            if sample_id not in existing_ids:
                self._samples.append(asdict(sample))
        self._save()
        return sample_id

    def get_training_dataset(self, sample_type: Optional[str] = None) -> List[Dict]:
        """
        Retrieve training samples, optionally filtered by type.

        Args:
            sample_type: If provided, filter to this type only. None returns all.

        Returns:
            List of sample dicts.
        """
        with self._lock:
            if sample_type is None:
                return list(self._samples)
            return [s for s in self._samples if s["sample_type"] == sample_type]

    def compute_training_stats(self) -> Dict:
        """
        Compute aggregate statistics over the dataset.

        Returns:
            Dict with keys: total, by_type, by_sector, by_outcome.
        """
        by_type: Dict[str, int] = {}
        by_sector: Dict[str, int] = {}
        by_outcome: Dict[str, int] = {}

        with self._lock:
            for s in self._samples:
                by_type[s["sample_type"]] = by_type.get(s["sample_type"], 0) + 1
                by_sector[s["sector"]] = by_sector.get(s["sector"], 0) + 1
                by_outcome[s["outcome"]] = by_outcome.get(s["outcome"], 0) + 1

        return {
            "total": len(self._samples),
            "by_type": by_type,
            "by_sector": by_sector,
            "by_outcome": by_outcome,
        }

    def export_jsonl(self, output_path: str) -> int:
        """
        Export all training samples as JSONL (one JSON object per line).

        Compatible with OpenAI fine-tuning and HuggingFace datasets formats.

        Args:
            output_path: Absolute or relative path for the output .jsonl file.

        Returns:
            Number of lines written.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            samples = list(self._samples)
        lines_written = 0
        with open(out, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
                lines_written += 1
        log.info("LocalLLMTrainer: exported %d samples to %s", lines_written, output_path)
        return lines_written

    def get_stats(self) -> Dict:
        """
        Return high-level stats for dashboard display.

        Returns:
            Dict with total_samples, data_file path string, and sample_types list.
        """
        with self._lock:
            types_present = list({s["sample_type"] for s in self._samples})
            total = len(self._samples)
        return {
            "total_samples": total,
            "data_file": str(self._data_file),
            "sample_types": sorted(types_present),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_trainer: Optional[LocalLLMTrainer] = None


def get_local_llm_trainer() -> LocalLLMTrainer:
    """Return the process-wide singleton LocalLLMTrainer instance."""
    global _trainer
    if _trainer is None:
        _trainer = LocalLLMTrainer()
    return _trainer
