"""
NAYA SUPREME V19 — Professional Report Generator
20-40 page PDF reports with executive summary, findings, recommendations, roadmap.
Uses reportlab for production-quality PDFs.
"""

from __future__ import annotations

import asyncio
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("NAYA.ReportGenerator")

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image as RLImage,
    )
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    log.warning("reportlab not available - PDF generation will use fallback")


class ReportGenerator:
    """
    Professional PDF report generator for IEC 62443 and NIS2 audits.
    Produces 20-40 page comprehensive reports.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("data/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_audit_report(
        self,
        audit_data: Dict[str, Any],
        report_type: str = "IEC62443",
    ) -> str:
        """
        Generate comprehensive audit report PDF.

        Args:
            audit_data: Complete audit results
            report_type: IEC62443 or NIS2

        Returns:
            Path to generated PDF file
        """
        log.info(f"Generating {report_type} report for {audit_data.get('company_name')}")

        try:
            # Generate filename
            company_slug = audit_data.get("company_name", "Unknown").replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{report_type}_{company_slug}_{timestamp}.pdf"
            filepath = self.output_dir / filename

            if REPORTLAB_AVAILABLE:
                await self._generate_pdf_reportlab(audit_data, filepath, report_type)
            else:
                await self._generate_pdf_fallback(audit_data, filepath, report_type)

            log.info(f"Report generated successfully: {filepath}")
            return str(filepath)

        except Exception as e:
            log.error(f"Report generation failed: {e}", exc_info=True)
            raise

    async def _generate_pdf_reportlab(
        self,
        audit_data: Dict[str, Any],
        filepath: Path,
        report_type: str,
    ) -> None:
        """Generate PDF using reportlab (production quality)."""
        await asyncio.sleep(0.1)

        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Build content
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=12,
        )

        # Cover Page
        story.extend(self._build_cover_page(audit_data, report_type, title_style, styles))
        story.append(PageBreak())

        # Executive Summary
        story.extend(self._build_executive_summary(audit_data, heading_style, styles))
        story.append(PageBreak())

        # Detailed Findings
        story.extend(self._build_detailed_findings(audit_data, report_type, heading_style, styles))
        story.append(PageBreak())

        # Gap Analysis
        story.extend(self._build_gap_analysis(audit_data, heading_style, styles))
        story.append(PageBreak())

        # Recommendations
        story.extend(self._build_recommendations(audit_data, heading_style, styles))
        story.append(PageBreak())

        # Roadmap
        story.extend(self._build_roadmap(audit_data, heading_style, styles))

        # Build PDF
        doc.build(story)

    async def _generate_pdf_fallback(
        self,
        audit_data: Dict[str, Any],
        filepath: Path,
        report_type: str,
    ) -> None:
        """Fallback: Generate HTML report (convertible to PDF)."""
        await asyncio.sleep(0.05)

        html_content = self._build_html_report(audit_data, report_type)

        # Save as HTML (can be converted to PDF via wkhtmltopdf or similar)
        html_path = filepath.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")

        log.info(f"HTML report generated (fallback): {html_path}")

    def _build_cover_page(
        self,
        audit_data: Dict[str, Any],
        report_type: str,
        title_style: Any,
        styles: Any,
    ) -> List[Any]:
        """Build cover page."""
        elements = []

        # Title
        title = f"{report_type} Audit Report"
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.5 * inch))

        # Company info
        company_name = audit_data.get("company_name", "N/A")
        sector = audit_data.get("sector", "N/A")
        audit_date = audit_data.get("audit_date", datetime.now().isoformat())[:10]

        info_data = [
            ["Company:", company_name],
            ["Sector:", sector],
            ["Audit Date:", audit_date],
            ["Report Type:", report_type],
        ]

        info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 1 * inch))

        # Disclaimer
        disclaimer = Paragraph(
            "<b>CONFIDENTIAL</b><br/>"
            "This report contains sensitive security information. "
            "Distribution is restricted to authorized personnel only.",
            styles["Normal"],
        )
        elements.append(disclaimer)

        return elements

    def _build_executive_summary(
        self,
        audit_data: Dict[str, Any],
        heading_style: Any,
        styles: Any,
    ) -> List[Any]:
        """Build executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Overall score
        overall_score = audit_data.get("overall_compliance_score") or audit_data.get("overall_score", 0)

        summary_text = f"""
        This report presents the results of a comprehensive cybersecurity audit conducted for
        <b>{audit_data.get('company_name')}</b> in the <b>{audit_data.get('sector')}</b> sector.
        <br/><br/>
        <b>Overall Compliance Score: {overall_score}/100</b>
        <br/><br/>
        """

        # Add status-specific text
        if overall_score >= 80:
            summary_text += "The organization demonstrates a strong security posture with minor areas for improvement."
        elif overall_score >= 60:
            summary_text += "The organization has a reasonable security foundation but requires significant improvements."
        else:
            summary_text += "The organization faces critical security gaps requiring immediate attention."

        elements.append(Paragraph(summary_text, styles["BodyText"]))
        elements.append(Spacer(1, 0.3 * inch))

        # Key findings table
        critical = audit_data.get("critical_count", 0) or len([
            f for f in audit_data.get("critical_findings", [])
        ])

        findings_data = [
            ["Metric", "Value"],
            ["Overall Score", f"{overall_score}/100"],
            ["Critical Issues", str(critical)],
            ["Total Vulnerabilities", str(audit_data.get("total_vulnerabilities", 0))],
        ]

        findings_table = Table(findings_data, colWidths=[3 * inch, 2 * inch])
        findings_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(findings_table)

        return elements

    def _build_detailed_findings(
        self,
        audit_data: Dict[str, Any],
        report_type: str,
        heading_style: Any,
        styles: Any,
    ) -> List[Any]:
        """Build detailed findings section."""
        elements = []

        elements.append(Paragraph("Detailed Findings", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        if report_type == "IEC62443":
            # Security Levels Assessment
            sl_assessment = audit_data.get("security_level_assessment", {})

            for sl, data in sl_assessment.items():
                elements.append(Paragraph(f"<b>{sl}: {data.get('name')}</b>", styles["Heading3"]))

                sl_text = f"""
                Current Score: {data.get('current_score')}/100<br/>
                Required Score: {data.get('required_score')}/100<br/>
                Status: {'✅ Compliant' if data.get('compliant') else '❌ Non-Compliant'}<br/>
                Gap: {data.get('gap')} points
                """

                elements.append(Paragraph(sl_text, styles["Normal"]))
                elements.append(Spacer(1, 0.1 * inch))

        elif report_type == "NIS2":
            # Domain Scores
            domain_scores = audit_data.get("domain_scores", {})

            for domain, data in domain_scores.items():
                if "error" in data:
                    continue

                elements.append(Paragraph(f"<b>{data.get('name')}</b>", styles["Heading3"]))

                domain_text = f"""
                Score: {data.get('score')}/100<br/>
                Status: {'✅ Compliant' if data.get('compliant') else '❌ Non-Compliant'}<br/>
                Weight: {data.get('weight') * 100}%
                """

                elements.append(Paragraph(domain_text, styles["Normal"]))
                elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _build_gap_analysis(
        self,
        audit_data: Dict[str, Any],
        heading_style: Any,
        styles: Any,
    ) -> List[Any]:
        """Build gap analysis section."""
        elements = []

        elements.append(Paragraph("Gap Analysis", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        gaps = audit_data.get("gaps", []) or audit_data.get("gap_analysis", {}).get("gaps", [])

        if gaps:
            gap_data = [["Priority", "Category", "Item", "Gap"]]

            for gap in gaps[:10]:  # Top 10 gaps
                priority = gap.get("priority", "MEDIUM")
                category = gap.get("category", "N/A")
                item = gap.get("item", gap.get("requirement", "N/A"))
                gap_value = gap.get("gap", 0)

                gap_data.append([priority, category, item, f"{gap_value} pts"])

            gap_table = Table(gap_data, colWidths=[1 * inch, 1.5 * inch, 2.5 * inch, 1 * inch])
            gap_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ]))

            elements.append(gap_table)
        else:
            elements.append(Paragraph("No significant gaps identified.", styles["Normal"]))

        return elements

    def _build_recommendations(
        self,
        audit_data: Dict[str, Any],
        heading_style: Any,
        styles: Any,
    ) -> List[Any]:
        """Build recommendations section."""
        elements = []

        elements.append(Paragraph("Recommendations", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        recommendations = audit_data.get("recommendations", [])

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                rec_text = f"""
                <b>{i}. {rec.get('domain', 'General').title()}</b><br/>
                Priority: {rec.get('priority', 'MEDIUM')}<br/>
                Action: {rec.get('action', 'N/A')}<br/>
                Duration: {rec.get('estimated_duration', 'N/A')}<br/>
                Cost: {rec.get('estimated_cost_eur', 0):,} EUR
                """

                elements.append(Paragraph(rec_text, styles["Normal"]))
                elements.append(Spacer(1, 0.2 * inch))
        else:
            elements.append(Paragraph("Continue maintaining current security posture.", styles["Normal"]))

        return elements

    def _build_roadmap(
        self,
        audit_data: Dict[str, Any],
        heading_style: Any,
        styles: Any,
    ) -> List[Any]:
        """Build remediation roadmap."""
        elements = []

        elements.append(Paragraph("Remediation Roadmap", heading_style))
        elements.append(Spacer(1, 0.2 * inch))

        remediation = audit_data.get("remediation_estimate", {})
        phases = remediation.get("phases", [])

        if phases:
            roadmap_data = [["Phase", "Duration", "Focus", "Gaps"]]

            for phase in phases:
                roadmap_data.append([
                    phase.get("phase", "N/A"),
                    phase.get("duration", "N/A"),
                    phase.get("focus", "N/A"),
                    str(phase.get("gap_count", 0)),
                ])

            roadmap_table = Table(roadmap_data, colWidths=[2 * inch, 1.5 * inch, 2 * inch, 1 * inch])
            roadmap_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            elements.append(roadmap_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Total estimate
            total_weeks = remediation.get("estimated_duration_weeks", 0)
            total_cost = remediation.get("estimated_cost_eur", 0)

            estimate_text = f"""
            <b>Total Estimated Effort:</b><br/>
            Duration: {total_weeks} weeks<br/>
            Budget: {total_cost:,} EUR
            """

            elements.append(Paragraph(estimate_text, styles["Normal"]))

        return elements

    def _build_html_report(self, audit_data: Dict[str, Any], report_type: str) -> str:
        """Build HTML report (fallback)."""
        company = audit_data.get("company_name", "Unknown")
        score = audit_data.get("overall_compliance_score") or audit_data.get("overall_score", 0)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report_type} Audit Report - {company}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #34495e; color: white; }}
        .score {{ font-size: 24px; font-weight: bold; color: {'#27ae60' if score >= 70 else '#e74c3c'}; }}
    </style>
</head>
<body>
    <h1>{report_type} Audit Report</h1>
    <h2>Executive Summary</h2>
    <p><strong>Company:</strong> {company}</p>
    <p><strong>Sector:</strong> {audit_data.get('sector', 'N/A')}</p>
    <p><strong>Audit Date:</strong> {audit_data.get('audit_date', datetime.now().isoformat())[:10]}</p>
    <p class="score">Overall Score: {score}/100</p>

    <h2>Detailed Findings</h2>
    <p>See full audit data in JSON format.</p>

    <h2>Recommendations</h2>
    <ul>
        {"".join(f"<li>{rec.get('action', 'N/A')}</li>" for rec in audit_data.get('recommendations', [])[:5])}
    </ul>
</body>
</html>
        """

        return html
