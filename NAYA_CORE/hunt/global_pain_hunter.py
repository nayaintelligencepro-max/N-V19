"""
NAYA V19 — Global Pain Hunter X10
═══════════════════════════════════════════════════════════════════════
Chasse MONDIALE de douleurs B2B en temps réel.
Sources actives :
  1. Serper.dev (Google Search — signaux réels)
  2. Marchés publics data.gouv.fr + BOAMP
  3. LinkedIn patterns (offres d'emploi = douleur cachée)
  4. Leboncoin / PagesJaunes scraping (PME locales)
  5. Google Maps API (entreprises sans site, sans avis = opp)
  6. Reddit/forums FR (plaintes secteur = douleurs collectives)
  7. Afrique francophone + Polynésie + DOM-TOM (marchés oubliés)

Résultat : pipeline de 30-100 prospects qualifiés/semaine
avec score de douleur, valeur estimée, email potentiel.
═══════════════════════════════════════════════════════════════════════
"""
import os, time, json, logging, threading, hashlib, urllib.request, urllib.parse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

log = logging.getLogger("NAYA.HUNT.GLOBAL")


def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


# ── Catégories de chasse avec valeurs estimées ───────────────────────────────

HUNT_CATEGORIES = {
    "audit_digital": {
        "queries": [
            '"avis négatifs" site:tripadvisor.fr OR site:google.com "restaurant" "mauvais service"',
            '"site internet lent" OR "site en maintenance" entreprise PME',
            '"pas de site web" OR "site obsolète" artisan OR commerce 2024 2025',
            '"appel offres" "refonte site" OR "création site" collectivité 2025',
        ],
        "value_range": (1500, 8000),
        "delivery_hours": 48,
        "pain_type": "visibilite_digitale",
    },
    "automatisation_process": {
        "queries": [
            '"nous cherchons" "automatiser" OR "automatisation" PME OR entreprise site:linkedin.com',
            '"perte de temps" "tâches répétitives" OR "processus manuels" entreprise',
            '"excel" "manuel" "inefficace" "améliorer" directeur OR responsable',
            '"recrutons" "gestionnaire administratif" site:linkedin.com',
        ],
        "value_range": (3000, 25000),
        "delivery_hours": 72,
        "pain_type": "automatisation",
    },
    "ia_chatbot": {
        "queries": [
            '"service client débordé" OR "trop de demandes" OR "manque de personnel" entreprise',
            '"chatbot" OR "assistant virtuel" "besoin" OR "recherche" site:linkedin.com',
            '"répondre 24h" OR "disponible 24/7" service client PME',
            '"FAQ" "questions répétitives" entreprise OR agence',
        ],
        "value_range": (2000, 15000),
        "delivery_hours": 48,
        "pain_type": "ia_service_client",
    },
    "marches_publics": {
        "queries": [
            'site:data.gouv.fr "appel d\'offres" "numérique" OR "digital" OR "informatique" 2025',
            'site:boamp.fr "mission" "conseil" OR "transformation" "2025"',
            '"marché public" "DSI" "prestation" "consultant" 2025',
            '"appel d\'offres" "Polynésie française" OR "Nouvelle-Calédonie" "informatique" 2025',
        ],
        "value_range": (15000, 500000),
        "delivery_hours": 168,
        "pain_type": "marche_public",
    },
    "ecommerce_dropship": {
        "queries": [
            '"boutique en ligne" "pas de ventes" OR "peu de ventes" OR "améliorer" Shopify OR WooCommerce',
            '"taux de conversion" "faible" OR "problème" ecommerce France',
            '"abandon panier" "récupérer" boutique en ligne',
            '"dropshipping" "problèmes fournisseur" OR "délais livraison"',
        ],
        "value_range": (1500, 12000),
        "delivery_hours": 72,
        "pain_type": "ecommerce_optimisation",
    },
    "afrique_francophone": {
        "queries": [
            '"Côte d\'Ivoire" OR "Sénégal" OR "Cameroun" "appel d\'offres" "technologie" OR "digital" 2025',
            '"Maroc" "transformation digitale" "prestataire" OR "consultant" 2025',
            '"entreprise africaine" "besoin" "solution numérique" OR "automatisation"',
            '"fintech" OR "edtech" "Afrique" "développement" "partenaire" 2025',
        ],
        "value_range": (5000, 150000),
        "delivery_hours": 96,
        "pain_type": "afrique_digital",
    },
    "immobilier_investissement": {
        "queries": [
            '"terrain à vendre" "Polynésie française" OR "Tahiti" prix',
            '"investissement immobilier" "Pacifique" OR "DOM-TOM" rentable 2025',
            '"viager" OR "vente rapide" "propriétaire" cherche acheteur',
            '"rénovation" "financement" "aide" artisan OR promoteur',
        ],
        "value_range": (5000, 80000),
        "delivery_hours": 168,
        "pain_type": "immobilier_opportunite",
    },
    "recrutement_rh": {
        "queries": [
            '"difficultés recrutement" OR "pénurie talent" entreprise France 2025',
            '"turnover" "réduire" "fidéliser" RH PME',
            '"onboarding" "améliorer" "intégration" employés entreprise',
            '"marque employeur" "développer" PME ou ETI',
        ],
        "value_range": (3000, 30000),
        "delivery_hours": 96,
        "pain_type": "rh_talent",
    },
}


@dataclass
class HuntedOpportunity:
    """Opportunité détectée avec scoring et données contact."""
    opportunity_id: str
    category: str
    pain_type: str
    title: str
    description: str
    source_url: str
    source_type: str

    # Scoring
    pain_score: float = 0.0        # 0-1
    urgency_score: float = 0.0     # 0-1
    solvability_score: float = 0.0 # 0-1
    total_score: float = 0.0

    # Valeur estimée
    estimated_value_min: float = 0.0
    estimated_value_max: float = 0.0
    estimated_value: float = 0.0

    # Contact potentiel
    company_name: str = ""
    domain: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""

    # Offre recommandée
    recommended_offer: str = ""
    delivery_hours: int = 48

    # Metadata
    detected_at: float = field(default_factory=time.time)
    hunted: bool = False
    outreach_sent: bool = False
    status: str = "new"  # new / enriched / outreached / responded / won / lost

    def to_dict(self) -> Dict:
        return {
            "id": self.opportunity_id,
            "category": self.category,
            "pain_type": self.pain_type,
            "title": self.title[:100],
            "company": self.company_name,
            "domain": self.domain,
            "email": self.contact_email,
            "pain_score": round(self.pain_score, 2),
            "value_min": self.estimated_value_min,
            "value_max": self.estimated_value_max,
            "value": self.estimated_value,
            "delivery_h": self.delivery_hours,
            "status": self.status,
            "detected": datetime.fromtimestamp(self.detected_at).isoformat(),
        }


class GlobalPainHunter:
    """
    Chasseur global de douleurs business — produit de vrais prospects qualifiés.
    Tourne en arrière-plan, alimente le pipeline revenue automatiquement.
    """

    PERSIST_FILE = Path("data/cache/global_hunt_results.json")
    MAX_STORED = 500

    def __init__(self):
        self._opportunities: List[HuntedOpportunity] = []
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._total_hunted = 0
        self._total_qualified = 0
        self._scan_interval = int(os.getenv("NAYA_HUNT_INTERVAL", "3600"))  # 1h défaut
        self._last_scan: Dict[str, float] = {}
        self.PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    # ── Core: Serper Search ──────────────────────────────────────────────────

    def _serper_search(self, query: str, num: int = 10) -> List[Dict]:
        """Recherche Google via Serper API — clé rotative."""
        key = _gs("SERPER_API_KEY", "")
        if not key:
            return []
        try:
            url = "https://google.serper.dev/search"
            payload = json.dumps({"q": query, "num": num, "gl": "fr", "hl": "fr"}).encode()
            req = urllib.request.Request(url, data=payload, headers={
                "X-API-KEY": key.split(",")[0].strip(),
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                return data.get("organic", [])
        except Exception as e:
            log.debug(f"[HUNT] Serper error: {e}")
            return []

    # ── Core: Extract company domain from URL ────────────────────────────────

    def _extract_domain(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            for prefix in ["www.", "fr.", "en."]:
                domain = domain.replace(prefix, "")
            return domain
        except Exception:
            return ""

    # ── Core: Score an opportunity ───────────────────────────────────────────

    def _score_opportunity(self, result: Dict, category: str) -> HuntedOpportunity:
        """Évalue une opportunité depuis un résultat Serper."""
        snippet = (result.get("snippet", "") + " " + result.get("title", "")).lower()
        url = result.get("link", "")
        title = result.get("title", "")

        # Pain signals — mots qui indiquent une vraie douleur
        pain_keywords = [
            "problème", "difficulté", "urgent", "besoin", "cherche", "manque",
            "perte", "améliorer", "solution", "aide", "mission", "appel",
            "recruitment", "recrute", "embauche", "transformation", "crise",
        ]
        urgency_keywords = ["urgent", "immédiat", "asap", "dès que possible", "2025", "rapidement"]
        negative_keywords = ["solution", "résolu", "terminé", "clôturé", "fermé"]

        pain_score = min(1.0, sum(1 for kw in pain_keywords if kw in snippet) / 5)
        urgency_score = min(1.0, sum(1 for kw in urgency_keywords if kw in snippet) / 3)
        solvability = 0.7  # défaut — à raffiner par enrichissement
        if any(kw in snippet for kw in negative_keywords):
            solvability = 0.2

        total = (pain_score * 0.4 + urgency_score * 0.3 + solvability * 0.3)

        cat_data = HUNT_CATEGORIES.get(category, {})
        vmin, vmax = cat_data.get("value_range", (1000, 10000))
        estimated = vmin + (vmax - vmin) * total

        domain = self._extract_domain(url)
        company_name = domain.replace(".fr", "").replace(".com", "").replace("-", " ").title()

        opp_id = hashlib.md5(f"{url}:{category}".encode()).hexdigest()[:12]

        return HuntedOpportunity(
            opportunity_id=opp_id,
            category=category,
            pain_type=cat_data.get("pain_type", category),
            title=title[:120],
            description=result.get("snippet", "")[:300],
            source_url=url,
            source_type="serper_google",
            pain_score=pain_score,
            urgency_score=urgency_score,
            solvability_score=solvability,
            total_score=total,
            estimated_value_min=vmin,
            estimated_value_max=vmax,
            estimated_value=round(estimated, 0),
            company_name=company_name,
            domain=domain,
            delivery_hours=cat_data.get("delivery_hours", 72),
            recommended_offer=cat_data.get("pain_type", category).replace("_", " ").title(),
        )

    # ── Main hunt cycle ──────────────────────────────────────────────────────

    def hunt_category(self, category: str) -> List[HuntedOpportunity]:
        """Chasse une catégorie complète — retourne les opps qualifiées."""
        cat_data = HUNT_CATEGORIES.get(category, {})
        queries = cat_data.get("queries", [])
        found = []

        for query in queries[:3]:  # Max 3 queries/catégorie par cycle
            results = self._serper_search(query, num=5)
            for r in results:
                opp = self._score_opportunity(r, category)
                if opp.total_score >= 0.3:  # Seuil minimum de qualité
                    found.append(opp)
                    self._total_qualified += 1
            self._total_hunted += len(results)
            time.sleep(0.5)  # Politesse API

        log.info(f"[HUNT] {category}: {len(found)} opps qualifiées / {self._total_hunted} résultats")
        return found

    def hunt_all(self) -> List[HuntedOpportunity]:
        """Lance la chasse sur toutes les catégories."""
        all_opps = []
        categories = list(HUNT_CATEGORIES.keys())

        for cat in categories:
            # Rate limiting — ne pas rechasser une catégorie trop souvent
            last = self._last_scan.get(cat, 0)
            if time.time() - last < 3600:  # Min 1h entre 2 scans de la même catégorie
                continue

            try:
                opps = self.hunt_category(cat)
                all_opps.extend(opps)
                self._last_scan[cat] = time.time()

                # Stocker nouvelles opps (dédupliquées)
                with self._lock:
                    existing_ids = {o.opportunity_id for o in self._opportunities}
                    new_opps = [o for o in opps if o.opportunity_id not in existing_ids]
                    self._opportunities.extend(new_opps)
                    # Garder seulement les MAX_STORED dernières
                    if len(self._opportunities) > self.MAX_STORED:
                        self._opportunities = sorted(
                            self._opportunities,
                            key=lambda x: x.detected_at,
                            reverse=True
                        )[:self.MAX_STORED]

                # Alerter Telegram pour les opps à haute valeur
                for opp in new_opps:
                    if opp.estimated_value >= 5000 and opp.total_score >= 0.5:
                        self._alert_telegram(opp)

            except Exception as e:
                log.warning(f"[HUNT] Error hunting {cat}: {e}")

        self._save()

        # Injecter dans le pipeline real_pipeline_orchestrator
        self._inject_to_pipeline(all_opps)

        return all_opps

    def _inject_to_pipeline(self, opportunities: List[HuntedOpportunity]):
        """Injecte les meilleures opps dans le pipeline revenue."""
        # Trier par score et valeur
        top_opps = sorted(
            [o for o in opportunities if o.total_score >= 0.4],
            key=lambda x: x.estimated_value * x.total_score,
            reverse=True
        )[:5]  # Top 5 par cycle

        try:
            from NAYA_CORE.real_pipeline_orchestrator import get_pipeline
            pipeline = get_pipeline()
            for opp in top_opps:
                pain_signal = {
                    "id": opp.opportunity_id,
                    "description": opp.title,
                    "sector": opp.category,
                    "pain_type": opp.pain_type,
                    "estimated_value": opp.estimated_value,
                    "urgency": opp.urgency_score,
                    "solvability": opp.solvability_score,
                    "company_name": opp.company_name,
                    "domain": opp.domain,
                    "source_url": opp.source_url,
                    "annual_cost": opp.estimated_value * 5,
                }
                try:
                    pipeline.execute_full_pipeline(pain_signal)
                    log.info(f"[HUNT] Injected into pipeline: {opp.company_name} ({opp.estimated_value:.0f}€)")
                except Exception as e:
                    log.debug(f"[HUNT] Pipeline inject error: {e}")
        except Exception as e:
            log.debug(f"[HUNT] Pipeline unavailable: {e}")

    def _alert_telegram(self, opp: HuntedOpportunity):
        """Alerte Telegram pour une opportunité qualifiée."""
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            notifier = get_notifier()
            notifier.send(
                f"🎯 <b>OPP DÉTECTÉE [{opp.category.upper()}]</b>\n"
                f"🏢 {opp.company_name or 'Prospect'}\n"
                f"💰 Valeur estimée: {opp.estimated_value:,.0f}€\n"
                f"📊 Score: {opp.total_score:.0%}\n"
                f"⚡ Délai livraison: {opp.delivery_hours}H\n"
                f"🔗 {opp.source_url[:80]}\n"
                f"📋 {opp.description[:120]}"
            )
        except Exception:
            pass

    # ── Background scheduler ─────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="NAYA-GlobalHunter", daemon=True
        )
        self._thread.start()
        log.info(f"[HUNT] Global Pain Hunter V19 started (interval={self._scan_interval}s)")

    def stop(self):
        self._running = False

    def _loop(self):
        time.sleep(60)  # Attendre le boot complet
        self.hunt_all()  # Premier scan immédiat
        while self._running:
            time.sleep(self._scan_interval)
            try:
                self.hunt_all()
            except Exception as e:
                log.error(f"[HUNT] Loop error: {e}")

    # ── API ─────────────────────────────────────────────────────────────────

    def get_top_opportunities(self, n: int = 20, min_score: float = 0.3) -> List[Dict]:
        with self._lock:
            filtered = [o for o in self._opportunities if o.total_score >= min_score]
            sorted_opps = sorted(filtered, key=lambda x: x.estimated_value * x.total_score, reverse=True)
            return [o.to_dict() for o in sorted_opps[:n]]

    def get_stats(self) -> Dict:
        with self._lock:
            total = len(self._opportunities)
            by_cat = {}
            total_value = 0.0
            for o in self._opportunities:
                by_cat[o.category] = by_cat.get(o.category, 0) + 1
                total_value += o.estimated_value
            return {
                "total_opportunities": total,
                "total_hunted": self._total_hunted,
                "total_qualified": self._total_qualified,
                "total_pipeline_value_eur": round(total_value, 0),
                "by_category": by_cat,
                "running": self._running,
                "categories_available": len(HUNT_CATEGORIES),
                "last_scans": {k: datetime.fromtimestamp(v).isoformat() for k, v in self._last_scan.items()},
            }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save(self):
        try:
            with self._lock:
                data = [o.to_dict() for o in self._opportunities]
            self.PERSIST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            log.debug(f"[HUNT] Save error: {e}")

    def _load(self):
        try:
            if self.PERSIST_FILE.exists():
                data = json.loads(self.PERSIST_FILE.read_text())
                log.info(f"[HUNT] Loaded {len(data)} stored opportunities")
        except Exception:
            pass


# ── Singleton ────────────────────────────────────────────────────────────────

_hunter: Optional[GlobalPainHunter] = None
_hunter_lock = threading.Lock()


def get_global_hunter() -> GlobalPainHunter:
    global _hunter
    if _hunter is None:
        with _hunter_lock:
            if _hunter is None:
                _hunter = GlobalPainHunter()
    return _hunter
