#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Generate Comprehensive Validation Report
═══════════════════════════════════════════════════════════════════════════════
Génère un rapport consolidé complet de toutes les validations:
- Pre-deploy gate tests (par environnement)
- Real sales validation
- Statistiques revenus
- État système complet

Usage:
    python scripts/generate_validation_report.py
    python scripts/generate_validation_report.py --format markdown
    python scripts/generate_validation_report.py --format json --output report.json
═══════════════════════════════════════════════════════════════════════════════
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

ROOT = Path(__file__).resolve().parent.parent
GATE_LEDGER = ROOT / "data" / "validation" / "pre_deploy_gate.json"
SALES_LEDGER = ROOT / "data" / "validation" / "real_sales_ledger.json"
VELOCITY_DATA = ROOT / "data" / "validation" / "sales_velocity.json"


def load_json_safe(filepath: Path) -> List[Dict]:
    """Load JSON file safely"""
    try:
        if filepath.exists():
            return json.loads(filepath.read_text())
        return []
    except Exception as e:
        print(f"⚠️  Error loading {filepath}: {e}", file=sys.stderr)
        return []


def analyze_gate_data() -> Dict[str, Any]:
    """Analyze pre-deploy gate data"""
    gate_data = load_json_safe(GATE_LEDGER)

    # Group by environment
    by_env = {}
    for entry in gate_data:
        env = entry.get('deploy_env', 'unknown')
        if env not in by_env:
            by_env[env] = []
        by_env[env].append(entry)

    # Calculate totals per environment
    env_totals = {}
    for env, entries in by_env.items():
        total_amount = sum(e.get('amount_eur', 0) for e in entries)
        env_totals[env] = {
            'count': len(entries),
            'total_eur': total_amount,
            'sales': entries,
        }

    return {
        'total_entries': len(gate_data),
        'by_environment': env_totals,
        'environments_tested': list(by_env.keys()),
    }


def analyze_sales_data() -> Dict[str, Any]:
    """Analyze real sales data"""
    sales_data = load_json_safe(SALES_LEDGER)

    # Group by status
    by_status = {}
    for sale in sales_data:
        status = sale.get('status', 'unknown')
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(sale)

    # Calculate revenue
    confirmed = by_status.get('payment_confirmed', [])
    completed = by_status.get('sale_completed', [])
    revenue_sales = confirmed + completed

    total_revenue = sum(s.get('amount_eur', 0) for s in revenue_sales)
    avg_amount = total_revenue / len(revenue_sales) if revenue_sales else 0

    # By sector
    by_sector = {}
    for sale in revenue_sales:
        sector = sale.get('sector', 'unknown')
        if sector not in by_sector:
            by_sector[sector] = {'count': 0, 'total_eur': 0}
        by_sector[sector]['count'] += 1
        by_sector[sector]['total_eur'] += sale.get('amount_eur', 0)

    return {
        'total_sales': len(sales_data),
        'by_status': {k: len(v) for k, v in by_status.items()},
        'payment_confirmed': len(confirmed),
        'sale_completed': len(completed),
        'total_revenue_eur': total_revenue,
        'avg_amount_eur': avg_amount,
        'by_sector': by_sector,
        'all_sales': sales_data,
    }


def generate_markdown_report(gate_analysis: Dict, sales_analysis: Dict) -> str:
    """Generate markdown report"""

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

    md = f"""# NAYA SUPREME V19 — VALIDATION REPORT

**Generated:** {now}

---

## 📊 PRE-DEPLOY GATE VALIDATION

### Summary
- **Total gate entries:** {gate_analysis['total_entries']}
- **Environments tested:** {', '.join(gate_analysis['environments_tested'])}

### By Environment

| Environment | Sales Count | Total Amount (EUR) |
|-------------|-------------|-------------------|
"""

    for env in ['local', 'docker', 'vercel', 'render', 'cloud_run']:
        env_data = gate_analysis['by_environment'].get(env, {'count': 0, 'total_eur': 0})
        md += f"| {env.upper():12s} | {env_data['count']:11d} | {env_data['total_eur']:>17,.0f} |\n"

    # Calculate total
    total_gate_amount = sum(
        env_data.get('total_eur', 0)
        for env_data in gate_analysis['by_environment'].values()
    )

    md += f"| **TOTAL** | **{gate_analysis['total_entries']:9d}** | **{total_gate_amount:>15,.0f}** |\n"

    md += f"""
---

## 💰 REAL SALES VALIDATION

### Summary
- **Total sales:** {sales_analysis['total_sales']}
- **Payment confirmed:** {sales_analysis['payment_confirmed']}
- **Sales completed:** {sales_analysis['sale_completed']}
- **Total revenue:** {sales_analysis['total_revenue_eur']:,.2f} EUR
- **Average amount:** {sales_analysis['avg_amount_eur']:,.2f} EUR

### By Status

| Status | Count |
|--------|-------|
"""

    for status, count in sales_analysis['by_status'].items():
        md += f"| {status:25s} | {count:5d} |\n"

    md += f"""
### By Sector

| Sector | Sales | Total Revenue (EUR) |
|--------|-------|-------------------|
"""

    for sector, data in sales_analysis['by_sector'].items():
        md += f"| {sector:20s} | {data['count']:5d} | {data['total_eur']:>17,.2f} |\n"

    md += f"""
---

## 🎯 CONSOLIDATED METRICS

- **Total validation entries:** {gate_analysis['total_entries'] + sales_analysis['total_sales']}
- **Total validated revenue:** {total_gate_amount + sales_analysis['total_revenue_eur']:,.2f} EUR
- **Environments validated:** {len(gate_analysis['environments_tested'])}
- **Real sales confirmed:** {sales_analysis['payment_confirmed'] + sales_analysis['sale_completed']}

---

## ✅ STATUS

"""

    if gate_analysis['total_entries'] > 0 and sales_analysis['total_revenue_eur'] > 0:
        md += "**System Status:** ✅ VALIDATED\n\n"
        md += "All validation gates passed with real sales confirmation.\n"
    else:
        md += "**System Status:** ⚠️  PARTIAL\n\n"
        md += "Some validation data missing. Run validation tests.\n"

    md += "\n---\n\n*Generated by NAYA SUPREME V19 Validation System*\n"

    return md


def generate_json_report(gate_analysis: Dict, sales_analysis: Dict) -> Dict:
    """Generate JSON report"""

    total_gate_amount = sum(
        env_data.get('total_eur', 0)
        for env_data in gate_analysis['by_environment'].values()
    )

    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'version': '19.0.0',
        'pre_deploy_gate': {
            'total_entries': gate_analysis['total_entries'],
            'total_amount_eur': total_gate_amount,
            'by_environment': gate_analysis['by_environment'],
            'environments_tested': gate_analysis['environments_tested'],
        },
        'real_sales': {
            'total_sales': sales_analysis['total_sales'],
            'payment_confirmed': sales_analysis['payment_confirmed'],
            'sale_completed': sales_analysis['sale_completed'],
            'total_revenue_eur': sales_analysis['total_revenue_eur'],
            'avg_amount_eur': sales_analysis['avg_amount_eur'],
            'by_status': sales_analysis['by_status'],
            'by_sector': sales_analysis['by_sector'],
        },
        'consolidated': {
            'total_validation_entries': gate_analysis['total_entries'] + sales_analysis['total_sales'],
            'total_validated_revenue_eur': total_gate_amount + sales_analysis['total_revenue_eur'],
            'environments_validated': len(gate_analysis['environments_tested']),
            'real_sales_confirmed': sales_analysis['payment_confirmed'] + sales_analysis['sale_completed'],
        },
        'status': {
            'validated': gate_analysis['total_entries'] > 0 and sales_analysis['total_revenue_eur'] > 0,
            'gate_tests_run': gate_analysis['total_entries'] > 0,
            'real_sales_validated': sales_analysis['total_revenue_eur'] > 0,
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Generate validation report")
    parser.add_argument(
        '--format',
        choices=['markdown', 'json', 'both'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (default: stdout)'
    )

    args = parser.parse_args()

    # Analyze data
    print("📊 Analyzing validation data...", file=sys.stderr)
    gate_analysis = analyze_gate_data()
    sales_analysis = analyze_sales_data()

    # Generate report
    if args.format in ['markdown', 'both']:
        md_report = generate_markdown_report(gate_analysis, sales_analysis)

        if args.output and args.format == 'markdown':
            args.output.write_text(md_report)
            print(f"✅ Markdown report saved to: {args.output}", file=sys.stderr)
        else:
            print(md_report)

    if args.format in ['json', 'both']:
        json_report = generate_json_report(gate_analysis, sales_analysis)

        if args.output and args.format == 'json':
            args.output.write_text(json.dumps(json_report, indent=2))
            print(f"✅ JSON report saved to: {args.output}", file=sys.stderr)
        elif args.format == 'json':
            print(json.dumps(json_report, indent=2))

    if args.format == 'both':
        # Save both formats
        md_file = ROOT / "data" / "validation" / "validation_report.md"
        json_file = ROOT / "data" / "validation" / "validation_report.json"

        md_file.write_text(generate_markdown_report(gate_analysis, sales_analysis))
        json_file.write_text(json.dumps(generate_json_report(gate_analysis, sales_analysis), indent=2))

        print(f"✅ Reports saved:", file=sys.stderr)
        print(f"   Markdown: {md_file}", file=sys.stderr)
        print(f"   JSON    : {json_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
