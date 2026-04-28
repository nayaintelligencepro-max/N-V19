"""
NAYA V21 — NIS2 Report Generator
Génération de rapports PDF professionnels pour les audits NIS2.
Utilise reportlab si disponible, sinon format texte structuré.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .nis2_checker import NIS2Assessment

log = logging.getLogger("NAYA.SAAS_NIS2.REPORT")

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "data" / "saas_nis2" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.platypus import HRFlowable
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class NIS2ReportGenerator:
    """Génère des rapports de conformité NIS2 en PDF ou texte."""

    def generate(self, assessment: "NIS2Assessment") -> str:
        """
        Génère un rapport et retourne le chemin du fichier.
        Utilise reportlab si disponible, sinon texte structuré.
        """
        if REPORTLAB_AVAILABLE:
            return self._generate_pdf(assessment)
        return self._generate_text(assessment)

    def _generate_pdf(self, assessment: "NIS2Assessment") -> str:
        """Génération PDF via reportlab."""
        path = REPORTS_DIR / f"nis2_report_{assessment.assessment_id[:8]}.pdf"
        doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
                                topMargin=25*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=18, spaceAfter=6)
        h2_style = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceAfter=4)
        normal = styles["Normal"]

        story = []
        # Header
        story.append(Paragraph("🔒 RAPPORT CONFORMITÉ NIS2", title_style))
        story.append(Paragraph(f"Entreprise: <b>{assessment.company}</b>", normal))
        story.append(Paragraph(f"Secteur: {assessment.sector}", normal))
        story.append(Paragraph(f"Date: {assessment.created_at[:10]}", normal))
        story.append(HRFlowable(width="100%"))
        story.append(Spacer(1, 5*mm))

        # Score
        score_color = colors.green if assessment.score >= 60 else (colors.orange if assessment.score >= 40 else colors.red)
        story.append(Paragraph(f"<b>Score de Conformité NIS2: {assessment.score}/100 — {assessment.tier.upper()}</b>", h2_style))
        story.append(Spacer(1, 3*mm))

        # Lacunes
        if assessment.gaps:
            story.append(Paragraph("<b>Lacunes Identifiées</b>", h2_style))
            for gap in assessment.gaps:
                story.append(Paragraph(f"• {gap}", normal))
            story.append(Spacer(1, 3*mm))

        # Recommandations
        if assessment.recommendations:
            story.append(Paragraph("<b>Recommandations Prioritaires</b>", h2_style))
            for rec in assessment.recommendations:
                story.append(Paragraph(f"✓ {rec}", normal))
            story.append(Spacer(1, 3*mm))

        # Footer
        story.append(HRFlowable(width="100%"))
        story.append(Paragraph(
            "Rapport généré par NAYA SUPREME V21 — Contact: naya@naya-supreme.com",
            ParagraphStyle("footer", parent=normal, fontSize=8, textColor=colors.grey),
        ))

        doc.build(story)
        log.info("PDF généré: %s", path)
        return str(path)

    def _generate_text(self, assessment: "NIS2Assessment") -> str:
        """Génération rapport texte structuré (fallback sans reportlab)."""
        path = REPORTS_DIR / f"nis2_report_{assessment.assessment_id[:8]}.txt"
        lines = [
            "=" * 60,
            "RAPPORT CONFORMITÉ NIS2 — NAYA SUPREME V21",
            "=" * 60,
            f"Entreprise   : {assessment.company}",
            f"Secteur      : {assessment.sector}",
            f"Contact      : {assessment.contact_email}",
            f"Date         : {assessment.created_at[:10]}",
            f"Assessment ID: {assessment.assessment_id}",
            "",
            f"SCORE DE CONFORMITÉ NIS2 : {assessment.score}/100",
            f"NIVEAU                   : {assessment.tier.upper()}",
            "",
        ]
        if assessment.gaps:
            lines.append("LACUNES IDENTIFIÉES :")
            for gap in assessment.gaps:
                lines.append(f"  ✗ {gap}")
            lines.append("")
        if assessment.recommendations:
            lines.append("RECOMMANDATIONS PRIORITAIRES :")
            for rec in assessment.recommendations:
                lines.append(f"  → {rec}")
            lines.append("")
        lines += [
            "─" * 60,
            "Pour accéder au rapport complet avec roadmap de remédiation,",
            "abonnez-vous au plan NIS2 Starter (500 EUR/mois).",
            "Contact : naya@naya-supreme.com",
            "=" * 60,
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        log.info("Rapport texte généré: %s", path)
        return str(path)


# ── Singleton ─────────────────────────────────────────────────────────────────
_generator: Optional[NIS2ReportGenerator] = None


def get_report_generator() -> NIS2ReportGenerator:
    global _generator
    if _generator is None:
        _generator = NIS2ReportGenerator()
    return _generator
