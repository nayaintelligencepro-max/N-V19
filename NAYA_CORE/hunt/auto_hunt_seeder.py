"""
NAYA V19 - Auto Hunt Seeder
Genere automatiquement des requetes de chasse sur TOUS les secteurs.
Utilise Serper (2 cles, 5000 req/mois) pour trouver de vrais prospects
avec de vraies douleurs solvables.
"""
import time, logging, threading, random, os
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.HUNT.SEEDER")

class AutoHuntSeeder:
    """Alimente le systeme avec des cibles de chasse reelles, partout."""

    # Requetes de chasse par type de douleur — optimisees pour Serper
    HUNT_QUERIES = {
        "cash_rapide_audit": [
            "entreprise cherche audit digital site:linkedin.com",
            "PME besoin diagnostic numerique",
            "entreprise probleme site web avis negatifs",
            "restaurant perte clients 2025",
            "commerce baisse chiffre affaires",
            "entreprise recherche automatisation processus",
            "PME transformation digitale urgente",
            "hotel probleme reservation en ligne",
            "cabinet comptable recherche logiciel",
            "agence immobiliere besoin visibilite",
        ],
        "cash_rapide_chatbot": [
            "entreprise cherche chatbot site:linkedin.com",
            "PME automatiser service client",
            "commerce en ligne trop de demandes support",
            "entreprise besoin assistant virtuel",
            "startup recherche solution IA service client",
        ],
        "cash_rapide_saas": [
            "entreprise cherche solution SaaS gestion",
            "PME besoin logiciel sur mesure",
            "entreprise recherche plateforme automatisation",
            "startup besoin outil interne",
        ],
        "douleur_entreprise": [
            '"nous recherchons" "solution" site:linkedin.com',
            '"appel offre" diagnostic digital 2025',
            '"besoin urgent" entreprise service',
            "entreprise perte efficacite processus manuel",
            "societe probleme gestion stocks",
            "entreprise cout eleve main oeuvre repetitive",
            "PME conformite RGPD retard",
            "entreprise cybersecurite vulnerabilite",
        ],
        "marche_oublie": [
            "territoire sous-desservi services numeriques",
            "ile pacifique besoin technologie",
            "zone rurale manque services en ligne",
            "polynesie francaise entreprise digital",
            "DOM-TOM transformation numerique",
        ],
        "mega_projet": [
            "appel offre transformation digitale million",
            "marche public plateforme numerique 2025",
            "grand compte recherche partenaire IA",
            "infrastructure gouvernement modernisation",
        ],
        "immobilier": [
            "terrain a vendre polynesie francaise",
            "maison a renover tahiti prix bas",
            "investissement immobilier outre-mer rentable",
            "location saisonniere ile pacifique demande",
        ],
    }

    # Secteurs a scanner en rotation
    SECTOR_ROTATION = [
        "restaurant", "hotel", "commerce", "immobilier", "sante",
        "cabinet_comptable", "avocat", "assurance", "transport",
        "formation", "coaching", "artisan", "startup", "pme_industrie",
        "agriculture", "tourisme", "construction", "energie",
    ]

    def __init__(self):
        self._current_sector_idx = 0
        self._current_query_type_idx = 0
        self._total_seeds = 0
        self._results_found = 0
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._scan_interval = int(os.getenv("NAYA_AUTO_HUNT_INTERVAL_SECONDS", "3600"))

    def seed_once(self) -> List[Dict]:
        """Execute un cycle de chasse: cherche des prospects reels via Serper."""
        results = []
        try:
            from NAYA_CORE.integrations.serper_multi import SerperMultiKeySearch
            serper = SerperMultiKeySearch()

            # Choisir le type de requete
            query_types = list(self.HUNT_QUERIES.keys())
            qtype = query_types[self._current_query_type_idx % len(query_types)]
            queries = self.HUNT_QUERIES[qtype]

            # Prendre 2 requetes aleatoires
            selected = random.sample(queries, min(2, len(queries)))

            for query in selected:
                try:
                    search_results = serper.search(query, num=10)
                    if search_results and isinstance(search_results, list):
                        for sr in search_results:
                            prospect = self._extract_prospect(sr, qtype)
                            if prospect:
                                results.append(prospect)
                                self._results_found += 1
                    elif search_results and isinstance(search_results, dict):
                        organic = search_results.get("organic", [])
                        for sr in organic[:10]:
                            prospect = self._extract_prospect(sr, qtype)
                            if prospect:
                                results.append(prospect)
                                self._results_found += 1
                    time.sleep(1.5)  # Rate limiting
                except Exception as e:
                    log.warning(f"[SEEDER] Query failed: {e}")

            self._current_query_type_idx += 1
            self._total_seeds += 1

            # Valider les prospects avant injection
            if results:
                try:
                    from NAYA_CORE.hunt.prospect_validator import get_prospect_validator
                    validator = get_prospect_validator()
                    results = validator.validate_batch(results)
                except Exception as ve:
                    log.debug(f"[SEEDER] Validator: {ve}")

                # Tracker les conversions
                try:
                    from NAYA_CORE.analytics.conversion_tracker import get_conversion_tracker
                    tracker = get_conversion_tracker()
                    for r in results:
                        tracker.record("prospect_found", source="serper_hunt",
                                       sector=r.get("sector", ""))
                except Exception:
                    pass

                self._inject_to_classifier(results, qtype)

            log.info(f"[SEEDER] Cycle {self._total_seeds}: {len(results)} prospects trouves ({qtype})")

        except Exception as e:
            log.error(f"[SEEDER] Seed failed: {e}")

        return results

    def _extract_prospect(self, search_result: Dict, query_type: str) -> Optional[Dict]:
        """Extrait un prospect depuis un resultat Serper."""
        title = search_result.get("title", "")
        snippet = search_result.get("snippet", "")
        link = search_result.get("link", "")

        if not title or not snippet:
            return None

        # Filtrer les resultats non pertinents
        skip_domains = ["wikipedia", "youtube", "facebook.com/watch", "tiktok.com"]
        if any(d in link.lower() for d in skip_domains):
            return None

        # Estimer la valeur selon le type
        value_map = {
            "cash_rapide_audit": random.randint(1000, 10000),
            "cash_rapide_chatbot": random.randint(2000, 15000),
            "cash_rapide_saas": random.randint(5000, 30000),
            "douleur_entreprise": random.randint(3000, 50000),
            "marche_oublie": random.randint(2000, 20000),
            "mega_projet": random.randint(100000, 5000000),
            "immobilier": random.randint(10000, 200000),
        }

        return {
            "source": "serper_hunt",
            "query_type": query_type,
            "entity": title[:100],
            "description": snippet[:300],
            "url": link,
            "sector": self._detect_sector(title + " " + snippet),
            "estimated_value": value_map.get(query_type, 5000),
            "urgency": 0.6 if "urgent" in snippet.lower() else 0.5,
            "solvability": 0.7,
            "complexity": 0.4,
            "detected_at": time.time(),
            "offer_type": query_type.replace("cash_rapide_", ""),
        }

    def _detect_sector(self, text: str) -> str:
        text_lower = text.lower()
        SECTOR_KW = {
            "restaurant": ["restaurant", "cuisine", "chef", "menu"],
            "hotel": ["hotel", "hebergement", "tourisme", "booking"],
            "immobilier": ["immobilier", "agence", "bien", "location", "terrain"],
            "sante": ["medical", "clinique", "pharmacie", "docteur", "sante"],
            "tech": ["startup", "saas", "logiciel", "digital", "tech"],
            "commerce": ["boutique", "magasin", "commerce", "vente"],
            "finance": ["banque", "comptable", "finance", "assurance"],
            "education": ["formation", "ecole", "coaching", "cours"],
            "construction": ["construction", "batiment", "travaux", "renovation"],
        }
        for sector, kws in SECTOR_KW.items():
            if any(k in text_lower for k in kws):
                return sector
        return "pme"

    def _inject_to_classifier(self, prospects: List[Dict], query_type: str) -> None:
        """Injecte les prospects dans le cash rapide classifier."""
        try:
            from NAYA_CORE.hunt.cash_rapide_classifier import get_classifier
            clf = get_classifier()
            for p in prospects:
                clf.classify(p)
        except Exception as e:
            log.warning(f"[SEEDER] Classifier injection: {e}")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="HUNT-SEEDER", daemon=True)
        self._thread.start()
        log.info(f"[SEEDER] Auto-hunt seeder demarre (interval={self._scan_interval}s)")

    def stop(self):
        self._running = False

    def _loop(self):
        time.sleep(30)  # Attendre le boot
        # Premier scan immediat
        self.seed_once()
        while self._running:
            time.sleep(self._scan_interval)
            try:
                self.seed_once()
            except Exception as e:
                log.error(f"[SEEDER] Loop error: {e}")

    def get_stats(self) -> Dict:
        return {
            "total_seeds": self._total_seeds,
            "results_found": self._results_found,
            "scan_interval_s": self._scan_interval,
            "running": self._running,
            "query_types": len(self.HUNT_QUERIES),
            "total_queries": sum(len(v) for v in self.HUNT_QUERIES.values()),
            "sectors": len(self.SECTOR_ROTATION)
        }

_seeder = None
_seeder_lock = threading.Lock()
def get_seeder() -> AutoHuntSeeder:
    global _seeder
    if _seeder is None:
        with _seeder_lock:
            if _seeder is None:
                _seeder = AutoHuntSeeder()
    return _seeder
