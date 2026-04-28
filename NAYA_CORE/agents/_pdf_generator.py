"""
NAYA V19.3 — Générateur PDF réel (reportlab).

Utilisé par contract_generator_agent pour produire :
  - Contrats de service
  - Factures TVA
  - Audits IEC 62443 / NIS2

Fallback texte transparent si reportlab absent (placeholder lisible, aucune
donnée perdue), pour que le système tourne en dev sans dépendance lourde.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class PdfGeneratorReal:
    """Générateur PDF production-ready via reportlab."""

    def __init__(self) -> None:
        try:
            from reportlab.lib.pagesizes import A4  # noqa: F401
            from reportlab.lib.styles import getSampleStyleSheet  # noqa: F401
            from reportlab.platypus import SimpleDocTemplate  # noqa: F401

            self._available = True
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[pdf_generator] reportlab indisponible ({exc}) — fallback texte")
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def generate(self, template_name: str, output_path: str, content: Dict[str, Any]) -> str:
        """Génère un PDF à partir d'un template et du contenu fourni."""
        if not self._available:
            return self._write_text_fallback(output_path, template_name, content)

        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'NayaTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=20,
        )
        body_style = styles['BodyText']

        story = []

        # Titre
        title = content.get('title') or ("FACTURE" if template_name == "invoice" else "CONTRAT")
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.5 * cm))

        # Détails sous forme de tableau
        if template_name == "invoice":
            rows = [
                ["Numéro facture", content.get('invoice_id', '')],
                ["Date", content.get('date', '')],
                ["Échéance", content.get('due_date', '')],
                ["Client", content.get('client_company', '')],
                ["Contact", content.get('client_name', '')],
                ["Adresse", content.get('client_address', '')],
                ["Prestataire", content.get('provider', 'NAYA SUPREME')],
                ["Description", content.get('description', '')],
                ["Montant HT", f"{content.get('amount_ht', 0):,.2f} EUR"],
                ["TVA (20%)", f"{content.get('tva', 0):,.2f} EUR"],
                ["Montant TTC", f"{content.get('amount_ttc', 0):,.2f} EUR"],
                ["Lien de paiement", content.get('payment_link', '')],
            ]
        else:
            rows = [
                ["Contrat N°", content.get('contract_id', '')],
                ["Date", content.get('date', '')],
                ["Client", content.get('client_company', '')],
                ["Contact", content.get('client_name', '')],
                ["Adresse client", content.get('client_address', '')],
                ["Prestataire", content.get('provider', 'NAYA SUPREME')],
                ["Adresse prestataire", content.get('provider_address', 'Polynésie française')],
                ["Service", content.get('service_description', '')],
                ["Livrables", ", ".join(content.get('deliverables', [])) if isinstance(content.get('deliverables'), list) else str(content.get('deliverables', ''))],
                ["Montant", content.get('amount', '')],
                ["Conditions", content.get('payment_terms', '')],
                ["Date début", content.get('start_date', '')],
                ["Date fin", content.get('end_date', '')],
            ]

        table = Table(rows, colWidths=[5 * cm, 12 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(table)

        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph(
            "Document généré automatiquement par NAYA SUPREME V19.3. "
            "Toute modification invalide la signature SHA-256 associée.",
            body_style,
        ))

        doc.build(story)
        logger.info(f"[pdf_generator] PDF généré : {output_path}")
        return output_path

    def _write_text_fallback(self, output_path: str, template_name: str,
                             content: Dict[str, Any]) -> str:
        """Fallback texte quand reportlab n'est pas dispo."""
        txt_path = output_path.replace('.pdf', '.txt')
        Path(txt_path).parent.mkdir(parents=True, exist_ok=True)
        with open(txt_path, 'w', encoding='utf-8') as fh:
            fh.write(f"=== {template_name.upper()} ===\n")
            for k, v in content.items():
                fh.write(f"{k}: {v}\n")
        logger.info(f"[pdf_generator] fallback texte écrit : {txt_path}")
        return txt_path


__all__ = ['PdfGeneratorReal']
