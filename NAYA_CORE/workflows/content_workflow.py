#!/usr/bin/env python3
"""
NAYA WORKFLOWS - Content Workflow
Brief → Article → Distribution → Recycling
"""

import asyncio
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from datetime import datetime


class ContentState(TypedDict):
    """État du workflow de génération de contenu"""
    content_id: str
    brief: str
    sector: str
    content_type: str  # article, whitepaper, case_study, newsletter
    target_audience: str
    keywords: list
    generated_content: dict
    distribution_channels: list
    distribution_status: dict
    recycled_versions: list
    performance_metrics: dict
    created_at: str
    updated_at: str


async def generate_brief_node(state: ContentState) -> ContentState:
    """Node 1: Génère un brief de contenu basé sur le secteur et l'audience"""
    print(f"📝 Generating content brief for {state['sector']}...")
    
    # Enrichir le brief avec contexte marché
    enhanced_brief = {
        "original": state.get("brief", ""),
        "sector": state["sector"],
        "target_audience": state["target_audience"],
        "angle": f"Expertise IEC 62443 appliquée à {state['sector']}",
        "cta": "Audit flash disponible",
        "tone": "expert technique, pédagogique",
        "length_words": 800 if state["content_type"] == "article" else 2000
    }
    
    state["brief"] = str(enhanced_brief)
    state["updated_at"] = datetime.now().isoformat()
    
    return state


async def generate_content_node(state: ContentState) -> ContentState:
    """Node 2: Génère le contenu via LLM"""
    print(f"✍️  Generating {state['content_type']}...")
    
    # Simulation génération contenu (en production: appel LLM)
    content = {
        "title": f"IEC 62443 pour le secteur {state['sector']}: Guide complet",
        "subtitle": "Sécurisez votre OT en conformité NIS2",
        "body": f"""
# Introduction
Le secteur {state['sector']} fait face à des défis cybersécurité OT critiques...

# Les enjeux IEC 62443
[Contenu technique détaillé sur IEC 62443 appliqué au secteur]

# Solutions pratiques
[Approche concrète adaptée au {state['sector']}]

# Conclusion
Un audit IEC 62443 express permet d'identifier vos gaps critiques en 48h.
        """.strip(),
        "keywords": state.get("keywords", []),
        "word_count": 850,
        "estimated_read_time_min": 4
    }
    
    state["generated_content"] = content
    state["updated_at"] = datetime.now().isoformat()
    
    return state


async def distribute_content_node(state: ContentState) -> ContentState:
    """Node 3: Distribue le contenu sur les canaux définis"""
    print(f"📤 Distributing content to {len(state.get('distribution_channels', []))} channels...")
    
    distribution_status = {}
    for channel in state.get("distribution_channels", ["linkedin", "newsletter"]):
        # Simulation distribution
        distribution_status[channel] = {
            "status": "published",
            "url": f"https://{channel}.com/naya-supreme/{state['content_id']}",
            "published_at": datetime.now().isoformat()
        }
    
    state["distribution_status"] = distribution_status
    state["updated_at"] = datetime.now().isoformat()
    
    return state


async def recycle_content_node(state: ContentState) -> ContentState:
    """Node 4: Recycle le contenu en versions alternatives"""
    print(f"♻️  Recycling content into alternative formats...")
    
    recycled = []
    
    # Version LinkedIn post (court)
    recycled.append({
        "format": "linkedin_post",
        "content": state["generated_content"]["body"][:300] + "...",
        "cta": "Lire l'article complet →"
    })
    
    # Version email newsletter
    recycled.append({
        "format": "newsletter_snippet",
        "content": state["generated_content"]["body"][:500],
        "subject": state["generated_content"]["title"]
    })
    
    # Version thread Twitter/X
    body = state["generated_content"]["body"]
    tweets = [body[i:i+250] for i in range(0, min(len(body), 1000), 250)]
    recycled.append({
        "format": "twitter_thread",
        "tweets": tweets[:4]
    })
    
    state["recycled_versions"] = recycled
    state["updated_at"] = datetime.now().isoformat()
    
    return state


async def track_performance_node(state: ContentState) -> ContentState:
    """Node 5: Tracking performance du contenu"""
    print(f"📊 Tracking content performance...")
    
    # Métriques simulées (en production: vraies analytics)
    state["performance_metrics"] = {
        "views": 0,
        "engagement_rate": 0.0,
        "leads_generated": 0,
        "revenue_attributed_eur": 0,
        "tracking_started_at": datetime.now().isoformat()
    }
    
    state["updated_at"] = datetime.now().isoformat()
    
    return state


# Construction du graph LangGraph
def create_content_workflow() -> StateGraph:
    """Crée le workflow stateful de génération de contenu"""
    
    workflow = StateGraph(ContentState)
    
    # Ajout des nodes
    workflow.add_node("generate_brief", generate_brief_node)
    workflow.add_node("generate_content", generate_content_node)
    workflow.add_node("distribute", distribute_content_node)
    workflow.add_node("recycle", recycle_content_node)
    workflow.add_node("track_performance", track_performance_node)
    
    # Définition des edges
    workflow.set_entry_point("generate_brief")
    workflow.add_edge("generate_brief", "generate_content")
    workflow.add_edge("generate_content", "distribute")
    workflow.add_edge("distribute", "recycle")
    workflow.add_edge("recycle", "track_performance")
    workflow.add_edge("track_performance", END)
    
    return workflow.compile()


# Instance globale compilée
content_workflow = create_content_workflow()


async def run_content_workflow(
    sector: str,
    content_type: str = "article",
    target_audience: str = "RSSI, Directeurs Industriels",
    distribution_channels: list = None
) -> ContentState:
    """
    Exécute le workflow complet de génération de contenu

    Args:
        sector: Secteur cible
        content_type: Type de contenu (article, whitepaper, etc.)
        target_audience: Audience cible
        distribution_channels: Canaux de distribution

    Returns:
        État final avec contenu généré et distribué
    """
    content_id = f"CONTENT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    initial_state: ContentState = {
        "content_id": content_id,
        "brief": f"Créer un {content_type} sur IEC 62443 pour {sector}",
        "sector": sector,
        "content_type": content_type,
        "target_audience": target_audience,
        "keywords": ["IEC 62443", "cybersécurité OT", sector, "NIS2"],
        "generated_content": {},
        "distribution_channels": distribution_channels or ["linkedin", "newsletter"],
        "distribution_status": {},
        "recycled_versions": [],
        "performance_metrics": {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Exécution du workflow
    result = await content_workflow.ainvoke(initial_state)
    
    return result


async def main():
    """Test du workflow"""
    print("🎨 NAYA Content Workflow - Test")
    print("=" * 60)
    
    result = await run_content_workflow(
        sector="Transport & Logistique",
        content_type="article",
        target_audience="RSSI Transport, DSI Logistique",
        distribution_channels=["linkedin", "newsletter", "blog"]
    )
    
    print(f"\n✅ Workflow complete!")
    print(f"   Content ID: {result['content_id']}")
    print(f"   Title: {result['generated_content']['title']}")
    print(f"   Word count: {result['generated_content']['word_count']}")
    print(f"   Distributed to: {list(result['distribution_status'].keys())}")
    print(f"   Recycled versions: {len(result['recycled_versions'])}")


if __name__ == "__main__":
    asyncio.run(main())
