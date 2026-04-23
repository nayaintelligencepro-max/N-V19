"""
NAYA V19 — Module Catalogue — PROJECT_04_TINY_HOUSE
====================================================
Catalogue interactif des dispositions de modules 20 m² avec
configurations panneaux solaires et énergie renouvelable.

Permet au propriétaire de choisir ses 2 prototypes personnels en
comparant visuellement :
  · La disposition des pièces (plan texte + description)
  · Le système solaire adapté (ensoleillement Polynésie)
  · Les options d'énergie renouvelable (solaire, récupération eau, ventilation naturelle)
  · Le prix estimé par configuration

Toutes les dispositions respectent le programme minimal :
  ✔ Chambre parentale climatisée + WC/douche ensuite
  ✔ Chambre enfant climatisée
  ✔ WC/douche commun
  ✔ Salon ouvert sur cuisine climatisé
  ✔ Buanderie compacte
  ✔ Énergie renouvelable (solaire + batterie)
  ✔ Surface : 20 m² (+ mezzanine optionnelle selon variante)
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.CATALOGUE.P04")

# ─── Constantes ────────────────────────────────────────────────────────────────

MIN_PRICE_EUR: float = 1_000.0
BASE_SURFACE_M2: int = 20


# ─── Système énergétique ────────────────────────────────────────────────────────

@dataclass
class SolarConfig:
    """Configuration panneau solaire + stockage + production eau."""
    tier: str                        # ESSENTIEL | CONFORT | PREMIUM | AUTONOME_TOTAL
    solar_panels_kwc: float          # Puissance crête installée (kWc)
    battery_kwh: float               # Capacité batterie (kWh)
    panel_count: int                 # Nombre de panneaux
    panel_type: str                  # Monocristallin | Polycristallin | Bifacial
    inverter_type: str               # Hybride | Off-grid | Grid-tie
    autonomy_days: float             # Jours d'autonomie sans soleil
    daily_production_kwh: float      # Production journalière moyenne Polynésie
    daily_consumption_kwh: float     # Consommation estimée module complet
    self_sufficiency_pct: float      # % couverture par solaire
    hot_water: str                   # Chauffe-eau solaire thermique ou électrique
    rainwater_recovery: bool         # Récupération eau de pluie
    natural_ventilation: bool        # Ventilation passive optimisée
    price_eur: float                 # Coût système énergétique

    def to_dict(self) -> Dict:
        return {
            "tier": self.tier,
            "solar_panels_kwc": self.solar_panels_kwc,
            "battery_kwh": self.battery_kwh,
            "panel_count": self.panel_count,
            "panel_type": self.panel_type,
            "inverter_type": self.inverter_type,
            "autonomy_days": self.autonomy_days,
            "daily_production_kwh": self.daily_production_kwh,
            "daily_consumption_kwh": self.daily_consumption_kwh,
            "self_sufficiency_pct": self.self_sufficiency_pct,
            "hot_water": hot_water_label(self.hot_water),
            "rainwater_recovery": self.rainwater_recovery,
            "natural_ventilation": self.natural_ventilation,
            "price_eur": self.price_eur,
            "monthly_energy_cost_eur": round(
                max(0.0, self.daily_consumption_kwh * 30
                    * (1 - self.self_sufficiency_pct / 100) * 0.22), 0
            ),
        }


def hot_water_label(code: str) -> str:
    return {
        "solar_thermal": "Chauffe-eau solaire thermique (0 EUR/mois)",
        "electric_heatpump": "Chauffe-eau thermodynamique (très économe)",
        "electric_standard": "Chauffe-eau électrique standard",
    }.get(code, code)


SOLAR_CONFIGS: Dict[str, SolarConfig] = {
    "ESSENTIEL": SolarConfig(
        tier="ESSENTIEL",
        solar_panels_kwc=1.5,
        battery_kwh=5.0,
        panel_count=4,
        panel_type="Monocristallin 375 Wc",
        inverter_type="Hybride 3 kVA",
        autonomy_days=1.5,
        daily_production_kwh=7.5,
        daily_consumption_kwh=8.0,
        self_sufficiency_pct=85.0,
        hot_water="electric_heatpump",
        rainwater_recovery=False,
        natural_ventilation=True,
        price_eur=3_500,
    ),
    "CONFORT": SolarConfig(
        tier="CONFORT",
        solar_panels_kwc=3.0,
        battery_kwh=10.0,
        panel_count=8,
        panel_type="Monocristallin 375 Wc",
        inverter_type="Hybride 5 kVA",
        autonomy_days=3.0,
        daily_production_kwh=15.0,
        daily_consumption_kwh=10.0,
        self_sufficiency_pct=95.0,
        hot_water="solar_thermal",
        rainwater_recovery=True,
        natural_ventilation=True,
        price_eur=6_500,
    ),
    "PREMIUM": SolarConfig(
        tier="PREMIUM",
        solar_panels_kwc=4.5,
        battery_kwh=20.0,
        panel_count=12,
        panel_type="Bifacial 440 Wc haute efficacité",
        inverter_type="Off-grid 8 kVA",
        autonomy_days=5.0,
        daily_production_kwh=22.5,
        daily_consumption_kwh=12.0,
        self_sufficiency_pct=99.0,
        hot_water="solar_thermal",
        rainwater_recovery=True,
        natural_ventilation=True,
        price_eur=10_500,
    ),
    "AUTONOME_TOTAL": SolarConfig(
        tier="AUTONOME_TOTAL",
        solar_panels_kwc=6.0,
        battery_kwh=30.0,
        panel_count=16,
        panel_type="Bifacial 440 Wc + micro-onduleurs",
        inverter_type="Off-grid 10 kVA + groupe secours hybride",
        autonomy_days=7.0,
        daily_production_kwh=30.0,
        daily_consumption_kwh=14.0,
        self_sufficiency_pct=100.0,
        hot_water="solar_thermal",
        rainwater_recovery=True,
        natural_ventilation=True,
        price_eur=16_000,
    ),
}


# ─── Disposition modules ────────────────────────────────────────────────────────

@dataclass
class RoomSpec:
    name: str
    surface_m2: float
    ac: bool = False
    ensuite_wc: bool = False
    ensuite_shower: bool = False
    level: str = "ground"     # ground | mezzanine | loft

    def label(self) -> str:
        extras = []
        if self.ac:
            extras.append("🌬 Clim")
        if self.ensuite_wc and self.ensuite_shower:
            extras.append("🚿 WC+Douche ensuite")
        elif self.ensuite_wc:
            extras.append("🚽 WC ensuite")
        lev = f" [{self.level}]" if self.level != "ground" else ""
        suffix = f" — {', '.join(extras)}" if extras else ""
        return f"{self.name} {self.surface_m2:.0f}m²{lev}{suffix}"


@dataclass
class ModuleLayout:
    """Disposition complète d'un module 20 m²."""
    code: str                        # ex: M1, M2, M3…
    name: str
    tagline: str
    surface_m2: float
    mezzanine_m2: float
    total_m2: float
    levels: int                      # 1 | 2
    orientation: str                 # est-ouest | nord-sud | libre
    rooms: List[RoomSpec]
    floor_plan_ascii: str            # Plan ASCII simplifié
    structural_type: str             # Acier léger | Bois-acier | CLT | Composite
    facade: str                      # Bois tropique | Bardage métal | Composite HPL
    roof_type: str                   # Monopente | Deux pentes | Toiture terrasse
    base_price_eur: float            # Prix module seul (hors énergie, livraison)
    strengths: List[str]
    constraints: List[str]
    best_for: str

    @property
    def rooms_summary(self) -> str:
        return " · ".join(r.label() for r in self.rooms)

    def to_dict(self, solar_tier: str = "CONFORT") -> Dict:
        solar = SOLAR_CONFIGS.get(solar_tier, SOLAR_CONFIGS["CONFORT"])
        total_price = self.base_price_eur + solar.price_eur
        return {
            "code": self.code,
            "name": self.name,
            "tagline": self.tagline,
            "surface": {
                "floor_m2": self.surface_m2,
                "mezzanine_m2": self.mezzanine_m2,
                "total_m2": self.total_m2,
                "levels": self.levels,
            },
            "orientation": self.orientation,
            "rooms": [
                {"name": r.name, "m2": r.surface_m2, "ac": r.ac,
                 "ensuite": r.ensuite_wc and r.ensuite_shower, "level": r.level}
                for r in self.rooms
            ],
            "rooms_summary": self.rooms_summary,
            "floor_plan": self.floor_plan_ascii,
            "construction": {
                "structural_type": self.structural_type,
                "facade": self.facade,
                "roof_type": self.roof_type,
            },
            "pricing": {
                "module_base_eur": self.base_price_eur,
                "solar_system_eur": solar.price_eur,
                "total_eur": total_price,
                "solar_tier": solar_tier,
            },
            "energy": solar.to_dict(),
            "strengths": self.strengths,
            "constraints": self.constraints,
            "best_for": self.best_for,
        }


# ─── Les 6 dispositions disponibles ────────────────────────────────────────────

MODULE_LAYOUTS: Dict[str, ModuleLayout] = {

    "M1": ModuleLayout(
        code="M1",
        name="ALPHA — Plain Tropical",
        tagline="Tout au même niveau · Maximal en utilisation · Idéal terrain plat",
        surface_m2=20.0, mezzanine_m2=0.0, total_m2=20.0, levels=1,
        orientation="nord-sud (entrée nord, chambres sud au calme)",
        rooms=[
            RoomSpec("Chambre parentale",  7.0, ac=True, ensuite_wc=True, ensuite_shower=True),
            RoomSpec("Chambre enfant",     4.5, ac=True),
            RoomSpec("WC + Douche commun", 3.0),
            RoomSpec("Salon / Cuisine ouvert", 4.5, ac=True),
            RoomSpec("Buanderie",          1.0),
        ],
        floor_plan_ascii="""
┌──────────────────────────────────────┐
│  CH. PARENTALE 7m²  ║  SALON/CUISINE │
│  [Clim + WC/Douche] ║  4.5m² [Clim] │
│                     ║               │
├─────────────────────╢  CH. ENFANT   │
│  WC/Douche commun   ║  4.5m² [Clim] │
│  3m²                ║               │
├─────────────────────╨───────────────┤
│         BUANDERIE 1m²               │
└──────────────────────────────────────┘
""",
        structural_type="Acier léger galvanisé (résistant cyclone)",
        facade="Bardage composite bois-aluminium",
        roof_type="Monopente 15° (évacuation pluie tropicale optimale)",
        base_price_eur=16_500,
        strengths=[
            "Aucune contrainte d'escalier — accès total PMR possible",
            "Montage le plus rapide (1.5 jours)",
            "Coût de structure le plus bas",
            "Toiture monopente = récupération eau de pluie maximale",
        ],
        constraints=[
            "Hauteur sous plafond unique (2.5m)",
            "Séparation acoustique salon/chambres à soigner",
        ],
        best_for="Terrain plat · Résidence permanente · Couple + 1 enfant",
    ),

    "M2": ModuleLayout(
        code="M2",
        name="BETA — Mezzanine Loft",
        tagline="Chambre parentale en hauteur · Vue dégagée · Intimité maximale",
        surface_m2=20.0, mezzanine_m2=8.0, total_m2=28.0, levels=2,
        orientation="est-ouest (mezzanine côté lever soleil)",
        rooms=[
            RoomSpec("Chambre parentale (mezzanine)", 8.0, ac=True,
                     ensuite_wc=True, ensuite_shower=True, level="mezzanine"),
            RoomSpec("Chambre enfant",                5.0, ac=True, level="ground"),
            RoomSpec("WC + Douche commun",            3.0,          level="ground"),
            RoomSpec("Salon / Cuisine ouvert",        9.5, ac=True, level="ground"),
            RoomSpec("Buanderie",                     2.5,          level="ground"),
        ],
        floor_plan_ascii="""
MEZZANINE (niveau +1) :
┌──────────────────────────────────┐
│  CHAMBRE PARENTALE 8m²           │
│  [Clim + WC/Douche ensuite]      │
│  → Échelle/escalier accès        │
└──────────────────────────────────┘

REZ-DE-CHAUSSÉE (niveau 0) :
┌──────────────────────────────────┐
│  SALON/CUISINE 9.5m² [Clim]      │ ← Double hauteur sous plafond
│  (espace ouvert, 4m de haut)     │
├──────────────────────────────────┤
│  CH. ENFANT 5m²  │ WC/Douche 3m²│
│  [Clim]          │ commun        │
├──────────────────┴───────────────┤
│  BUANDERIE 2.5m²                 │
└──────────────────────────────────┘
""",
        structural_type="Acier léger + plancher CLT mezzanine",
        facade="Bardage bois tropical (Merbau certifié FSC)",
        roof_type="Deux pentes avec pignon vitré côté mezzanine",
        base_price_eur=20_000,
        strengths=[
            "Double hauteur salon = sensation d'espace ×2",
            "Séparation totale nuit/jour entre parents et enfant",
            "Vue panoramique depuis mezzanine",
            "28 m² utiles pour 20 m² d'emprise au sol",
        ],
        constraints=[
            "Escalier/échelle requis (2-3 m² perdus)",
            "Montage +0.5 jour vs M1",
            "Prix structure légèrement supérieur",
        ],
        best_for="Vue dégagée · Intimité parentale · Amateurs d'architecture",
    ),

    "M3": ModuleLayout(
        code="M3",
        name="GAMMA — Patio Ouvert",
        tagline="Terrasse intégrée · Mode de vie extérieur polynésien · Ventilation naturelle",
        surface_m2=20.0, mezzanine_m2=0.0, total_m2=20.0, levels=1,
        orientation="nord (terrasse plein sud, protégée)",
        rooms=[
            RoomSpec("Chambre parentale", 6.0, ac=True, ensuite_wc=True, ensuite_shower=True),
            RoomSpec("Chambre enfant",    4.0, ac=True),
            RoomSpec("WC + Douche commun", 2.5),
            RoomSpec("Salon / Cuisine ouvert", 3.5, ac=True),
            RoomSpec("Terrasse couverte intégrée", 4.0),  # non comptée dans 20m²
            RoomSpec("Buanderie",         0.0),           # mutualisée terrasse
        ],
        floor_plan_ascii="""
┌──────────────────────────────────┐
│  CH. PARENTALE 6m²               │
│  [Clim + WC/Douche]              │
├──────────────────────────────────┤
│  CH. ENFANT 4m² [Clim]           │
├──────────────────────────────────┤
│  WC/Douche commun 2.5m²          │
├──────────────────────────────────┤
│  SALON/CUISINE 3.5m² [Clim]      │
├══════════════════════════════════╡
│  TERRASSE COUVERTE 4m²           │ ← Débordement toiture, vie extérieure
│  (buanderie angle terrasse)      │
└──────────────────────────────────┘
""",
        structural_type="Acier léger + extensions bois",
        facade="Bois tropical + bambou traité",
        roof_type="Monopente prolongée en auvent terrasse (débordement 2m)",
        base_price_eur=17_500,
        strengths=[
            "Terrasse couverte 4m² = pièce de vie extérieure permanente",
            "Ventilation naturelle by design (cross-ventilation N→S)",
            "Très adapté au climat polynésien",
            "Facture clim réduite grâce aux brise-soleil",
        ],
        constraints=[
            "Intérieur légèrement plus compact (16m² clos)",
            "Nécessite terrain avec exposition sud dégagée",
        ],
        best_for="Mode de vie extérieur · Zones sans vent dominant · Tourisme/glamping",
    ),

    "M4": ModuleLayout(
        code="M4",
        name="DELTA — Duplex Compact",
        tagline="2 niveaux complets · Chambres à l'étage · Séjour haut plafond",
        surface_m2=20.0, mezzanine_m2=15.0, total_m2=35.0, levels=2,
        orientation="libre",
        rooms=[
            RoomSpec("Chambre parentale", 9.0, ac=True, ensuite_wc=True, ensuite_shower=True, level="mezzanine"),
            RoomSpec("Chambre enfant",    6.0, ac=True,                                       level="mezzanine"),
            RoomSpec("WC + Douche commun", 3.0,                                               level="ground"),
            RoomSpec("Salon / Cuisine ouvert", 10.0, ac=True,                                 level="ground"),
            RoomSpec("Buanderie",          2.0,                                               level="ground"),
        ],
        floor_plan_ascii="""
ÉTAGE (niveau +1) — 15m² :
┌──────────────────────────────────┐
│  CH. PARENTALE 9m² [Clim]        │
│  [WC + Douche ensuite]           │
│                                  │
│  CH. ENFANT 6m² [Clim]           │
└──────────────────────────────────┘
           ▼ Escalier intérieur

REZ-DE-CHAUSSÉE (niveau 0) — 20m² :
┌──────────────────────────────────┐
│  SALON / CUISINE 10m² [Clim]     │
│  (double hauteur partielle)      │
├──────────────────────────────────┤
│  WC/Douche commun 3m² │ BUE 2m² │
└──────────────────────────────────┘
""",
        structural_type="Acier léger double ossature + plancher béton léger",
        facade="Composite HPL ultra-résistant",
        roof_type="Toiture terrasse (accessible depuis étage, panneaux solaires optimaux)",
        base_price_eur=24_000,
        strengths=[
            "35 m² utiles pour 20 m² au sol = meilleur ratio",
            "Toiture terrasse plate = surface solaire maximale (toute orientation libre)",
            "Escalier intérieur discret et sécurisé",
            "Chambres totalement isolées du séjour (acoustique optimale)",
        ],
        constraints=[
            "Prix de structure le plus élevé",
            "Montage 2.5 jours (le plus long)",
            "Escalier intérieur permanent requis",
        ],
        best_for="Famille complète · Usage intensif · Zone urbaine (emprise sol minimale)",
    ),

    "M5": ModuleLayout(
        code="M5",
        name="EPSILON — Suite Parentale Prioritaire",
        tagline="Chambre parentale XL · Suite hôtelière · Espaces enfant optimisés",
        surface_m2=20.0, mezzanine_m2=0.0, total_m2=20.0, levels=1,
        orientation="est-ouest (suite parentale plein est, lever soleil)",
        rooms=[
            RoomSpec("Suite parentale XL", 10.0, ac=True, ensuite_wc=True, ensuite_shower=True),
            RoomSpec("Chambre enfant",      4.0, ac=True),
            RoomSpec("WC + Douche commun",  2.5),
            RoomSpec("Kitchenette + Coin repas", 3.5, ac=True),
            RoomSpec("Buanderie",           0.0),  # encastrée dans suite parentale
        ],
        floor_plan_ascii="""
┌─────────────────────┬────────────────┐
│  SUITE PARENTALE    │  CH. ENFANT    │
│  10m²               │  4m² [Clim]   │
│  [Clim + WC/Douche] ├────────────────┤
│  + coin lecture/    │  WC/Douche     │
│  dressing           │  commun 2.5m²  │
├─────────────────────┴────────────────┤
│  KITCHENETTE + COIN REPAS 3.5m²      │
│  [Clim] — Buanderie encastrée        │
└──────────────────────────────────────┘
""",
        structural_type="Acier léger galvanisé",
        facade="Bardage aluminium laqué blanc (réflexion chaleur tropicale)",
        roof_type="Monopente avec casquette solaire intégrée (ombre balcon)",
        base_price_eur=17_000,
        strengths=[
            "Suite parentale digne d'un boutique-hôtel",
            "Coin dressing/lecture intégré dans la suite",
            "Concept premium = valorisation revente/location",
            "Adapté couple sans enfant ou enfant grand",
        ],
        constraints=[
            "Kitchenette compacte (pas de cuisine équipée professionnelle)",
            "Chambre enfant plus petite que M1/M2",
        ],
        best_for="Propriétaire cherchant confort personnel maximal · Location premium",
    ),

    "M6": ModuleLayout(
        code="M6",
        name="ZETA — Off-Grid Maximum",
        tagline="100% autonome · Zéro réseau · Panneaux intégrés structure · Toiture solaire totale",
        surface_m2=20.0, mezzanine_m2=4.0, total_m2=24.0, levels=2,
        orientation="nord-sud (toiture orientée plein nord dans hémisphère sud — optimal PF)",
        rooms=[
            RoomSpec("Chambre parentale", 7.0, ac=True, ensuite_wc=True, ensuite_shower=True, level="mezzanine"),
            RoomSpec("Chambre enfant",    4.5, ac=True,                                       level="ground"),
            RoomSpec("WC + Douche commun", 2.5,                                               level="ground"),
            RoomSpec("Salon / Cuisine ouvert", 5.5, ac=True,                                  level="ground"),
            RoomSpec("Buanderie solaire", 0.5,                                                level="ground"),
        ],
        floor_plan_ascii="""
TOITURE : 20m² de panneaux solaires intégrés (BIPV)
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓  PANNEAUX SOLAIRES INTÉGRÉS 20m² ▓  ← Toiture-solaire bifaciale
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

MEZZANINE (4m²) :
┌──────────────────────┐
│  CH. PARENTALE 7m²   │
│  [Clim + WC/Douche]  │
└──────────────────────┘

REZ-DE-CHAUSSÉE :
┌──────────────────────────────────┐
│  SALON/CUISINE 5.5m² [Clim]      │
├──────────────────────────────────┤
│  CH. ENFANT 4.5m² [Clim]         │
├──────────────────────────────────┤
│  WC/Douche 2.5m² │ BUE 0.5m²    │
└──────────────────────────────────┘
""",
        structural_type="Acier inox marin + panneaux BIPV (toiture-solaire)",
        facade="Composite ultra-léger + brise-soleil intégrés",
        roof_type="Toiture-solaire intégrée BIPV 20m² (panneaux = toiture)",
        base_price_eur=28_000,
        strengths=[
            "Toiture entière = surface solaire (20m² BIPV = ~8 kWc)",
            "0 EUR de facture énergie — autonomie totale garantie",
            "Pas besoin de branchement eau/élec extérieur",
            "Récupération eau de pluie 5 000L/an (Polynésie)",
            "Résistance maximale : structure inox marin anti-cyclone",
        ],
        constraints=[
            "Prix le plus élevé du catalogue",
            "Maintenance BIPV annuelle recommandée",
            "Terrain avec exposition solaire non masquée requis",
        ],
        best_for="Île isolée · Site off-grid total · Investissement long terme · Vision durable",
    ),
}


# ─── Moteur catalogue ───────────────────────────────────────────────────────────

class ModuleCatalogue:
    """
    Catalogue interactif des modules 20 m² TINY_HOUSE.

    Permet de :
      · Lister toutes les dispositions disponibles
      · Filtrer par critères (budget, niveaux, style)
      · Comparer 2 modules côte à côte
      · Sélectionner les 2 prototypes avec configuration solaire
      · Générer un brief de sélection pour commande fournisseur
    """

    PROJECT_ID = "PROJECT_04_TINY_HOUSE"
    DEFAULT_SOLAR_TIER = "CONFORT"

    # ── Listing & filtres ─────────────────────────────────────────────────

    def list_all(self, solar_tier: str = DEFAULT_SOLAR_TIER) -> List[Dict]:
        """Retourne tous les modules avec prix incluant le système solaire choisi."""
        return [m.to_dict(solar_tier) for m in MODULE_LAYOUTS.values()]

    def filter(
        self,
        max_budget_eur: Optional[float] = None,
        levels: Optional[int] = None,
        mezzanine: Optional[bool] = None,
        solar_tier: str = DEFAULT_SOLAR_TIER,
        has_ensuite: bool = True,
    ) -> List[Dict]:
        """
        Filtre les modules selon les critères.
        Tous les résultats incluent chambre parentale + enfant + WC/douche (programme minimal).
        """
        solar = SOLAR_CONFIGS.get(solar_tier, SOLAR_CONFIGS[self.DEFAULT_SOLAR_TIER])
        results = []
        for m in MODULE_LAYOUTS.values():
            total_price = m.base_price_eur + solar.price_eur
            if max_budget_eur and total_price > max_budget_eur:
                continue
            if levels is not None and m.levels != levels:
                continue
            if mezzanine is not None:
                has_mez = m.mezzanine_m2 > 0
                if has_mez != mezzanine:
                    continue
            if has_ensuite:
                parents_room = next(
                    (r for r in m.rooms if r.ensuite_wc and r.ensuite_shower), None
                )
                if not parents_room:
                    continue
            results.append(m.to_dict(solar_tier))
        return sorted(results, key=lambda x: x["pricing"]["total_eur"])

    # ── Comparaison ────────────────────────────────────────────────────────

    def compare(self, code_a: str, code_b: str,
                solar_tier: str = DEFAULT_SOLAR_TIER) -> Dict:
        """Compare 2 modules côte à côte."""
        ma = MODULE_LAYOUTS.get(code_a.upper())
        mb = MODULE_LAYOUTS.get(code_b.upper())
        if not ma:
            return {"error": f"Module inconnu: {code_a}", "available": list(MODULE_LAYOUTS.keys())}
        if not mb:
            return {"error": f"Module inconnu: {code_b}", "available": list(MODULE_LAYOUTS.keys())}
        da = ma.to_dict(solar_tier)
        db = mb.to_dict(solar_tier)
        return {
            "comparison": {
                "module_a": {"code": code_a, **da},
                "module_b": {"code": code_b, **db},
            },
            "delta": {
                "price_diff_eur": round(db["pricing"]["total_eur"] - da["pricing"]["total_eur"], 0),
                "surface_diff_m2": round(db["surface"]["total_m2"] - da["surface"]["total_m2"], 1),
                "solar_diff_kwc": round(
                    SOLAR_CONFIGS[solar_tier].solar_panels_kwc
                    - SOLAR_CONFIGS[solar_tier].solar_panels_kwc, 1
                ),
                "cheaper": code_a if da["pricing"]["total_eur"] <= db["pricing"]["total_eur"] else code_b,
                "more_space": code_a if da["surface"]["total_m2"] >= db["surface"]["total_m2"] else code_b,
            },
            "solar_tier": solar_tier,
            "solar_config": SOLAR_CONFIGS[solar_tier].to_dict(),
        }

    # ── Sélection prototypes ───────────────────────────────────────────────

    def select_prototypes(
        self,
        module_a_code: str,
        module_b_code: str,
        solar_tier_a: str = DEFAULT_SOLAR_TIER,
        solar_tier_b: str = DEFAULT_SOLAR_TIER,
        notes: str = "",
    ) -> Dict:
        """
        Confirme la sélection des 2 modules prototypes avec leur configuration solaire.
        Génère le brief de commande pour négociation fournisseur.
        """
        ma = MODULE_LAYOUTS.get(module_a_code.upper())
        mb = MODULE_LAYOUTS.get(module_b_code.upper())
        errors = []
        if not ma:
            errors.append(f"Module A inconnu: {module_a_code}")
        if not mb:
            errors.append(f"Module B inconnu: {module_b_code}")
        if errors:
            return {"error": errors, "available_codes": list(MODULE_LAYOUTS.keys())}

        solar_a = SOLAR_CONFIGS.get(solar_tier_a, SOLAR_CONFIGS[self.DEFAULT_SOLAR_TIER])
        solar_b = SOLAR_CONFIGS.get(solar_tier_b, SOLAR_CONFIGS[self.DEFAULT_SOLAR_TIER])

        unit_a_total = ma.base_price_eur + solar_a.price_eur
        unit_b_total = mb.base_price_eur + solar_b.price_eur
        grand_total  = unit_a_total + unit_b_total

        selection = {
            "selection_id": f"SEL-{int(time.time())}",
            "project": self.PROJECT_ID,
            "purpose": "Validation prototype — qualification fournisseur",
            "units": [
                {
                    "unit": "A",
                    "module_code": module_a_code.upper(),
                    "module_name": ma.name,
                    "tagline": ma.tagline,
                    "surface_m2": ma.surface_m2,
                    "mezzanine_m2": ma.mezzanine_m2,
                    "total_m2": ma.total_m2,
                    "levels": ma.levels,
                    "structural_type": ma.structural_type,
                    "roof_type": ma.roof_type,
                    "rooms_summary": ma.rooms_summary,
                    "floor_plan": ma.floor_plan_ascii,
                    "solar_tier": solar_tier_a,
                    "solar": solar_a.to_dict(),
                    "module_price_eur": ma.base_price_eur,
                    "solar_price_eur": solar_a.price_eur,
                    "total_eur": unit_a_total,
                    "strengths": ma.strengths,
                    "best_for": ma.best_for,
                },
                {
                    "unit": "B",
                    "module_code": module_b_code.upper(),
                    "module_name": mb.name,
                    "tagline": mb.tagline,
                    "surface_m2": mb.surface_m2,
                    "mezzanine_m2": mb.mezzanine_m2,
                    "total_m2": mb.total_m2,
                    "levels": mb.levels,
                    "structural_type": mb.structural_type,
                    "roof_type": mb.roof_type,
                    "rooms_summary": mb.rooms_summary,
                    "floor_plan": mb.floor_plan_ascii,
                    "solar_tier": solar_tier_b,
                    "solar": solar_b.to_dict(),
                    "module_price_eur": mb.base_price_eur,
                    "solar_price_eur": solar_b.price_eur,
                    "total_eur": unit_b_total,
                    "strengths": mb.strengths,
                    "best_for": mb.best_for,
                },
            ],
            "totals": {
                "unit_a_eur": unit_a_total,
                "unit_b_eur": unit_b_total,
                "grand_total_eur": grand_total,
                "note": "Prix indicatif ex-usine. Hors livraison Polynésie (~3 000–5 000 EUR/conteneur).",
            },
            "notes": notes,
            "created_at": time.time(),
        }
        log.info(
            f"[CATALOGUE] Sélection prototypes: {module_a_code}+{module_b_code} | "
            f"{grand_total:,.0f} EUR total"
        )
        return selection

    # ── Systèmes solaires ──────────────────────────────────────────────────

    def list_solar_configs(self) -> List[Dict]:
        """Retourne tous les tiers solaires disponibles."""
        return [sc.to_dict() for sc in SOLAR_CONFIGS.values()]

    def get_solar_config(self, tier: str) -> Dict:
        """Retourne les détails d'un tier solaire."""
        sc = SOLAR_CONFIGS.get(tier.upper())
        if not sc:
            return {"error": f"Tier inconnu: {tier}",
                    "available_tiers": list(SOLAR_CONFIGS.keys())}
        return sc.to_dict()

    def recommend_solar(self, module_code: str, usage: str = "permanent") -> Dict:
        """
        Recommande le tier solaire adapté selon l'usage.
        usage : permanent | seasonal | rental | offgrid
        """
        m = MODULE_LAYOUTS.get(module_code.upper())
        if not m:
            return {"error": f"Module inconnu: {module_code}"}
        recommendations = {
            "permanent": "CONFORT",      # Résidence principale
            "seasonal":  "ESSENTIEL",    # Usage saisonnier
            "rental":    "PREMIUM",      # Location = fiabilité maximale
            "offgrid":   "AUTONOME_TOTAL",  # Île isolée
        }
        tier = recommendations.get(usage, "CONFORT")
        sc = SOLAR_CONFIGS[tier]
        return {
            "module_code": module_code.upper(),
            "usage": usage,
            "recommended_tier": tier,
            "reason": {
                "permanent": "Confort quotidien, 95% autonomie, chauffe-eau solaire inclus",
                "seasonal": "Essentiel suffit pour usage ponctuel, coût optimisé",
                "rental": "Premium = fiabilité maximale, 0 panne = 0 remboursement locataire",
                "offgrid": "Autonomie totale 7 jours sans soleil, 0 dépendance réseau",
            }.get(usage, ""),
            "solar_config": sc.to_dict(),
            "total_with_module_eur": m.base_price_eur + sc.price_eur,
        }

    # ── Affichage texte ────────────────────────────────────────────────────

    def print_catalogue(self, solar_tier: str = DEFAULT_SOLAR_TIER) -> str:
        """Retourne le catalogue complet en texte lisible."""
        lines = [
            "═" * 70,
            "  NAYA TINY HOUSE — CATALOGUE DES MODULES 20 m²",
            f"  Système solaire inclus : {solar_tier}",
            "  Programme minimum garanti dans tous les modules :",
            "  ✔ Chambre parentale (Clim + WC/Douche ensuite)",
            "  ✔ Chambre enfant (Clim)  ✔ WC/Douche commun",
            "  ✔ Salon/Cuisine (Clim)   ✔ Buanderie  ✔ Énergie renouvelable",
            "═" * 70,
        ]
        solar = SOLAR_CONFIGS.get(solar_tier, SOLAR_CONFIGS[self.DEFAULT_SOLAR_TIER])
        for m in MODULE_LAYOUTS.values():
            total = m.base_price_eur + solar.price_eur
            lines += [
                "",
                f"  [{m.code}] {m.name}",
                f"  {m.tagline}",
                f"  Surface : {m.surface_m2}m² sol"
                + (f" + {m.mezzanine_m2}m² mezzanine = {m.total_m2}m² total" if m.mezzanine_m2 else ""),
                f"  Structure : {m.structural_type}",
                f"  Toiture : {m.roof_type}",
                "  Pièces :",
            ]
            for r in m.rooms:
                if r.surface_m2 > 0:
                    lines.append(f"    • {r.label()}")
            lines += [
                f"  Solaire inclus : {solar.solar_panels_kwc} kWc · {solar.battery_kwh} kWh batterie"
                f" · {solar.self_sufficiency_pct:.0f}% autonomie",
                f"  💶 Module seul : {m.base_price_eur:,.0f} EUR",
                f"     + Solaire {solar_tier} : {solar.price_eur:,.0f} EUR",
                f"     = TOTAL : {total:,.0f} EUR",
                f"  ✅ Idéal pour : {m.best_for}",
                "  " + "─" * 66,
            ]
        lines += [
            "",
            "  SYSTÈMES SOLAIRES DISPONIBLES :",
            "  " + "─" * 50,
        ]
        for sc in SOLAR_CONFIGS.values():
            lines.append(
                f"  [{sc.tier:15}] {sc.solar_panels_kwc} kWc · {sc.battery_kwh:4} kWh · "
                f"{sc.autonomy_days} j autonomie · {sc.self_sufficiency_pct:.0f}% · "
                f"{sc.price_eur:,} EUR"
            )
        lines += ["", "═" * 70]
        return "\n".join(lines)

    # ── Infos module unique ────────────────────────────────────────────────

    def get_module(self, code: str, solar_tier: str = DEFAULT_SOLAR_TIER) -> Dict:
        """Retourne les détails complets d'un module."""
        m = MODULE_LAYOUTS.get(code.upper())
        if not m:
            return {"error": f"Module inconnu: {code}",
                    "available_codes": list(MODULE_LAYOUTS.keys())}
        return m.to_dict(solar_tier)
