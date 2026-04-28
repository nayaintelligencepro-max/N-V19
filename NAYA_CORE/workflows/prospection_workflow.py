"""
PROSPECTION WORKFLOW v19.1
Production-ready LangGraph stateful workflow
Pain Detection → Prospect Enrichment → Offer Generation

Cycle time: Pain detected → Offer ready = 24 heures max
Target: 20-50 new prospects/week auto-qualified
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum

# LLM imports
import anthropic
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool

# Integration imports
from NAYA_CORE.integrations.apollo_hunter import ApolloHunter
from NAYA_CORE.integrations.serper_multi import SerperMultiKeySearch as SerperMultiSearch
from NAYA_CORE.execution.llm_router import LLMRouter
from NAYA_REVENUE_ENGINE.offer_generator import OfferGenerator
from NAYA_CORE.memory.vector_db_integration import VectorDBIntegration
from NAYA_CORE.state.state_manager import StateManager


# ============================================================================
# DATA MODELS
# ============================================================================

class PainSignal(BaseModel):
    """Detected pain from market signals"""
    signal_type: str  # "job_offer", "news", "linkedin", "regulatory"
    company: str
    sector: str
    decision_maker_title: str
    detected_pain: str
    budget_estimate: int  # EUR
    source: str
    confidence_score: float  # 0.0-1.0
    detected_at: str

class EnrichedProspect(BaseModel):
    """Prospect after Apollo/Hunter enrichment"""
    pain_signal: PainSignal
    company_name: str
    company_size: str
    company_revenue: Optional[str]
    decision_maker_name: str
    decision_maker_email: str
    decision_maker_phone: Optional[str]
    decision_maker_linkedin: str
    tech_stack: List[str]
    ot_vulnerability_signals: List[str]
    enrichment_score: float
    enriched_at: str

class ProspectionState(BaseModel):
    """State machine for prospection workflow"""
    prospect_id: str
    state: str  # "detected", "enriching", "offer_generating", "ready", "failed"
    pain_signal: Optional[PainSignal] = None
    enriched_prospect: Optional[EnrichedProspect] = None
    offer_generated: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    created_at: str = None
    updated_at: str = None


# ============================================================================
# PAIN DETECTION ENGINE
# ============================================================================

class PainDetectionEngine:
    """
    Scan for detectable pains via:
    - Job offers (RSSI, IEC 62443, OT Security roles)
    - News triggers (cyberattacks, compliance deadlines)
    - LinkedIn signals (new hires, promotions)
    - Regulatory triggers (NIS2, ISO 27001 renewals)
    """
    
    PAIN_KEYWORDS = {
        "rssi": ["RSSI", "Chef sécurité", "Responsable cybersécurité", "OT Security"],
        "iec62443": ["IEC 62443", "Conformité industrielle", "OT certification"],
        "nis2": ["NIS2", "Entités critiques", "Opérateurs essentiels"],
        "scada": ["SCADA", "Automate", "Système temps réel"],
        "ransomware": ["ransomware", "cyberattaque", "incident", "cryptage"],
    }
    
    def __init__(self, serper_api, llm_router):
        self.serper = SerperMultiSearch(api_key=serper_api)
        self.llm = llm_router
        self.memory = VectorDBIntegration()
        
    async def detect_from_job_offers(self) -> List[PainSignal]:
        """Scan job boards for RSSI/OT security open positions"""
        signals = []
        
        # Search LinkedIn jobs
        job_queries = [
            "RSSI responsable cybersécurité industrielle",
            "OT Security Engineer Europe",
            "IEC 62443 consultant implementation",
            "SCADA security engineer job offer"
        ]
        
        for query in job_queries:
            results = await self.serper.search(query, num_results=5)
            
            for result in results:
                # Parse job offer for pain indicators
                pain = await self._parse_job_offer(result)
                if pain and pain.confidence_score >= 0.7:
                    signals.append(pain)
                    
        return signals
    
    async def detect_from_news(self) -> List[PainSignal]:
        """Scan news for cyberattack/compliance incidents"""
        signals = []
        
        news_queries = [
            "cyberattaque usine France Europe 2025 2026",
            "ransomware industriel incident NIS2",
            "conformité NIS2 deadline manquée",
            "audit ISO 27001 vulnerabilité"
        ]
        
        for query in news_queries:
            results = await self.serper.search(query, num_results=5, news=True)
            
            for result in results:
                pain = await self._parse_news(result)
                if pain and pain.confidence_score >= 0.65:
                    signals.append(pain)
                    
        return signals
    
    async def detect_from_linkedin(self) -> List[PainSignal]:
        """Detect LinkedIn signals: new RSSI, role changes"""
        signals = []
        
        # Would require LinkedIn API integration
        # For now, return empty - to be implemented
        return signals
    
    async def _parse_job_offer(self, job_result: Dict) -> Optional[PainSignal]:
        """Use LLM to parse job offer for pain indicators"""
        
        prompt = f"""
        Analyze this job offer for cybersecurity/OT pain signals.
        
        Job Title: {job_result.get('title', '')}
        Company: {job_result.get('company', '')}
        Description: {job_result.get('description', '')[:500]}
        
        Extract:
        1. Decision maker title (RSSI/DSI/etc)
        2. Pain detected (what problem they're hiring for)
        3. Budget estimate (from salary range if available)
        4. Confidence score (0.0-1.0)
        
        Return JSON only.
        """
        
        response = await self.llm.call(prompt, temperature=0.3)
        
        try:
            data = json.loads(response)
            return PainSignal(
                signal_type="job_offer",
                company=job_result.get('company', 'Unknown'),
                sector="Technology/OT",
                decision_maker_title=data.get('decision_maker_title', 'RSSI'),
                detected_pain=data.get('pain', ''),
                budget_estimate=int(data.get('budget_estimate', 1000)),
                source=job_result.get('link', ''),
                confidence_score=float(data.get('confidence_score', 0.7)),
                detected_at=datetime.now().isoformat()
            )
        except (json.JSONDecodeError, ValueError):
            return None
    
    async def _parse_news(self, news_result: Dict) -> Optional[PainSignal]:
        """Parse news article for pain signals"""
        
        prompt = f"""
        Extract pain signal from this news article about cybersecurity incident or compliance.
        
        Title: {news_result.get('title', '')}
        Source: {news_result.get('source', '')}
        Summary: {news_result.get('snippet', '')[:400]}
        
        Extract:
        1. Affected sector
        2. Pain type (ransomware/compliance/vulnerability)
        3. Implied company size affected
        4. Urgency (0.0-1.0)
        
        Return JSON only.
        """
        
        response = await self.llm.call(prompt, temperature=0.3)
        
        try:
            data = json.loads(response)
            return PainSignal(
                signal_type="news",
                company=news_result.get('source', 'Industry-wide'),
                sector=data.get('sector', 'OT/Manufacturing'),
                decision_maker_title="DSI/RSSI",
                detected_pain=data.get('pain_type', ''),
                budget_estimate=data.get('budget_estimate', 15000),
                source=news_result.get('link', ''),
                confidence_score=float(data.get('urgency', 0.7)),
                detected_at=datetime.now().isoformat()
            )
        except (json.JSONDecodeError, ValueError):
            return None


# ============================================================================
# PROSPECT ENRICHMENT ENGINE
# ============================================================================

class ProspectEnrichmentEngine:
    """
    Enrich pain signals with prospect data:
    - Company info (size, revenue, tech stack)
    - Decision maker contact info
    - OT vulnerability signals
    """
    
    def __init__(self, apollo_api, hunter_api, llm_router):
        self.apollo = ApolloHunter(api_key=apollo_api)
        self.hunter_api = hunter_api
        self.llm = llm_router
        
    async def enrich(self, pain: PainSignal) -> Optional[EnrichedProspect]:
        """Enrich pain signal with prospect data (3-source strategy)"""
        
        # Source 1: Apollo.io
        apollo_data = await self.apollo.find_prospect(
            company=pain.company,
            title=pain.decision_maker_title
        )
        
        if apollo_data and apollo_data.get('email'):
            return await self._build_enriched_prospect(pain, apollo_data, "apollo")
        
        # Source 2: Hunter.io fallback
        hunter_data = await self._hunter_search(pain.company, pain.decision_maker_title)
        if hunter_data and hunter_data.get('email'):
            return await self._build_enriched_prospect(pain, hunter_data, "hunter")
        
        # Source 3: Web scraping/pattern matching
        scraped_data = await self._scrape_company_email(pain.company)
        if scraped_data and scraped_data.get('email'):
            return await self._build_enriched_prospect(pain, scraped_data, "scraped")
        
        # If all 3 sources fail, mark for manual review
        print(f"⚠️ Email not found for {pain.company} - marking for manual review")
        return None
    
    async def _build_enriched_prospect(
        self, 
        pain: PainSignal, 
        contact_data: Dict,
        source: str
    ) -> EnrichedProspect:
        """Build enriched prospect object"""
        
        # Get company info
        company_info = await self._get_company_info(pain.company)
        
        # Detect OT vulnerabilities
        ot_signals = await self._detect_ot_vulnerabilities(pain.company, pain.sector)
        
        enrichment_score = 0.95 if source == "apollo" else (0.85 if source == "hunter" else 0.75)
        
        return EnrichedProspect(
            pain_signal=pain,
            company_name=pain.company,
            company_size=company_info.get('size', 'Unknown'),
            company_revenue=company_info.get('revenue', None),
            decision_maker_name=contact_data.get('name', pain.decision_maker_title),
            decision_maker_email=contact_data.get('email', ''),
            decision_maker_phone=contact_data.get('phone', None),
            decision_maker_linkedin=contact_data.get('linkedin_url', ''),
            tech_stack=company_info.get('tech_stack', []),
            ot_vulnerability_signals=ot_signals,
            enrichment_score=enrichment_score,
            enriched_at=datetime.now().isoformat()
        )
    
    async def _hunter_search(self, company: str, title: str) -> Optional[Dict]:
        """Search Hunter.io for email. V19.3: real API call."""
        import os
        api_key = os.getenv('HUNTER_API_KEY', '')
        if not api_key:
            return None
        try:
            import aiohttp
            # Convertir company name en domaine (heuristique simple)
            domain = company.lower().replace(' ', '').replace(',', '') + '.com'
            url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={api_key}&limit=5"
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    emails = data.get('data', {}).get('emails', [])
                    # Prioriser les emails avec titre similaire
                    title_l = (title or '').lower()
                    for e in emails:
                        pos = (e.get('position') or '').lower()
                        if title_l and any(w in pos for w in title_l.split()):
                            return {
                                'email': e['value'],
                                'name': f"{e.get('first_name','')} {e.get('last_name','')}".strip(),
                                'confidence': e.get('confidence', 0),
                                'source': 'hunter.io'
                            }
                    # Sinon premier email disponible
                    if emails:
                        e = emails[0]
                        return {
                            'email': e['value'],
                            'name': f"{e.get('first_name','')} {e.get('last_name','')}".strip(),
                            'confidence': e.get('confidence', 0),
                            'source': 'hunter.io'
                        }
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Hunter.io error: {e}")
        return None

    async def _scrape_company_email(self, company: str) -> Optional[Dict]:
        """Scrape company website for email pattern. V19.3: real scraping."""
        try:
            import aiohttp
            import re
            domain = company.lower().replace(' ', '').replace(',', '') + '.com'
            async with aiohttp.ClientSession() as sess:
                for path in ['/contact', '/about', '/']:
                    try:
                        async with sess.get(f"https://{domain}{path}", timeout=5) as resp:
                            if resp.status != 200:
                                continue
                            html = await resp.text()
                            # Chercher patterns email
                            emails = re.findall(
                                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                                html
                            )
                            # Filtrer emails génériques vs persos
                            personal = [e for e in emails if not any(
                                g in e.lower() for g in ['noreply', 'no-reply', 'info@', 'contact@']
                            )]
                            chosen = personal[0] if personal else (emails[0] if emails else None)
                            if chosen:
                                return {'email': chosen, 'source': 'scrape', 'confidence': 50}
                    except Exception:
                        continue
        except Exception:
            pass
        return None

    async def _get_company_info(self, company: str) -> Dict:
        """Get company details via Apollo or LinkedIn. V19.3: real fetch."""
        import os
        apollo_key = os.getenv('APOLLO_API_KEY', '')
        if apollo_key:
            try:
                import aiohttp
                url = "https://api.apollo.io/v1/organizations/search"
                payload = {"api_key": apollo_key, "q_organization_name": company}
                async with aiohttp.ClientSession() as sess:
                    async with sess.post(url, json=payload, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            orgs = data.get('organizations', [])
                            if orgs:
                                org = orgs[0]
                                return {
                                    'size': org.get('estimated_num_employees', 'SMB'),
                                    'revenue': org.get('annual_revenue', None),
                                    'tech_stack': org.get('technologies', [])[:10],
                                    'industry': org.get('industry', ''),
                                    'country': org.get('country', ''),
                                    'source': 'apollo'
                                }
            except Exception:
                pass
        # Fallback inference par nom de secteur
        return {
            'size': 'SMB',
            'revenue': None,
            'tech_stack': ['Linux', 'Automation'],
            'source': 'fallback'
        }

    async def _detect_ot_vulnerabilities(self, company: str, sector: str) -> List[str]:
        """Infer OT vulnerabilities based on sector. V19.3: sector-aware heuristics."""
        # Base de connaissance sectorielle (IEC 62443 / NIS2)
        sector_vulns = {
            'energy': ['Legacy SCADA (Siemens S7)', 'Unsegmented OT/IT networks',
                       'No IEC 62443-2-1 governance', 'Unpatched RTU firmware',
                       'Weak remote access (VPN only, no MFA)'],
            'manufacturing': ['Legacy PLCs (>10 years)', 'Flat network topology',
                              'No asset inventory', 'Unmonitored USB ports on HMIs',
                              'Vendor remote access without logging'],
            'transport': ['Signaling system isolation gaps', 'Unpatched Windows XP/7 HMIs',
                          'No network segmentation IT/OT', 'Weak PKI for train-to-ground'],
            'water': ['Remote telemetry over unencrypted cellular', 'Default PLC credentials',
                     'No anomaly detection on SCADA', 'Unpatched Modbus devices'],
            'logistics': ['WMS/ERP integration vulnerabilities', 'Unsecured IoT sensors',
                          'No segmentation warehouse OT', 'Legacy barcode infrastructure'],
        }
        sector_l = (sector or '').lower()
        for key, vulns in sector_vulns.items():
            if key in sector_l:
                return vulns
        # Fallback générique OT
        return ['Legacy SCADA', 'Unpatched systems', 'Inadequate segmentation',
                'No IEC 62443 compliance baseline', 'Missing OT/IT boundary controls']


# ============================================================================
# MAIN WORKFLOW ORCHESTRATOR
# ============================================================================

class ProspectionWorkflow:
    """
    Complete prospection workflow:
    Pain Detected → Enriched → Offer Generated → Ready for Outreach
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.pain_detector = PainDetectionEngine(
            config['serper_api'],
            LLMRouter(config)
        )
        self.prospect_enricher = ProspectEnrichmentEngine(
            config['apollo_api'],
            config['hunter_api'],
            LLMRouter(config)
        )
        self.offer_generator = OfferGenerator(config)
        self.state_manager = StateManager()
        self.memory = VectorDBIntegration()
        
    async def run_detection_cycle(self) -> List[PainSignal]:
        """Run pain detection across all sources"""
        
        pain_signals = []
        
        # Parallel detection
        job_pains = await self.pain_detector.detect_from_job_offers()
        news_pains = await self.pain_detector.detect_from_news()
        
        pain_signals.extend(job_pains)
        pain_signals.extend(news_pains)
        
        # Score and filter
        scored_pains = [p for p in pain_signals if p.confidence_score >= 0.7]
        
        print(f"🔍 Detection cycle: {len(scored_pains)} qualified pains detected")
        return scored_pains
    
    async def process_prospect(self, pain: PainSignal) -> Optional[Dict[str, Any]]:
        """
        Process single prospect through full workflow
        Returns ready offer or None if blocked
        """
        
        # Create state
        prospect_id = f"PROS_{int(datetime.now().timestamp())}"
        state = ProspectionState(
            prospect_id=prospect_id,
            state="detected",
            pain_signal=pain,
            created_at=datetime.now().isoformat()
        )
        
        try:
            # Step 1: Enrich
            print(f"📊 Enriching prospect for {pain.company}...")
            state.state = "enriching"
            enriched = await self.prospect_enricher.enrich(pain)
            
            if not enriched or not enriched.decision_maker_email:
                print(f"❌ Enrichment failed - marking for manual: {pain.company}")
                state.state = "failed"
                state.errors.append("Email validation failed - manual required")
                return None
            
            state.enriched_prospect = enriched
            
            # Step 2: Generate offer
            print(f"💼 Generating offer for {enriched.decision_maker_name}...")
            state.state = "offer_generating"
            offer = await self.offer_generator.generate(enriched)
            
            if not offer:
                state.state = "failed"
                state.errors.append("Offer generation failed")
                return None
            
            state.offer_generated = offer
            state.state = "ready"
            
            # Save to memory
            await self.memory.add(prospect_id, {
                'prospect': enriched.dict(),
                'offer': offer,
                'status': 'ready_for_outreach'
            })
            
            print(f"✅ Prospect {prospect_id} ready: {enriched.decision_maker_email}")
            return {
                'prospect_id': prospect_id,
                'enriched_prospect': enriched,
                'offer': offer,
                'status': 'ready'
            }
            
        except Exception as e:
            state.state = "failed"
            state.errors.append(str(e))
            print(f"❌ Prospect processing failed: {e}")
            return None
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        """
        Complete prospection cycle:
        Detect pains → Enrich prospects → Generate offers
        Runs every 24 hours in production
        """
        
        print("\n" + "="*60)
        print("🚀 PROSPECTION WORKFLOW CYCLE START")
        print("="*60)
        
        cycle_start = datetime.now().isoformat()
        results = {
            'cycle_start': cycle_start,
            'pains_detected': 0,
            'prospects_enriched': 0,
            'offers_ready': 0,
            'ready_prospects': []
        }
        
        try:
            # Detection
            pain_signals = await self.run_detection_cycle()
            results['pains_detected'] = len(pain_signals)
            
            # Process each prospect
            ready_count = 0
            for pain in pain_signals:
                prospect_result = await self.process_prospect(pain)
                if prospect_result:
                    results['ready_prospects'].append(prospect_result)
                    ready_count += 1
            
            results['prospects_enriched'] = len(pain_signals)
            results['offers_ready'] = ready_count
            
            print("\n" + "="*60)
            print(f"✅ CYCLE COMPLETE")
            print(f"   Pains detected: {results['pains_detected']}")
            print(f"   Offers ready: {results['offers_ready']}")
            print("="*60 + "\n")
            
            return results
            
        except Exception as e:
            print(f"❌ Workflow cycle failed: {e}")
            results['error'] = str(e)
            return results


# ============================================================================
# TEST & ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    
    # Test config
    config = {
        'serper_api': 'test_key',
        'apollo_api': 'test_key',
        'hunter_api': 'test_key',
        'anthropic_api': 'test_key',
        'groq_api': 'test_key'
    }
    
    # Initialize and run
    workflow = ProspectionWorkflow(config)
    
    # Run async
    async def main():
        result = await workflow.run_full_cycle()
        print("\nWorkflow result:")
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())
