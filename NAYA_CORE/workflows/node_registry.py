#!/usr/bin/env python3
"""
NAYA WORKFLOWS - Node Registry
Registre central de tous les nodes LangGraph disponibles
"""

from typing import Dict, Callable, Any
from enum import Enum


class NodeCategory(Enum):
    """Catégories de nodes"""
    PROSPECTION = "prospection"
    AUDIT = "audit"
    CONTENT = "content"
    CLOSING = "closing"
    ENRICHMENT = "enrichment"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"


class NodeRegistry:
    """
    Registre central des nodes LangGraph
    Permet une découverte et réutilisation facile des nodes
    """

    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        node_fn: Callable,
        category: NodeCategory,
        description: str,
        input_schema: Dict = None,
        output_schema: Dict = None
    ):
        """
        Enregistre un node dans le registre

        Args:
            name: Nom unique du node
            node_fn: Fonction async du node
            category: Catégorie
            description: Description du node
            input_schema: Schéma d'entrée attendu
            output_schema: Schéma de sortie produit
        """
        self._nodes[name] = {
            "function": node_fn,
            "category": category,
            "description": description,
            "input_schema": input_schema or {},
            "output_schema": output_schema or {}
        }

    def get(self, name: str) -> Callable:
        """Récupère un node par nom"""
        if name not in self._nodes:
            raise KeyError(f"Node '{name}' not found in registry")
        return self._nodes[name]["function"]

    def list_by_category(self, category: NodeCategory) -> Dict[str, Dict]:
        """Liste tous les nodes d'une catégorie"""
        return {
            name: info
            for name, info in self._nodes.items()
            if info["category"] == category
        }

    def list_all(self) -> Dict[str, Dict]:
        """Liste tous les nodes enregistrés"""
        return self._nodes.copy()

    def get_info(self, name: str) -> Dict:
        """Récupère les métadonnées d'un node"""
        if name not in self._nodes:
            raise KeyError(f"Node '{name}' not found in registry")
        return {
            "name": name,
            "category": self._nodes[name]["category"].value,
            "description": self._nodes[name]["description"],
            "input_schema": self._nodes[name]["input_schema"],
            "output_schema": self._nodes[name]["output_schema"]
        }


# Instance globale
node_registry = NodeRegistry()


def auto_register_prospection_nodes():
    """Auto-enregistre les nodes du workflow prospection"""
    try:
        from NAYA_CORE.workflows.prospection_workflow import (
            enrich_prospect_node,
            score_prospect_node,
            generate_offer_node,
            send_outreach_node,
            handle_reply_node,
            generate_contract_node
        )

        node_registry.register(
            "enrich_prospect",
            enrich_prospect_node,
            NodeCategory.ENRICHMENT,
            "Enrichit un prospect avec données Apollo/Hunter/LinkedIn"
        )

        node_registry.register(
            "score_prospect",
            score_prospect_node,
            NodeCategory.ANALYSIS,
            "Score un prospect (0-100) selon critères NAYA"
        )

        node_registry.register(
            "generate_offer",
            generate_offer_node,
            NodeCategory.PROSPECTION,
            "Génère une offre personnalisée (PDF + email + LinkedIn)"
        )

        node_registry.register(
            "send_outreach",
            send_outreach_node,
            NodeCategory.COMMUNICATION,
            "Envoie la séquence outreach multi-touch (7 touches)"
        )

        node_registry.register(
            "handle_reply",
            handle_reply_node,
            NodeCategory.COMMUNICATION,
            "Gère les réponses prospects (objections, questions)"
        )

        node_registry.register(
            "generate_contract",
            generate_contract_node,
            NodeCategory.CLOSING,
            "Génère contrat PDF signable + payment link"
        )

    except ImportError as e:
        print(f"Could not auto-register prospection nodes: {e}")


def auto_register_audit_nodes():
    """Auto-enregistre les nodes du workflow audit"""
    try:
        from NAYA_CORE.workflows.audit_workflow import (
            analyze_signal_node,
            generate_audit_node,
            generate_report_node,
            propose_upsell_node
        )

        node_registry.register(
            "analyze_signal",
            analyze_signal_node,
            NodeCategory.ANALYSIS,
            "Analyse un signal marché pour qualifier besoin audit"
        )

        node_registry.register(
            "generate_audit",
            generate_audit_node,
            NodeCategory.AUDIT,
            "Génère audit IEC 62443 / NIS2 automatisé"
        )

        node_registry.register(
            "generate_report",
            generate_report_node,
            NodeCategory.AUDIT,
            "Génère rapport PDF professionnel 20-40 pages"
        )

        node_registry.register(
            "propose_upsell",
            propose_upsell_node,
            NodeCategory.CLOSING,
            "Propose mission remédiation (upsell post-audit)"
        )

    except ImportError as e:
        print(f"Could not auto-register audit nodes: {e}")


def auto_register_content_nodes():
    """Auto-enregistre les nodes du workflow content"""
    try:
        from NAYA_CORE.workflows.content_workflow import (
            generate_brief_node,
            generate_content_node,
            distribute_content_node,
            recycle_content_node,
            track_performance_node
        )

        node_registry.register(
            "generate_brief",
            generate_brief_node,
            NodeCategory.CONTENT,
            "Génère brief de contenu enrichi"
        )

        node_registry.register(
            "generate_content",
            generate_content_node,
            NodeCategory.CONTENT,
            "Génère contenu (article/whitepaper/case study)"
        )

        node_registry.register(
            "distribute_content",
            distribute_content_node,
            NodeCategory.COMMUNICATION,
            "Distribue contenu sur canaux (LinkedIn/newsletter/blog)"
        )

        node_registry.register(
            "recycle_content",
            recycle_content_node,
            NodeCategory.CONTENT,
            "Recycle contenu en versions alternatives"
        )

        node_registry.register(
            "track_performance",
            track_performance_node,
            NodeCategory.ANALYSIS,
            "Track performance contenu (views, engagement, leads)"
        )

    except ImportError as e:
        print(f"Could not auto-register content nodes: {e}")


def auto_register_closing_nodes():
    """Auto-enregistre les nodes du workflow closing"""
    try:
        from NAYA_CORE.workflows.closing_workflow import (
            analyze_response_node,
            handle_objection_node,
            negotiate_node,
            close_deal_node
        )

        node_registry.register(
            "analyze_response",
            analyze_response_node,
            NodeCategory.ANALYSIS,
            "Analyse réponse prospect (intention, objections)"
        )

        node_registry.register(
            "handle_objection",
            handle_objection_node,
            NodeCategory.CLOSING,
            "Traite objection avec best response mémorisée"
        )

        node_registry.register(
            "negotiate",
            negotiate_node,
            NodeCategory.CLOSING,
            "Négocie conditions (prix, délai, scope)"
        )

        node_registry.register(
            "close_deal",
            close_deal_node,
            NodeCategory.CLOSING,
            "Finalise deal (contrat + paiement)"
        )

    except ImportError as e:
        print(f"Could not auto-register closing nodes: {e}")


# Auto-registration au chargement du module
def initialize_registry():
    """Initialise le registre avec tous les nodes disponibles"""
    auto_register_prospection_nodes()
    auto_register_audit_nodes()
    auto_register_content_nodes()
    auto_register_closing_nodes()


# Initialisation automatique
initialize_registry()


if __name__ == "__main__":
    print("📋 NAYA Node Registry - Available Nodes")
    print("=" * 60)

    all_nodes = node_registry.list_all()
    print(f"\nTotal nodes registered: {len(all_nodes)}")

    for category in NodeCategory:
        nodes = node_registry.list_by_category(category)
        if nodes:
            print(f"\n{category.value.upper()} ({len(nodes)} nodes):")
            for name, info in nodes.items():
                print(f"  • {name}: {info['description']}")
