"""
================================================================================
FINANCIAL IMPACT ANALYSIS PIPELINE
================================================================================

DESCRIPTION:
    Main orchestrator for the financial impact analysis pipeline. Coordinates
    the entire workflow from vulnerability scanning to financial risk assessment.

WORKFLOW:
    1. Receive scan results from scanner service
    2. Extract and flatten all vulnerabilities
    3. Sort vulnerabilities by severity
    4. Fetch user's asset inventory from database
    5. Use AI to map vulnerabilities to business assets
    6. Calculate financial impact for each vulnerability
    7. Generate Financial Risk Tickets
    8. Return comprehensive financial analysis

KEY FEATURES:
    - Automated end-to-end processing
    - AI-powered asset correlation
    - Executive-ready financial reports
    - Prioritized risk tickets by ROSI

AUTHOR: ABhiram PS
DATE: 2026-01-15
================================================================================
"""

from typing import Dict, Any, List
from .asset_mapper_service import map_all_vulnerabilities
from .risk_ticket_generator import generate_all_risk_tickets, format_ticket_as_markdown
from .financial_impact_service import get_severity_weight


def extract_all_vulnerabilities(scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract and flatten all vulnerabilities from scan results.
    
    Args:
        scan_results: Dictionary of scan results from multiple tools
        
    Returns:
        Flattened list of all vulnerabilities with tool metadata
    """
    all_vulnerabilities = []
    
    for tool_name, result in scan_results.items():
        essential_findings = result.get("essential", [])
        
        if essential_findings and isinstance(essential_findings, list):
            for finding in essential_findings:
                # Add tool metadata
                vuln = finding.copy()
                vuln["source_tool"] = tool_name
                all_vulnerabilities.append(vuln)
    
    return all_vulnerabilities


def sort_vulnerabilities_by_severity(vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort vulnerabilities by severity (Critical -> High -> Medium -> Low).
    
    Args:
        vulnerabilities: List of vulnerabilities
        
    Returns:
        Sorted list (highest severity first)
    """
    return sorted(
        vulnerabilities,
        key=lambda v: get_severity_weight(v.get("severity", "")),
        reverse=True
    )


def calculate_summary_statistics(risk_tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics for executive dashboard.
    
    Args:
        risk_tickets: List of generated risk tickets
        
    Returns:
        Summary statistics dictionary
    """
    if not risk_tickets:
        return {
            "total_vulnerabilities": 0,
            "total_financial_exposure": 0,
            "severity_breakdown": {},
            "total_fix_cost": 0,
            "total_rosi": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0
        }
    
    total_exposure = sum(t["financial_exposure"]["total"] for t in risk_tickets)
    total_fix_cost = sum(t["rosi"]["fix_cost"] for t in risk_tickets)
    
    # Calculate average ROSI
    avg_rosi = sum(t["rosi"]["rosi_percentage"] for t in risk_tickets) / len(risk_tickets)
    
    # Severity breakdown
    severity_counts = {}
    for ticket in risk_tickets:
        severity = ticket["severity"].upper()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    return {
        "total_vulnerabilities": len(risk_tickets),
        "total_financial_exposure": round(total_exposure, 2),
        "severity_breakdown": severity_counts,
        "total_fix_cost": round(total_fix_cost, 2),
        "average_rosi": round(avg_rosi, 2),
        "net_benefit": round(total_exposure - total_fix_cost, 2),
        "critical_count": severity_counts.get("CRITICAL", 0),
        "high_count": severity_counts.get("HIGH", 0),
        "medium_count": severity_counts.get("MEDIUM", 0),
        "low_count": severity_counts.get("LOW", 0)
    }


def process_scan_results(
    scan_results: Dict[str, Any],
    uploader_id: str
) -> Dict[str, Any]:
    """
    Main pipeline entry point. Process scan results and generate financial analysis.
    
    Args:
        scan_results: Raw scan results from scanner service
        uploader_id: Firebase UID of the user (for fetching assets)
        
    Returns:
        Complete financial analysis with risk tickets and summary
    """
    print("\n" + "="*80)
    print("💰 FINANCIAL IMPACT ANALYSIS PIPELINE")
    print("="*80)
    
    # Step 1: Extract all vulnerabilities
    print("\n📋 Step 1: Extracting vulnerabilities from scan results...")
    all_vulnerabilities = extract_all_vulnerabilities(scan_results)
    print(f"   Found {len(all_vulnerabilities)} total vulnerabilities")
    
    if not all_vulnerabilities:
        print("   ✅ No vulnerabilities found - clean scan!")
        return {
            "summary": calculate_summary_statistics([]),
            "risk_tickets": [],
            "vulnerabilities_processed": 0,
            "assets_mapped": 0
        }
    
    # Step 2: Sort by severity
    print("\n🔢 Step 2: Sorting vulnerabilities by severity...")
    sorted_vulnerabilities = sort_vulnerabilities_by_severity(all_vulnerabilities)
    severity_distribution = {}
    for v in sorted_vulnerabilities:
        sev = v.get("severity", "UNKNOWN").upper()
        severity_distribution[sev] = severity_distribution.get(sev, 0) + 1
    print(f"   Severity distribution: {severity_distribution}")
    
    # Step 3: Map vulnerabilities to business assets using AI
    print(f"\n🤖 Step 3: Mapping vulnerabilities to business assets (User: {uploader_id})...")
    enriched_vulnerabilities = map_all_vulnerabilities(sorted_vulnerabilities, uploader_id)
    
    # Step 4: Generate Financial Risk Tickets
    print("\n🎫 Step 4: Generating Financial Risk Tickets...")
    risk_tickets = generate_all_risk_tickets(enriched_vulnerabilities)
    print(f"   Generated {len(risk_tickets)} risk tickets")
    
    # Step 5: Calculate summary statistics
    print("\n📊 Step 5: Calculating financial summary...")
    summary = calculate_summary_statistics(risk_tickets)
    print(f"   Total Financial Exposure: ${summary['total_financial_exposure']:,.2f}")
    print(f"   Total Fix Cost: ${summary['total_fix_cost']:,.2f}")
    print(f"   Net Benefit: ${summary['net_benefit']:,.2f}")
    print(f"   Average ROSI: {summary['average_rosi']:,.0f}%")
    
    # Count mapped assets
    assets_mapped = sum(1 for v in enriched_vulnerabilities if v.get("matched_asset"))
    
    print("\n" + "="*80)
    print("✅ FINANCIAL ANALYSIS COMPLETE")
    print("="*80 + "\n")
    
    return {
        "summary": summary,
        "risk_tickets": risk_tickets,
        "vulnerabilities_processed": len(all_vulnerabilities),
        "assets_mapped": assets_mapped,
        "enriched_vulnerabilities": enriched_vulnerabilities
    }


def generate_financial_report_markdown(financial_analysis: Dict[str, Any]) -> str:
    """
    Generate markdown report section for financial analysis.
    
    Args:
        financial_analysis: Output from process_scan_results
        
    Returns:
        Markdown formatted financial report
    """
    summary = financial_analysis["summary"]
    risk_tickets = financial_analysis["risk_tickets"]
    
    md = f"""
# 💰 FINANCIAL IMPACT ANALYSIS

## Executive Dashboard

**Total Vulnerabilities:** {summary['total_vulnerabilities']}  
**Total Financial Exposure:** ${summary['total_financial_exposure']:,.2f}  
**Estimated Fix Cost:** ${summary['total_fix_cost']:,.2f}  
**Net Benefit of Remediation:** ${summary['net_benefit']:,.2f}  
**Average ROSI:** {summary['average_rosi']:,.0f}%

### Severity Distribution

- 🔴 **Critical:** {summary['critical_count']}
- 🟠 **High:** {summary['high_count']}
- 🟡 **Medium:** {summary['medium_count']}
- 🟢 **Low:** {summary['low_count']}

---

## 🎫 Financial Risk Tickets

The following tickets represent individual security vulnerabilities translated into business risks with financial quantification.

"""
    
    # Add all risk tickets
    for ticket in risk_tickets:
        md += format_ticket_as_markdown(ticket)
        md += "\n---\n\n"
    
    # Add investment recommendations
    md += """
## 💡 Investment Recommendations

Based on the ROSI analysis, we recommend prioritizing remediation in the following order:

"""
    
    # Sort tickets by ROSI percentage
    sorted_by_rosi = sorted(risk_tickets, key=lambda t: t['rosi']['rosi_percentage'], reverse=True)
    
    for idx, ticket in enumerate(sorted_by_rosi[:5], 1):  # Top 5
        md += f"{idx}. **Ticket #{ticket['ticket_number']:03d}** - {ticket['asset_name']} "
        md += f"(ROSI: {ticket['rosi']['rosi_percentage']:,.0f}%)\n"
    
    md += "\n"
    
    return md
