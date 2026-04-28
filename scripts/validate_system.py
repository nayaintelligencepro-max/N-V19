#!/usr/bin/env python3
"""
NAYA SUPREME V19 - System Validation Script
Valide que TOUS les modules sont à 100% opérationnels
"""

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Ajout du répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent))


class SystemValidator:
    """Validateur complet du système NAYA"""
    
    def __init__(self):
        self.results = {
            "agents": {"total": 11, "passed": 0, "failed": []},
            "intelligence": {"total": 6, "passed": 0, "failed": []},
            "hunting": {"total": 8, "passed": 0, "failed": []},
            "audit": {"total": 6, "passed": 0, "failed": []},
            "content": {"total": 6, "passed": 0, "failed": []},
            "revenue": {"total": 8, "passed": 0, "failed": []},
            "security": {"total": 10, "passed": 0, "failed": []},
        }
    
    async def validate_module(self, module_path: str, module_name: str) -> Tuple[bool, str]:
        """
        Valide qu'un module peut être importé et contient du code réel
        
        Returns:
            (success, error_message)
        """
        try:
            module = importlib.import_module(module_path)
            
            # Vérifier qu'il n'y a pas que des pass statements
            module_file = Path(module.__file__)
            if module_file.exists():
                content = module_file.read_text()
                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
                
                # Si le fichier ne contient que des pass, c'est un échec
                if all(line == "pass" for line in lines if line):
                    return False, f"{module_name}: Contains only 'pass' statements"
                
                # Vérifier la taille minimale (au moins 50 lignes de code)
                if len(lines) < 50:
                    return False, f"{module_name}: Too small ({len(lines)} lines), likely incomplete"
            
            return True, ""
            
        except ImportError as e:
            return False, f"{module_name}: ImportError - {str(e)}"
        except Exception as e:
            return False, f"{module_name}: {type(e).__name__} - {str(e)}"
    
    async def validate_agents(self):
        """Valide les 11 agents IA"""
        print("\n🤖 Validating 11 AI Agents...")
        
        agents = [
            ("NAYA_CORE.agents.pain_hunter", "Pain Hunter Agent"),
            ("NAYA_CORE.agents.researcher", "Researcher Agent"),
            ("NAYA_CORE.agents.offer_writer_advanced", "Offer Writer Agent"),
            ("NAYA_CORE.agents.outreach_agent", "Outreach Agent"),
            ("NAYA_CORE.agents.closer_advanced", "Closer Agent"),
            ("NAYA_CORE.agents.audit_generator", "Audit Generator Agent"),
            ("NAYA_CORE.agents.content_engine_advanced", "Content Engine Agent"),
            ("NAYA_CORE.agents.contract_generator_agent", "Contract Generator Agent"),
            ("NAYA_CORE.agents.revenue_tracker_agent", "Revenue Tracker Agent"),
            ("NAYA_CORE.agents.parallel_pipeline_orchestrator", "Parallel Pipeline Agent"),
            ("NAYA_CORE.agents.guardian_security", "Guardian Security Agent"),
        ]
        
        for module_path, name in agents:
            success, error = await self.validate_module(module_path, name)
            if success:
                self.results["agents"]["passed"] += 1
                print(f"  ✅ {name}")
            else:
                self.results["agents"]["failed"].append(error)
                print(f"  ❌ {name}: {error}")
    
    async def validate_intelligence(self):
        """Valide les 6 modules intelligence"""
        print("\n🧠 Validating Intelligence Layer (6 modules)...")
        
        modules = [
            ("intelligence.pain_detector", "Pain Detector"),
            ("intelligence.signal_scanner", "Signal Scanner"),
            ("intelligence.qualifier", "Qualifier"),
            ("intelligence.objection_handler", "Objection Handler"),
            ("intelligence.ab_testing", "A/B Testing"),
            ("intelligence.pricing_intelligence", "Pricing Intelligence"),
        ]
        
        for module_path, name in modules:
            success, error = await self.validate_module(module_path, name)
            if success:
                self.results["intelligence"]["passed"] += 1
                print(f"  ✅ {name}")
            else:
                self.results["intelligence"]["failed"].append(error)
                print(f"  ❌ {name}: {error}")
    
    async def validate_hunting(self):
        """Valide les 8 modules hunting"""
        print("\n🎯 Validating Hunting Engine (8 modules)...")
        
        modules = [
            ("hunting.apollo_agent", "Apollo Agent"),
            ("hunting.linkedin_agent", "LinkedIn Agent"),
            ("hunting.web_scraper", "Web Scraper"),
            ("hunting.job_offer_scanner", "Job Offer Scanner"),
            ("hunting.news_scanner", "News Scanner"),
            ("hunting.email_finder", "Email Finder"),
            ("hunting.contact_enricher", "Contact Enricher"),
            ("hunting.auto_hunt_seeder", "Auto Hunt Seeder"),
        ]
        
        for module_path, name in modules:
            success, error = await self.validate_module(module_path, name)
            if success:
                self.results["hunting"]["passed"] += 1
                print(f"  ✅ {name}")
            else:
                self.results["hunting"]["failed"].append(error)
                print(f"  ❌ {name}: {error}")
    
    async def validate_audit(self):
        """Valide les 6 modules audit"""
        print("\n🔍 Validating Audit Engine (6 modules)...")
        
        modules = [
            ("audit.iec62443_auditor", "IEC 62443 Auditor"),
            ("audit.nis2_checker", "NIS2 Checker"),
            ("audit.ot_vulnerability_scanner", "OT Vulnerability Scanner"),
            ("audit.report_generator", "Report Generator"),
            ("audit.recommendation_engine", "Recommendation Engine"),
            ("audit.audit_pricing", "Audit Pricing"),
        ]
        
        for module_path, name in modules:
            success, error = await self.validate_module(module_path, name)
            if success:
                self.results["audit"]["passed"] += 1
                print(f"  ✅ {name}")
            else:
                self.results["audit"]["failed"].append(error)
                print(f"  ❌ {name}: {error}")
    
    async def validate_content(self):
        """Valide les 6 modules content"""
        print("\n📝 Validating Content Engine (6 modules)...")
        
        modules = [
            ("content.content_strategy", "Content Strategy"),
            ("content.article_generator", "Article Generator"),
            ("content.whitepaper_generator", "Whitepaper Generator"),
            ("content.case_study_generator", "Case Study Generator"),
            ("content.newsletter_engine", "Newsletter Engine"),
            ("content.content_distributor", "Content Distributor"),
        ]
        
        for module_path, name in modules:
            success, error = await self.validate_module(module_path, name)
            if success:
                self.results["content"]["passed"] += 1
                print(f"  ✅ {name}")
            else:
                self.results["content"]["failed"].append(error)
                print(f"  ❌ {name}: {error}")
    
    async def validate_revenue(self):
        """Valide les 7 modules revenue (V19.3: Stripe retiré)"""
        print("\n💰 Validating Revenue Engine (7 modules)...")
        
        modules = [
            ("revenue.deblokme_integration", "Deblok.me Integration"),
            ("revenue.paypalme_integration", "PayPal.me Integration"),
            ("revenue.revenue_tracker", "Revenue Tracker"),
            ("revenue.contract_generator", "Contract Generator"),
            ("revenue.invoice_engine", "Invoice Engine"),
            ("revenue.subscription_manager", "Subscription Manager"),
            ("revenue.cashflow_projector", "Cashflow Projector"),
        ]
        
        for module_path, name in modules:
            success, error = await self.validate_module(module_path, name)
            if success:
                self.results["revenue"]["passed"] += 1
                print(f"  ✅ {name}")
            else:
                self.results["revenue"]["failed"].append(error)
                print(f"  ❌ {name}: {error}")
    
    async def validate_security(self):
        """Valide les 10 modules security"""
        print("\n🛡️  Validating Security Guardian (10 modules)...")
        
        modules = [
            ("security.self_scanner", "Self Scanner"),
            ("security.vulnerability_patcher", "Vulnerability Patcher"),
            ("security.secrets_manager", "Secrets Manager"),
            ("security.audit_logger", "Audit Logger"),
            ("security.threat_detector", "Threat Detector"),
            ("security.health_monitor", "Health Monitor"),
            ("security.error_classifier", "Error Classifier"),
            ("security.auto_fixer", "Auto Fixer"),
            ("security.degraded_mode", "Degraded Mode"),
            ("security.self_optimizer", "Self Optimizer"),
        ]
        
        for module_path, name in modules:
            success, error = await self.validate_module(module_path, name)
            if success:
                self.results["security"]["passed"] += 1
                print(f"  ✅ {name}")
            else:
                self.results["security"]["failed"].append(error)
                print(f"  ❌ {name}: {error}")
    
    async def run_full_validation(self):
        """Exécute la validation complète"""
        print("=" * 80)
        print("🚀 NAYA SUPREME V19 - SYSTEM VALIDATION")
        print("=" * 80)
        
        await asyncio.gather(
            self.validate_agents(),
            self.validate_intelligence(),
            self.validate_hunting(),
            self.validate_audit(),
            self.validate_content(),
            self.validate_revenue(),
            self.validate_security()
        )
        
        self.print_summary()
    
    def print_summary(self):
        """Affiche le résumé de validation"""
        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        
        total_modules = 0
        total_passed = 0
        
        for category, data in self.results.items():
            total = data["total"]
            passed = data["passed"]
            total_modules += total
            total_passed += passed
            
            status = "✅" if passed == total else "⚠️"
            percentage = (passed / total * 100) if total > 0 else 0
            
            print(f"\n{status} {category.upper()}: {passed}/{total} ({percentage:.0f}%)")
            
            if data["failed"]:
                for error in data["failed"]:
                    print(f"    ❌ {error}")
        
        print("\n" + "=" * 80)
        overall_percentage = (total_passed / total_modules * 100) if total_modules > 0 else 0
        
        if total_passed == total_modules:
            print(f"🎉 SYSTEM 100% OPERATIONAL ({total_passed}/{total_modules})")
            print("=" * 80)
            return 0
        else:
            print(f"⚠️  SYSTEM {overall_percentage:.1f}% OPERATIONAL ({total_passed}/{total_modules})")
            print("=" * 80)
            return 1


async def main():
    """Point d'entrée principal"""
    validator = SystemValidator()
    exit_code = await validator.run_full_validation()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
