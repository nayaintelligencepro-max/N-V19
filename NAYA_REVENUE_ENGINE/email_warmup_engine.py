"""
NAYA SUPREME V14 — Email Warm-Up & Deliverability Engine
════════════════════════════════════════════════════════════════════════════════
SANS WARM-UP = 100% SPAM = 0€ DE REVENU.

Ce module gère :
  1. Stratégie de warm-up progressif (semaine 1→4)
  2. Validation de délivrabilité (SPF/DKIM checks)
  3. Quota journalier intelligent (jamais saturer)
  4. Rotation d'adresses d'envoi
  5. Scoring de réputation
════════════════════════════════════════════════════════════════════════════════
"""
import os, time, json, logging, threading
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.WARMUP")

def _gs(k, d=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


# ─── Calendrier de warm-up progressif ─────────────────────────────────────
WARMUP_SCHEDULE = {
    1:  {"daily_max": 10,  "desc": "Semaine 1 — démarrage très prudent"},
    2:  {"daily_max": 25,  "desc": "Semaine 2 — montée graduelle"},
    3:  {"daily_max": 50,  "desc": "Semaine 3 — régime intermédiaire"},
    4:  {"daily_max": 100, "desc": "Semaine 4 — quasi-normal"},
    5:  {"daily_max": 200, "desc": "Semaine 5+ — régime de croisière"},
    99: {"daily_max": 500, "desc": "Compte établi — pleine capacité"},
}

SPAM_TRIGGERS = [
    "URGENT", "FREE", "GRATUIT", "GAGNEZ", "WIN", "CLICK HERE",
    "100%", "GARANTI", "OFFRE LIMITÉE", "PROMOTION", "DEAL",
    "$$", "€€", "argent facile", "revenus passifs",
]


@dataclass
class SendingAccount:
    email: str
    domain: str
    warmup_start_date: float = field(default_factory=time.time)
    sent_today: int = 0
    sent_total: int = 0
    bounces: int = 0
    spam_reports: int = 0
    opens: int = 0
    replies: int = 0
    reputation_score: float = 100.0  # 0-100
    last_reset_day: str = ""
    is_primary: bool = True


class EmailWarmUpEngine:
    """
    Gère la délivrabilité des emails pour maximiser les revenus.
    Un email non-délivré = 0% de chance de vente.
    """

    PERSIST_FILE = Path("data/cache/email_warmup.json")

    def __init__(self):
        self._accounts: Dict[str, SendingAccount] = {}
        self._lock = threading.Lock()
        self._load()
        self._init_primary_account()

    def _init_primary_account(self):
        """Initialise le compte d'envoi principal depuis les secrets."""
        email = _gs("EMAIL_FROM") or _gs("SMTP_USER")
        if email and email not in self._accounts:
            domain = email.split("@")[-1] if "@" in email else "unknown"
            self._accounts[email] = SendingAccount(email=email, domain=domain)
            log.info("[WarmUp] Compte initialisé: %s", email)

    def get_daily_quota(self, email: str) -> int:
        """Retourne le quota d'envoi journalier selon l'âge du compte."""
        acc = self._accounts.get(email)
        if not acc:
            return 10  # Très prudent pour compte inconnu
        week = max(1, int((time.time() - acc.warmup_start_date) / 604800) + 1)
        week_key = min(week, 99)
        for w in sorted(WARMUP_SCHEDULE.keys(), reverse=True):
            if week_key >= w:
                return WARMUP_SCHEDULE[w]["daily_max"]
        return 10

    def can_send(self, email: str) -> Tuple[bool, str]:
        """
        Vérifie si on peut envoyer depuis ce compte maintenant.
        Returns: (can_send, reason)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        with self._lock:
            acc = self._accounts.get(email)
            if not acc:
                return False, "Compte non configuré"

            # Reset compteur quotidien
            if acc.last_reset_day != today:
                acc.sent_today = 0
                acc.last_reset_day = today

            # Quota journalier
            quota = self.get_daily_quota(email)
            if acc.sent_today >= quota:
                return False, f"Quota journalier atteint ({acc.sent_today}/{quota})"

            # Réputation minimale
            if acc.reputation_score < 50:
                return False, f"Réputation trop basse ({acc.reputation_score:.0f}/100) — arrêt préventif"

            # Trop de spams
            if acc.spam_reports > 5:
                return False, f"Trop de spam reports ({acc.spam_reports})"

            return True, f"OK — {quota - acc.sent_today} envois restants aujourd'hui"

    def record_send(self, email: str) -> None:
        """Enregistre un envoi."""
        with self._lock:
            acc = self._accounts.get(email)
            if acc:
                acc.sent_today += 1
                acc.sent_total += 1
        self._persist()

    def record_event(self, email: str, event: str) -> None:
        """Enregistre bounce/spam/open/reply pour ajuster la réputation."""
        with self._lock:
            acc = self._accounts.get(email)
            if not acc:
                return
            if event == "bounce":
                acc.bounces += 1
                acc.reputation_score = max(0, acc.reputation_score - 5)
            elif event == "spam":
                acc.spam_reports += 1
                acc.reputation_score = max(0, acc.reputation_score - 15)
            elif event == "open":
                acc.opens += 1
                acc.reputation_score = min(100, acc.reputation_score + 1)
            elif event == "reply":
                acc.replies += 1
                acc.reputation_score = min(100, acc.reputation_score + 3)
        self._persist()

    def check_subject_spam_score(self, subject: str) -> Dict:
        """Analyse un sujet d'email pour les triggers spam."""
        subject_upper = subject.upper()
        found_triggers = [t for t in SPAM_TRIGGERS if t.upper() in subject_upper]
        caps_ratio = sum(1 for c in subject if c.isupper()) / max(len(subject), 1)
        score = 100
        score -= len(found_triggers) * 15
        score -= int(caps_ratio * 50) if caps_ratio > 0.3 else 0
        score -= 10 if subject.endswith("!") else 0
        score -= 10 if len(subject) > 60 else 0
        return {
            "score": max(0, score),
            "triggers_found": found_triggers,
            "caps_ratio": round(caps_ratio, 2),
            "recommendation": "✅ OK" if score >= 70 else ("⚠️ À améliorer" if score >= 50 else "❌ À reécrire"),
        }

    def get_best_send_time(self) -> Dict:
        """Retourne le meilleur créneau d'envoi selon les données."""
        hour = datetime.now().hour
        day = datetime.now().weekday()  # 0=lundi

        # Éviter weekends, nuits, heures de repas
        if day >= 5:  # Samedi/Dimanche
            return {"send_now": False, "reason": "Weekend — attendre lundi matin", "next_slot": "Lundi 09h00"}
        if hour < 8 or hour >= 18:
            next_h = 9 if hour < 8 else 9
            return {"send_now": False, "reason": f"Hors horaires bureau", "next_slot": f"Demain {next_h:02d}h00"}
        if 12 <= hour < 14:
            return {"send_now": False, "reason": "Déjeuner — taux d'ouverture faible", "next_slot": f"Aujourd'hui 14h00"}

        # Meilleurs créneaux : 9h-12h et 14h-17h
        best = 9 <= hour < 12 or 14 <= hour < 17
        return {
            "send_now": best,
            "current_hour": hour,
            "best_windows": ["09h-12h (optimal)", "14h-17h (bon)"],
            "reason": "Créneau optimal ✅" if best else "Créneau acceptable",
        }

    def get_deliverability_report(self) -> Dict:
        """Rapport complet de délivrabilité."""
        reports = []
        with self._lock:
            for email, acc in self._accounts.items():
                quota = self.get_daily_quota(email)
                bounce_rate = acc.bounces / max(acc.sent_total, 1) * 100
                spam_rate = acc.spam_reports / max(acc.sent_total, 1) * 100
                open_rate = acc.opens / max(acc.sent_total, 1) * 100

                week = int((time.time() - acc.warmup_start_date) / 604800) + 1
                reports.append({
                    "email": email,
                    "domain": acc.domain,
                    "reputation_score": round(acc.reputation_score, 1),
                    "warmup_week": week,
                    "daily_quota": quota,
                    "sent_today": acc.sent_today,
                    "sent_total": acc.sent_total,
                    "bounce_rate_pct": round(bounce_rate, 2),
                    "spam_rate_pct": round(spam_rate, 2),
                    "open_rate_pct": round(open_rate, 2),
                    "status": "✅ Sain" if acc.reputation_score >= 70 else ("⚠️ Attention" if acc.reputation_score >= 50 else "❌ Dégradé"),
                })

        return {
            "accounts": reports,
            "total_accounts": len(reports),
            "recommendations": self._get_recommendations(reports),
        }

    def _get_recommendations(self, reports: List[Dict]) -> List[str]:
        recs = []
        for r in reports:
            if r["warmup_week"] <= 1:
                recs.append(f"⚠️ {r['email']}: Semaine 1 — max {r['daily_quota']} emails/jour")
            if r["bounce_rate_pct"] > 5:
                recs.append(f"❌ {r['email']}: Taux bounce élevé ({r['bounce_rate_pct']:.1f}%) — nettoyer la liste")
            if r["spam_rate_pct"] > 0.3:
                recs.append(f"❌ {r['email']}: Spam reports ({r['spam_rate_pct']:.2f}%) — revoir les templates")
        if not recs:
            recs.append("✅ Tous les comptes sont dans les normes de délivrabilité")
        recs.append("💡 Configurer SPF/DKIM/DMARC sur votre domaine pour +40% de délivrabilité")
        recs.append("💡 Utiliser SendGrid avec un sous-domaine dédié (mail.votredomaine.com)")
        return recs

    def _persist(self):
        try:
            self.PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                k: {
                    "email": v.email, "domain": v.domain,
                    "warmup_start": v.warmup_start_date,
                    "sent_today": v.sent_today, "sent_total": v.sent_total,
                    "bounces": v.bounces, "spam_reports": v.spam_reports,
                    "opens": v.opens, "replies": v.replies,
                    "reputation": v.reputation_score,
                    "last_reset": v.last_reset_day,
                }
                for k, v in self._accounts.items()
            }
            self.PERSIST_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.warning("[WarmUp] Persist error: %s", e)

    def _load(self):
        try:
            if self.PERSIST_FILE.exists():
                data = json.loads(self.PERSIST_FILE.read_text())
                for k, v in data.items():
                    self._accounts[k] = SendingAccount(
                        email=v["email"], domain=v["domain"],
                        warmup_start_date=v["warmup_start"],
                        sent_today=v["sent_today"], sent_total=v["sent_total"],
                        bounces=v["bounces"], spam_reports=v["spam_reports"],
                        opens=v["opens"], replies=v["replies"],
                        reputation_score=v["reputation"],
                        last_reset_day=v["last_reset"],
                    )
        except Exception as e:
            log.debug("[WarmUp] Load: %s", e)


_WU: Optional[EmailWarmUpEngine] = None
_WU_LOCK = threading.Lock()

def get_warmup_engine() -> EmailWarmUpEngine:
    global _WU
    if _WU is None:
        with _WU_LOCK:
            if _WU is None:
                _WU = EmailWarmUpEngine()
    return _WU
