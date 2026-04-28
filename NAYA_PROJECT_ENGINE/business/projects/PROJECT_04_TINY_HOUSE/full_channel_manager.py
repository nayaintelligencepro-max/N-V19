"""
NAYA V19 — Full Channel Manager — PROJECT_04_TINY_HOUSE
========================================================
Gère TOUT le pipeline opérationnel du projet TINY_HOUSE :

  CANAUX & PLATEFORMES  : LinkedIn, Instagram, TikTok, Pinterest,
                          YouTube, Facebook, WhatsApp Business, site web
  STORYTELLING          : Narrative basée sur douleur réelle détectée
  COMMENTAIRES          : Templates réponses, modération, escalade
  MESSAGES              : DMs, séquences de suivi, réponses objections
  CRÉDIBILITÉ           : Preuves sociales, certifications, médias
  FOURNISSEURS          : Qualification usines, négociation, scoring
  USINES                : Suivi fabrication, contrôle qualité
  EXPÉDITIONS/LIVRAISON : Routes, douanes, tracking, livraison finale
  MONTAGE               : Support on-site, docs, SAV

Principe zéro déchet : tout contenu créé est versionné et réutilisable.
Toute création naît d'une douleur réelle détectée — jamais de contenu
décoratif sans conversion possible.
"""
import time
import uuid
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

log = logging.getLogger("NAYA.CHANNELS.P04")


# ── Canaux ─────────────────────────────────────────────────────────────────

class Channel(Enum):
    LINKEDIN        = "linkedin"
    INSTAGRAM       = "instagram"
    TIKTOK          = "tiktok"
    PINTEREST       = "pinterest"
    YOUTUBE         = "youtube"
    FACEBOOK        = "facebook"
    WHATSAPP_BIZ    = "whatsapp_business"
    WEBSITE         = "website"
    EMAIL           = "email"
    PRESS           = "press_release"


CHANNEL_SPECS: Dict[str, Dict] = {
    Channel.LINKEDIN.value:     {"max_chars": 3000, "tone": "professionnel",  "audience": "B2B décideurs",    "content_type": "article+post"},
    Channel.INSTAGRAM.value:    {"max_chars": 2200, "tone": "visuel+émotionnel","audience": "B2C aspirant",    "content_type": "photo+reel+story"},
    Channel.TIKTOK.value:       {"max_chars": 300,  "tone": "viral+authentique","audience": "18-35 mobile",   "content_type": "video_court"},
    Channel.PINTEREST.value:    {"max_chars": 500,  "tone": "inspirationnel",  "audience": "déco+habitat",     "content_type": "pin+board"},
    Channel.YOUTUBE.value:      {"max_chars": 5000, "tone": "éducatif+preuve", "audience": "recherche active","content_type": "video_long+short"},
    Channel.FACEBOOK.value:     {"max_chars": 2000, "tone": "communauté",     "audience": "35-55 famille",    "content_type": "post+groupe"},
    Channel.WHATSAPP_BIZ.value: {"max_chars": 1000, "tone": "direct+chaleureux","audience": "leads chauds",  "content_type": "message_1to1"},
    Channel.WEBSITE.value:      {"max_chars": 10000,"tone": "conviction+SEO",  "audience": "trafic organique","content_type": "landing+blog"},
    Channel.EMAIL.value:        {"max_chars": 2000, "tone": "personnel+ciblé", "audience": "pipeline qualifié","content_type": "sequence"},
    Channel.PRESS.value:        {"max_chars": 1500, "tone": "news officiel",   "audience": "journalistes",    "content_type": "communiqué"},
}


# ── Storytelling ──────────────────────────────────────────────────────────

class StoryAngle(Enum):
    PAIN_RESOLUTION    = "pain_resolution"       # La douleur → notre solution
    SOCIAL_PROOF       = "social_proof"          # Témoignages, cas réels
    BEHIND_THE_SCENES  = "behind_the_scenes"     # Usine, montage, livraison
    EDUCATION          = "education"             # Comment ça marche
    URGENCY_SCARCITY   = "urgency_scarcity"      # Stocks limités, délais courts
    SUSTAINABILITY     = "sustainability"        # Énergie renouvelable, impact


STORY_TEMPLATES: Dict[str, str] = {
    StoryAngle.PAIN_RESOLUTION.value: (
        "Vous avez besoin de {rooms} en {surface}m² prêt en {days} jours ? "
        "Nos modules {variant} sont livrés et montés — sans fondation, "
        "sans chantier classique, 100% autonomes (solaire + batterie)."
    ),
    StoryAngle.SOCIAL_PROOF.value: (
        "{client_type} en {sector} avait le même défi. "
        "Résultat : {outcome} en {duration}. Voici ce qu'ils en pensent."
    ),
    StoryAngle.BEHIND_THE_SCENES.value: (
        "Voici comment un module TINY_HOUSE passe de l'usine à votre terrain : "
        "fabrication {factory_country}, contrôle qualité, conteneur, "
        "livraison Polynésie, montage en {assembly_days}h."
    ),
    StoryAngle.EDUCATION.value: (
        "20m² peut sembler petit. Voici comment on maximise chaque centimètre : "
        "chambre parentale climatisée avec WC/douche, chambre enfant, "
        "salon-cuisine ouvert, buanderie — tout compris, zéro compromis."
    ),
    StoryAngle.URGENCY_SCARCITY.value: (
        "Prochain conteneur départ {departure_date}. "
        "{slots_remaining} emplacements disponibles. "
        "Commande validée → livraison {delivery_date}."
    ),
    StoryAngle.SUSTAINABILITY.value: (
        "Module {variant} : 0 réseau électrique requis. "
        "{solar_kwc}kWc solaire + {battery_kwh}kWh batterie = "
        "autonomie totale. Facture énergie : 0 EUR/mois."
    ),
}


# ── Objections & réponses ─────────────────────────────────────────────────

OBJECTION_RESPONSES: Dict[str, str] = {
    "trop_petit_20m2": (
        "20m² bien conçus = plus fonctionnel que 40m² mal pensés. "
        "Plan optimisé : chambre parentale, chambre enfant, WC/douche, "
        "salon-cuisine, buanderie — tout est là. Visite virtuelle disponible."
    ),
    "solidite_qualite": (
        "Modules certifiés résistance vents cycloniques, toiture IPX6, "
        "isolation tropicale R≥3. Prototype qualifié avant toute vente. "
        "Garantie constructeur 5 ans structure."
    ),
    "prix_trop_eleve": (
        "Comparez : construction classique 1500 EUR/m² = 30 000 EUR pour 20m², "
        "délai 12-18 mois. Notre module : livré monté en {days} jours, "
        "énergie incluse, zéro fondation."
    ),
    "financement": (
        "Nous travaillons avec {financer} pour faciliter le financement. "
        "Apport minimum {downpayment_pct}%, mensualités à partir de {monthly_eur} EUR/mois."
    ),
    "delai_trop_long": (
        "Délai actuel : {lead_time_days} jours depuis validation commande. "
        "Dépôt de réservation = place bloquée dans le prochain conteneur. "
        "Voulez-vous qu'on vérifie les disponibilités ?"
    ),
    "permis_construire": (
        "Statut réglementaire dépend de votre terrain et commune. "
        "Nous fournissons le dossier technique complet pour votre déclaration. "
        "Accompagnement administratif disponible (option +X EUR)."
    ),
}


# ── Fournisseurs & usines ─────────────────────────────────────────────────

@dataclass
class SupplierProfile:
    id: str
    name: str
    country: str
    product_type: str
    quality_score: float     # 0–10
    price_index: float       # 0–10 (10=très cher)
    reliability_score: float # 0–10
    lead_time_days: int
    min_order_qty: int
    notes: str = ""
    last_contact: float = field(default_factory=time.time)

    @property
    def overall_score(self) -> float:
        return round(
            self.quality_score * 0.40
            + (10 - self.price_index) * 0.30
            + self.reliability_score * 0.30,
            2,
        )


KNOWN_SUPPLIERS: List[SupplierProfile] = [
    SupplierProfile("SUP-CN-01", "Guangdong ModularCo",   "Chine",    "module_acier",    8.0, 5.0, 8.5, 60, 1),
    SupplierProfile("SUP-VN-01", "Binh Duong PrefabLtd",  "Vietnam",  "module_bois_acier",7.5, 4.5, 8.0, 45, 1),
    SupplierProfile("SUP-MY-01", "Selangor HomeKit",       "Malaisie", "module_composite",8.5, 6.5, 7.5, 55, 2),
    SupplierProfile("SUP-FR-01", "Bretagne Modulaire",     "France",   "module_bois",     9.5, 9.0, 9.0, 90, 1, "Label NF, garantie 10 ans"),
]


# ── Logistique ────────────────────────────────────────────────────────────

@dataclass
class ShipmentRecord:
    id: str = field(default_factory=lambda: f"SHIP-{uuid.uuid4().hex[:8].upper()}")
    project_id: str = "PROJECT_04_TINY_HOUSE"
    origin_country: str = ""
    destination: str = "Polynésie française"
    container_type: str = "40HC"
    units: int = 1
    status: str = "preparing"
    tracking_number: Optional[str] = None
    departure_date: Optional[str] = None
    eta_date: Optional[str] = None
    customs_cleared: bool = False
    delivered: bool = False
    assembly_booked: bool = False
    notes: str = ""
    created_at: float = field(default_factory=time.time)


# ── Moteur principal ──────────────────────────────────────────────────────

class TinyHouseFullChannelManager:
    """
    Gestionnaire opérationnel complet — PROJECT_04_TINY_HOUSE.

    Tout est géré : création contenu, publications, messages,
    modération, fournisseurs, logistique, assemblage.

    Principe : aucune création sans conversion potentielle.
    Tout asset créé est versionné dans le registre zero_waste.
    """

    PROJECT_ID = "PROJECT_04_TINY_HOUSE"

    def __init__(self) -> None:
        self._lock            = threading.RLock()
        self._content_library: List[Dict] = []
        self._shipments:       List[ShipmentRecord] = []
        self._supplier_scores: Dict[str, float] = {}
        self._comment_queue:   List[Dict] = []
        self._message_queue:   List[Dict] = []
        self._initialized_at  = time.time()
        self._stats: Dict[str, int] = {k: 0 for k in [
            "content_created", "content_published", "comments_handled",
            "messages_sent", "shipments_created", "suppliers_evaluated",
        ]}
        log.info(f"[{self.PROJECT_ID}] FullChannelManager initialisé")

    # ── Contenu & storytelling ────────────────────────────────────────────

    def create_content(self, pain_signal: str, channels: Optional[List[str]] = None,
                       angle: str = StoryAngle.PAIN_RESOLUTION.value,
                       context: Optional[Dict] = None) -> Dict:
        """
        Crée du contenu basé sur un signal de douleur réel.
        Adapté à chaque canal. Versionnée dans la bibliothèque.
        """
        if channels is None:
            channels = [Channel.INSTAGRAM.value, Channel.LINKEDIN.value,
                        Channel.TIKTOK.value, Channel.EMAIL.value]
        ctx = context or {}
        template = STORY_TEMPLATES.get(angle, STORY_TEMPLATES[StoryAngle.PAIN_RESOLUTION.value])
        base_text = template.format(
            rooms="chambre parentale + chambre enfant + salon/cuisine",
            surface=20, days=45, variant="ALPHA/BETA",
            solar_kwc=1.5, battery_kwh=5.0,
            client_type="client", sector="secteur", outcome="résultat",
            duration="durée", factory_country="Chine", assembly_days=2,
            departure_date="J+30", slots_remaining=3, delivery_date="J+75",
            before_situation="avant", after_situation="après",
            **ctx,
        ) if "{" in template else template

        pieces: List[Dict] = []
        for ch in channels:
            spec = CHANNEL_SPECS.get(ch, {"max_chars": 500, "tone": "neutre",
                                          "content_type": "post"})
            body = self._adapt_for_channel(base_text, ch, spec)
            piece = {
                "content_id": f"CNT-{uuid.uuid4().hex[:8].upper()}",
                "channel": ch, "angle": angle,
                "pain_signal": pain_signal,
                "body": body[:spec["max_chars"]],
                "cta": self._cta(ch),
                "tone": spec["tone"],
                "published": False,
                "created_at": time.time(),
                "version": 1,
                "recyclable": True,
            }
            pieces.append(piece)

        with self._lock:
            self._content_library.extend(pieces)
            self._stats["content_created"] += len(pieces)

        log.info(f"[CHANNELS] {len(pieces)} pièces créées | angle={angle} | pain={pain_signal[:40]}")
        return {"pain_signal": pain_signal, "angle": angle,
                "pieces_created": len(pieces), "channels": channels,
                "content_ids": [p["content_id"] for p in pieces]}

    def publish_content(self, content_id: str) -> Dict:
        """Marque une pièce de contenu comme publiée."""
        with self._lock:
            for piece in self._content_library:
                if piece["content_id"] == content_id:
                    piece["published"] = True
                    piece["published_at"] = time.time()
                    self._stats["content_published"] += 1
                    log.info(f"[CHANNELS] Publié: {content_id} sur {piece['channel']}")
                    return {"content_id": content_id, "channel": piece["channel"],
                            "published": True}
        return {"error": "Contenu non trouvé", "content_id": content_id}

    def recycle_content(self, content_id: str, new_pain_signal: str,
                        new_channel: Optional[str] = None) -> Dict:
        """
        Recycle un contenu existant pour un nouveau signal/canal.
        Crée version v+1 — principe zéro déchet.
        """
        with self._lock:
            original = next((p for p in self._content_library
                             if p["content_id"] == content_id), None)
        if not original:
            return {"error": "Contenu original non trouvé", "content_id": content_id}
        ch = new_channel or original["channel"]
        spec = CHANNEL_SPECS.get(ch, {"max_chars": 500, "tone": "neutre", "content_type": "post"})
        recycled = {
            **original,
            "content_id": f"CNT-{uuid.uuid4().hex[:8].upper()}",
            "pain_signal": new_pain_signal,
            "channel": ch,
            "body": self._adapt_for_channel(original["body"], ch, spec),
            "published": False,
            "version": original.get("version", 1) + 1,
            "recycled_from": content_id,
            "created_at": time.time(),
        }
        with self._lock:
            self._content_library.append(recycled)
            self._stats["content_created"] += 1
        log.info(f"[CHANNELS] Recyclé: {content_id} → {recycled['content_id']} v{recycled['version']}")
        return {"original_id": content_id, "recycled_id": recycled["content_id"],
                "version": recycled["version"], "new_channel": ch}

    # ── Commentaires ──────────────────────────────────────────────────────

    def handle_comment(self, platform: str, comment_text: str,
                       sentiment: str = "neutral",
                       author_type: str = "prospect") -> Dict:
        """
        Génère une réponse adaptée à un commentaire.
        Sentiment : positive | neutral | negative | question
        Author : prospect | client | competitor | troll
        """
        response = self._generate_comment_response(comment_text, sentiment, author_type)
        record = {
            "id": f"CMT-{uuid.uuid4().hex[:6].upper()}",
            "platform": platform,
            "comment": comment_text[:200],
            "sentiment": sentiment,
            "author_type": author_type,
            "response": response,
            "action": "reply" if author_type != "troll" else "hide",
            "handled_at": time.time(),
        }
        with self._lock:
            self._comment_queue.append(record)
            self._stats["comments_handled"] += 1
        return record

    def handle_objection_message(self, objection_key: str,
                                 channel: str = Channel.WHATSAPP_BIZ.value,
                                 context: Optional[Dict] = None) -> Dict:
        """Génère une réponse à une objection connue."""
        template = OBJECTION_RESPONSES.get(objection_key)
        if not template:
            return {"error": f"Objection inconnue: {objection_key}",
                    "known_objections": list(OBJECTION_RESPONSES.keys())}
        ctx = context or {}
        try:
            response = template.format(**ctx)
        except KeyError:
            response = template  # Retourne le template brut si contexte manquant
        msg = {
            "message_id": f"MSG-{uuid.uuid4().hex[:6].upper()}",
            "objection": objection_key,
            "channel": channel,
            "response": response,
            "cta": self._cta(channel),
            "created_at": time.time(),
        }
        with self._lock:
            self._message_queue.append(msg)
            self._stats["messages_sent"] += 1
        return msg

    # ── Fournisseurs & usines ─────────────────────────────────────────────

    def evaluate_suppliers(self) -> List[Dict]:
        """Évalue et classe tous les fournisseurs connus."""
        ranked = sorted(KNOWN_SUPPLIERS, key=lambda s: s.overall_score, reverse=True)
        result = []
        for s in ranked:
            score = s.overall_score
            self._supplier_scores[s.id] = score
            result.append({
                "supplier_id": s.id, "name": s.name, "country": s.country,
                "product_type": s.product_type,
                "overall_score": score,
                "quality": s.quality_score, "price_index": s.price_index,
                "reliability": s.reliability_score,
                "lead_time_days": s.lead_time_days, "moq": s.min_order_qty,
                "tier": "ELITE" if score >= 8.0 else ("PREFERRED" if score >= 6.5 else "STANDARD"),
                "notes": s.notes,
            })
        with self._lock:
            self._stats["suppliers_evaluated"] += 1
        log.info(f"[CHANNELS] {len(result)} fournisseurs évalués | top: {result[0]['name']}")
        return result

    def get_best_supplier(self, min_quality: float = 7.5,
                          max_lead_days: int = 60) -> Optional[Dict]:
        """Retourne le meilleur fournisseur selon critères."""
        candidates = [
            s for s in KNOWN_SUPPLIERS
            if s.quality_score >= min_quality and s.lead_time_days <= max_lead_days
        ]
        if not candidates:
            return None
        best = max(candidates, key=lambda s: s.overall_score)
        return {"supplier_id": best.id, "name": best.name, "country": best.country,
                "score": best.overall_score, "lead_time_days": best.lead_time_days}

    # ── Logistique & livraison ────────────────────────────────────────────

    def create_shipment(self, origin_country: str, units: int = 1,
                        container_type: str = "40HC",
                        notes: str = "") -> Dict:
        """Crée un enregistrement d'expédition."""
        shipment = ShipmentRecord(
            origin_country=origin_country,
            container_type=container_type,
            units=units,
            notes=notes,
        )
        with self._lock:
            self._shipments.append(shipment)
            self._stats["shipments_created"] += 1
        log.info(f"[CHANNELS] Expédition créée: {shipment.id} | {origin_country} → PF | {units} unité(s)")
        return {
            "shipment_id": shipment.id, "origin": origin_country,
            "destination": shipment.destination, "units": units,
            "container": container_type, "status": shipment.status,
        }

    def update_shipment(self, shipment_id: str, **kwargs: Any) -> Dict:
        """Met à jour un enregistrement d'expédition."""
        with self._lock:
            shipment = next((s for s in self._shipments if s.id == shipment_id), None)
            if not shipment:
                return {"error": "Expédition non trouvée", "shipment_id": shipment_id}
            for key, val in kwargs.items():
                if hasattr(shipment, key):
                    setattr(shipment, key, val)
            return {"shipment_id": shipment_id, "updated_fields": list(kwargs.keys()),
                    "status": shipment.status, "delivered": shipment.delivered}

    def get_assembly_brief(self, shipment_id: str) -> Dict:
        """Génère le brief montage pour une livraison."""
        with self._lock:
            shipment = next((s for s in self._shipments if s.id == shipment_id), None)
        if not shipment:
            return {"error": "Expédition non trouvée"}
        return {
            "shipment_id": shipment_id,
            "destination": shipment.destination,
            "units": shipment.units,
            "assembly_steps": [
                "1. Préparation terrain (nivellement, ancres ou longrines)",
                "2. Déchargement conteneur, inventaire modules",
                "3. Positionnement châssis principal",
                "4. Assemblage structure (panneaux, toiture) — 4-8h par module",
                "5. Raccordements électriques (solaire, batterie, tableau)",
                "6. Raccordements plomberie (eau, WC, douche, buanderie)",
                "7. Pose climatisation (unité extérieure + intérieures)",
                "8. Finitions intérieures (revêtements, portes, fenêtres)",
                "9. Tests et mise en service",
                "10. Formation utilisateur + remise documentation",
            ],
            "estimated_assembly_days": shipment.units * 2,
            "tools_required": ["Clés hexagonales", "Niveau", "Perceuse", "Matériel électrique",
                                "Raccords plomberie", "Kit mise en service solaire"],
            "support": "Manuel inclus dans livraison + support technique vidéo disponible",
        }

    # ── Crédibilité ───────────────────────────────────────────────────────

    def build_credibility_pack(self) -> Dict:
        """Génère le pack crédibilité pour le projet."""
        return {
            "certifications": [
                "Modules testés résistance vents > 200 km/h (normes cyclone PF)",
                "Isolation thermique certifiée R≥3.0 (tropique)",
                "Panneaux solaires IEC 61215 / IEC 61730",
                "Système batterie CE / UL listée",
            ],
            "proof_points": [
                "2 modules prototypes qualifiés avant lancement (scores > 7/10)",
                "Fournisseurs audités sur site avant commande série",
                "Délai garanti contractuellement (pénalités si dépassement)",
                "Service après-vente actif Polynésie + Europe",
            ],
            "media_angles": [
                "Habitat alternatif en Polynésie — autonomie totale en 45 jours",
                "La tiny house qui résiste aux cyclones : comment on y est arrivés",
                "Off-grid en Polynésie : 0 facture énergie avec ces modules",
            ],
            "social_proof_templates": [
                "'{client_name}', {sector}, '{result}' — {duration}",
                "Avant/Après : {before_situation} → {after_situation} en {days} jours",
            ],
        }

    # ── Stats & reporting ─────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Métriques opérationnelles complètes."""
        with self._lock:
            published = sum(1 for c in self._content_library if c.get("published"))
            recycled  = sum(1 for c in self._content_library if c.get("recycled_from"))
            delivered = sum(1 for s in self._shipments if s.delivered)
            return {
                "project": self.PROJECT_ID,
                "uptime_seconds": int(time.time() - self._initialized_at),
                "content": {
                    "total_created": len(self._content_library),
                    "published": published,
                    "recycled": recycled,
                    "pending_publish": len(self._content_library) - published,
                },
                "engagement": {
                    "comments_handled": self._stats["comments_handled"],
                    "messages_sent": self._stats["messages_sent"],
                },
                "supply_chain": {
                    "suppliers_evaluated": self._stats["suppliers_evaluated"],
                    "shipments_total": len(self._shipments),
                    "shipments_delivered": delivered,
                },
                "operations": dict(self._stats),
            }

    def get_content_library(self, channel: Optional[str] = None,
                            published_only: bool = False) -> List[Dict]:
        """Retourne la bibliothèque de contenu avec filtres optionnels."""
        with self._lock:
            lib = list(self._content_library)
        if channel:
            lib = [c for c in lib if c["channel"] == channel]
        if published_only:
            lib = [c for c in lib if c.get("published")]
        return lib

    # ── Interne ───────────────────────────────────────────────────────────

    def _adapt_for_channel(self, base: str, channel: str, spec: Dict) -> str:
        tone = spec.get("tone", "neutre")
        if channel == Channel.TIKTOK.value:
            return f"💡 {base[:200]} #tinyhouse #offgrid #polynésie #logementmodulaire"
        if channel == Channel.LINKEDIN.value:
            return (f"🏡 {base}\n\nSecteur habitat modulaire Polynésie — "
                    f"solution prête en 45 jours. Intéressé(e) ? Parlez-nous de votre projet.")
        if channel == Channel.INSTAGRAM.value:
            return (f"{base[:300]}\n\n🌿 Autonome · ⚡ Solaire · 🌀 Anti-cyclone\n"
                    f"#tinyhouse #polynésie #offgrid #logementmodulaire #autonomieenergetique")
        if channel == Channel.EMAIL.value:
            return f"Bonjour,\n\n{base}\n\nN'hésitez pas à répondre pour en savoir plus.\n\nÀ bientôt,\nL'équipe NAYA"
        if channel == Channel.WHATSAPP_BIZ.value:
            return f"👋 {base[:400]}\n\nVoulez-vous qu'on discute de votre projet ?"
        return base[:spec.get("max_chars", 500)]

    def _cta(self, channel: str) -> str:
        ctas = {
            Channel.LINKEDIN.value:     "Envoyez-moi un message pour discuter de votre projet →",
            Channel.INSTAGRAM.value:    "Lien en bio 🔗 | DM pour devis",
            Channel.TIKTOK.value:       "Commente 'INFO' pour recevoir le catalogue",
            Channel.PINTEREST.value:    "Épinglez et découvrez nos modules →",
            Channel.EMAIL.value:        "Répondez à cet email ou appelez le +689 XXXXXX",
            Channel.WHATSAPP_BIZ.value: "Répondez 'OUI' pour recevoir la documentation complète",
            Channel.WEBSITE.value:      "Demandez votre devis personnalisé en 2 minutes →",
            Channel.FACEBOOK.value:     "Commentez ou envoyez un message pour en savoir plus →",
            Channel.YOUTUBE.value:      "Abonnez-vous + activez la cloche 🔔 | Lien devis en description",
            Channel.PRESS.value:        "Contact presse : press@naya.pf",
        }
        return ctas.get(channel, "Contactez-nous pour en savoir plus →")

    def _generate_comment_response(self, comment: str, sentiment: str,
                                   author_type: str) -> str:
        comment_lower = comment.lower()
        if author_type == "troll":
            return "[action: hide/block]"
        if sentiment == "positive":
            return ("Merci pour votre message ! 🙏 Nous serions ravis de vous présenter "
                    "nos modules en détail. DM ou lien en bio pour le catalogue complet.")
        if "prix" in comment_lower or "combien" in comment_lower or "tarif" in comment_lower:
            return ("Le prix dépend de votre configuration et destination. "
                    "Nos modules démarrent à partir de 18 000 EUR livré monté. "
                    "DM pour un devis personnalisé 🏡")
        if "délai" in comment_lower or "livraison" in comment_lower or "quand" in comment_lower:
            return ("Délai actuel : 45-60 jours selon origine usine. "
                    "Dépôt de réservation = place bloquée dans le prochain conteneur. "
                    "Voulez-vous vérifier les disponibilités ?")
        if sentiment == "negative":
            return ("Merci pour votre retour. Pouvez-vous m'envoyer un DM pour qu'on discute "
                    "directement ? Je veux m'assurer que vous avez toutes les informations. 🤝")
        return ("Bonne question ! 😊 Envoyez-nous un DM ou consultez le lien en bio "
                "pour tous les détails sur nos modules. On répond en moins de 2h.")
