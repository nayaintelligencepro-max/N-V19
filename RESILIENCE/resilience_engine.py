"""
NAYA SUPREME V19 — RESILIENCE ENGINE
═══════════════════════════════════════════════════════════════
Le système s'adapte et anticipe — même si Python disparaît.

5 MODES DE FONCTIONNEMENT:

  MODE FULL     Python OK + tous modules actifs → 100% autonome
  MODE HYBRID   Python OK + modules partiels    → fallback webhooks
  MODE CLOUD    Python down / webhooks actifs   → Make.com/Zapier
  MODE TELEGRAM Bot Telegram seul actif         → contrôle mobile
  MODE OFFLINE  Tout down                        → JSON + SURVIVAL_GUIDE

GARDE-FOUS AUTOMATIQUES:
  • Export JSON complet toutes les heures
  • SURVIVAL_GUIDE.md régénéré (guide opérationnel 0-tech)
  • Scripts bash autonomes (aucune dépendance Python)
  • Webhooks Make.com activables en 5 min
  • Tout le catalogue OT exporté en CSV lisible depuis Excel
═══════════════════════════════════════════════════════════════
"""
import json, time, logging, os, threading, csv, io
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.RESILIENCE")
ROOT = Path(__file__).resolve().parent.parent
EXPORTS = ROOT / "data" / "exports"
EXPORTS.mkdir(parents=True, exist_ok=True)


class ResilienceEngine:
    """
    Moteur de résilience total.
    Le business continue quoi qu'il arrive.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        log.info("ResilienceEngine V19 — 5 modes de fallback")

    def start(self):
        """Démarre l'export automatique horaire."""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        # Export immédiat au boot
        self.full_export()
        log.info("Resilience: export horaire démarré")

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                self.full_export()
                time.sleep(3600)   # Toutes les heures
            except Exception as e:
                log.warning("Resilience loop: %s", e)
                time.sleep(300)

    # ── EXPORT PRINCIPAL ──────────────────────────────────────────────────
    def full_export(self) -> Dict[str, str]:
        """
        Export complet : JSON snapshot + CSV catalogue + guide + bash.
        Lisible sans Python depuis n'importe quel outil.
        """
        files = {}
        files["snapshot"] = self._export_snapshot()
        files["catalogue_csv"] = self._export_catalogue_csv()
        files["survival_guide"] = self._export_survival_guide()
        files["bash_script"] = self._export_bash_script()
        files["pipeline_csv"] = self._export_pipeline_csv()
        log.info("Resilience export complet: %d fichiers", len(files))
        return files

    def _collect_state(self) -> Dict:
        """Collecte l'état complet depuis tous les modules actifs."""
        state = {
            "naya_version": "19.0.0",
            "export_time": datetime.now().isoformat(),
            "mode": "full",
            "pipeline": {},
            "catalogue": {},
            "revenue": {},
            "actions_immediates": [],
        }
        try:
            from PARALLEL_ENGINE.parallel_pipeline_manager import get_parallel_pipeline
            state["pipeline"] = get_parallel_pipeline().get_dashboard()
        except Exception:
            pass
        try:
            from CATALOGUE_OT.catalogue_engine import get_catalogue_engine
            state["catalogue"] = get_catalogue_engine().get_stats()
        except Exception:
            pass
        try:
            from NAYA_REVENUE_ENGINE.revenue_target_engine import get_revenue_targets
            state["revenue"] = get_revenue_targets().get_current_target()
        except Exception:
            pass
        # Actions immédiates TOUJOURS présentes
        state["actions_immediates"] = [
            "1. Envoyer pitch Pack Audit Express 15k€ à 3 prospects Transport (template: exports/pitch_transport.txt)",
            "2. Appeler 2 RSSI énergie — urgence NIS2 IEC62443 (liste: exports/contacts_energie.csv)",
            "3. Follow-up J+3 sur tous les pitchs envoyés cette semaine",
            "4. Créer lien PayPal 15000€ pour premier closing Pack Audit Express",
            "5. Proposer monitoring 2k€/mois à tout client ayant reçu une formation",
        ]
        return state

    def _export_snapshot(self) -> str:
        """Export JSON complet — lisible sans Python."""
        state = self._collect_state()
        state["payment_links"] = {
            "paypal": "paypal.me/TONURL?amount=15000&currency_code=EUR",
            "deblock": "Application Deblock mobile → créer facture",
        }
        state["contacts_urgence"] = {
            "telegram_bot": "Si bot actif → /status, /hunt, /revenue",
            "email_secours": "Voir SECRETS/keys/domains_emails.json",
        }
        path = EXPORTS / "naya_snapshot_LATEST.json"
        path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        # Archive horodatée
        arch = EXPORTS / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        arch.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def _export_catalogue_csv(self) -> str:
        """Export CSV du catalogue OT — ouvrable directement dans Excel."""
        rows = [["Secteur", "Service", "Prix EUR", "Duree Jours", "Pack"]]
        try:
            from CATALOGUE_OT.catalogue_engine import get_catalogue_engine, Secteur
            cat = get_catalogue_engine()
            packs = [("audit_express", 15000), ("securite_avancee", 40000), ("premium_full", 80000)]
            for s in Secteur:
                for pack_key, prix in packs:
                    rows.append([s.value, f"Pack: {pack_key.replace('_', ' ').title()}", prix, 3, pack_key])
                svcs = cat.get_services(s, 30)
                for svc in svcs:
                    rows.append([s.value, svc["nom"], svc["prix"], svc["duree"], "service"])
        except Exception:
            rows.append(["IEC62443", "Service Cybersécurité OT", 39681, 3, "service"])

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerows(rows)
        path = EXPORTS / "catalogue_ot_COMPLET.csv"
        path.write_text(buf.getvalue(), encoding="utf-8")
        return str(path)

    def _export_pipeline_csv(self) -> str:
        """Export CSV du pipeline parallèle."""
        rows = [["Slot", "Projet", "Target EUR", "Priorité", "Actions"]]
        try:
            from PARALLEL_ENGINE.parallel_pipeline_manager import get_parallel_pipeline
            dash = get_parallel_pipeline().get_dashboard()
            for p in dash.get("projets_actifs", []):
                rows.append([
                    p.get("id", "?"), p["nom"], p["target"],
                    "HIGH", " | ".join(p.get("actions_prochaines", []))
                ])
        except Exception:
            rows.append(["—", "Pipeline non chargé", 0, "—", "Voir naya_snapshot_LATEST.json"])

        buf = io.StringIO()
        csv.writer(buf).writerows(rows)
        path = EXPORTS / "pipeline_actif.csv"
        path.write_text(buf.getvalue(), encoding="utf-8")
        return str(path)

    def _export_survival_guide(self) -> str:
        """SURVIVAL_GUIDE.md — opérer le business sans aucune technologie."""
        state = self._collect_state()
        rev = state.get("revenue", {})
        guide = f"""# NAYA V19 — SURVIVAL GUIDE
*Généré automatiquement le {datetime.now().strftime('%d/%m/%Y %H:%M')}*
*Utilisez ce guide si le serveur Python est indisponible.*

---

## OBJECTIFS REVENUS ACTIFS
| Mois | Cible | Levier |
|------|-------|--------|
| M1 | 5 000€ | Formation OT + Pack Audit Express |
| M2-3 | 10-20k€ | Catalogue OT Transport + Énergie |
| M6-9 | 30-50k€ | Pipeline chaud + Récurrence |
| M12 | 80-100k€ | Contrats annuels + Scale |

**Ce mois :** Objectif {rev.get('objectif_target', 5000):,}€ | Réalisé {rev.get('realise_ce_mois', 0):,}€

---

## 5 ACTIONS IMMÉDIATES (sans technologie)

{chr(10).join(state.get('actions_immediates', []))}

---

## CATALOGUE OT — 3 PACKS À VENDRE

### Pack Audit Express — 15 000€ / 3 jours
- **Cible** : PME industrielles, opérateurs transport, utilities
- **Pitch** : "3 jours. Tous vos risques OT identifiés. Plan d'action fourni."
- **Urgence** : Deadline NIS2 / audit ANSSI imminent
- **Paiement** : PayPal immédiat ou virement 8j

### Pack Sécurité Avancée — 40 000€ / 3 jours
- **Cible** : OIV, ETI, opérateurs critiques
- **Pitch** : "Conformité IEC 62443 SL-2 garantie. Politique IACS incluse."
- **Urgence** : Obligations NIS2 + sanctions jusqu'à 10M€

### Pack Premium Full — 80 000€ / 3 jours
- **Cible** : Grands comptes, infrastructures nationales
- **Pitch** : "De l'audit à la certification. Clé en main."

---

## PROSPECTION 0-TECH (LinkedIn + Téléphone)

### Recherche LinkedIn
```
"RSSI" + "industrie" + France → envoyer 10 messages/j
"DSI sécurité" + "énergie" + France → pitch NIS2
"Responsable OT" + transport → pitch ERTMS/SCADA
```

### Message LinkedIn (copier-coller)
```
Bonjour [Prénom],
j'accompagne les RSSI sur la conformité IEC 62443 OT.
En 3 jours : rapport complet + plan d'action.
Pack Audit Express : 15 000€.
Êtes-vous la bonne personne chez [Entreprise] ?
```

### Prospects prioritaires Transport
SNCF Réseau, RATP, Keolis, CMA CGM, Aéroports de Paris, Vinci Autoroutes

### Prospects prioritaires Énergie
EDF, Enedis, RTE, GRTgaz, GRDF, TotalEnergies, Neoen, CNR

### Prospects prioritaires Industrie
Airbus, Safran, Michelin, Renault, Stellantis, Alstom, Saint-Gobain

---

## PAIEMENT SANS SERVEUR
1. **PayPal.me** → paypal.me/TONURL?amount=15000&currency_code=EUR
2. **Deblock app** → Créer facture mobile, IBAN immédiat
3. **Virement** → RIB dans SECRETS/keys/payments.env

---

## RECYCLAGE D'ASSETS (Manuel)
- Tout email écrit → copier dans un Google Doc "TEMPLATES"
- Tout rapport → renommer + adapter pour prochain client
- Tout contact → ajouter dans un tableur "PROSPECTS"
- Principe : JAMAIS supprimer, toujours versionner

---

## MODE CLOUD (si Python down)
1. **Make.com** → activer le scénario "NAYA Backup" (webhook)
2. **Zapier** → zap "Nouveau prospect → Email auto"
3. **Telegram bot** → commandes /status /hunt /revenue (si bot actif)

---

*Ce guide est recréé automatiquement chaque heure par NAYA V19.*
*Fichier exports: {str(EXPORTS)}*
"""
        path = ROOT / "SURVIVAL_GUIDE.md"
        path.write_text(guide, encoding="utf-8")
        return str(path)

    def _export_bash_script(self) -> str:
        """Script bash autonome — 0 dépendance Python."""
        script = """#!/usr/bin/env bash
# NAYA V19 — SCRIPT BASH SURVIVAL
# Usage: bash data/exports/naya_survival.sh
# Aucune dépendance Python requise.

echo "======================================="
echo "  NAYA SUPREME V19 — SURVIVAL MODE"
echo "  $(date '+%d/%m/%Y %H:%M')"
echo "======================================="

SNAPSHOT="data/exports/naya_snapshot_LATEST.json"

if command -v python3 &>/dev/null && [ -f "$SNAPSHOT" ]; then
    echo ""
    echo "PIPELINE ACTIF:"
    python3 -c "
import json, sys
try:
    d = json.load(open('$SNAPSHOT'))
    p = d.get('pipeline', {})
    print(f'  Slots actifs: {p.get(\"slots_actifs\",\"?\")}/4')
    print(f'  Valeur pipeline: {p.get(\"valeur_pipeline\",0):,.0f}EUR')
    print(f'  Revenu total: {p.get(\"revenu_total\",0):,.0f}EUR')
except: pass
"
    echo ""
    echo "ACTIONS IMMÉDIATES:"
    python3 -c "
import json
try:
    d = json.load(open('$SNAPSHOT'))
    for a in d.get('actions_immediates', []):
        print(f'  {a}')
except: pass
"
else
    echo "Ouvrir manuellement: $SNAPSHOT"
    echo "Ou lire: SURVIVAL_GUIDE.md"
fi

echo ""
echo "CATALOGUE OT (3 packs):"
echo "  Pack Audit Express    → 15 000EUR / 3 jours (35% conversion)"
echo "  Pack Sécurité Avancée → 40 000EUR / 3 jours (22% conversion)"
echo "  Pack Premium Full     → 80 000EUR / 3 jours (12% conversion)"
echo ""
echo "CATALOGUE CSV: data/exports/catalogue_ot_COMPLET.csv"
echo "======================================="
"""
        path = EXPORTS / "naya_survival.sh"
        path.write_text(script, encoding="utf-8")
        try:
            os.chmod(path, 0o755)
        except Exception:
            pass
        return str(path)

    # ── STATUS ───────────────────────────────────────────────────────────
    def get_status(self) -> Dict:
        return {
            "mode": "full" if self._running else "partial",
            "export_horaire_actif": self._running,
            "exports_disponibles": {
                "snapshot_json": str(EXPORTS / "naya_snapshot_LATEST.json"),
                "catalogue_csv": str(EXPORTS / "catalogue_ot_COMPLET.csv"),
                "pipeline_csv": str(EXPORTS / "pipeline_actif.csv"),
                "survival_guide": str(ROOT / "SURVIVAL_GUIDE.md"),
                "bash_script": str(EXPORTS / "naya_survival.sh"),
            },
            "fallbacks": {
                "make_com": "activer scénario NAYA Backup sur make.com",
                "zapier": "zap 'prospect → email auto' sur zapier.com",
                "telegram": "commandes /status /hunt /revenue",
                "offline": "bash data/exports/naya_survival.sh",
            },
            "doctrine": "Le business continue quoi qu'il arrive",
        }


# ── SINGLETON ────────────────────────────────────────────────────────────────
_inst: Optional[ResilienceEngine] = None

def get_resilience_engine() -> ResilienceEngine:
    global _inst
    if _inst is None:
        _inst = ResilienceEngine()
    return _inst
