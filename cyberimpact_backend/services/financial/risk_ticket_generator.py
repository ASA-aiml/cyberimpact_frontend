"""
================================================================================
FINANCIAL RISK TICKET GENERATOR
================================================================================

DESCRIPTION:
    Generates executive-friendly "Financial Risk Tickets" that transform
    technical vulnerability findings into business-focused risk assessments.
    
    Designed for C-level executives who need to understand security risks
    in financial terms without technical jargon.

KEY FEATURES:
    1. Business Language: Translates technical vulnerabilities to business impact
    2. Financial Quantification: Dollar amounts for each risk
    3. Executive Summaries: 2-sentence CEO-friendly explanations
    4. ROSI Analysis: Investment justification for each fix
    5. Professional Formatting: Clean, scannable ticket format

TICKET STRUCTURE:
    - Header with ticket number and severity
    - Business Impact section
    - Financial Exposure (dollar amount)
    - Executive Summary (non-technical)
    - ROSI calculation
    - Technical details (simplified)

AUTHOR: ABhiram PS
DATE: 2026-01-15
================================================================================
"""

from typing import Dict, Any, List, Optional
from .financial_impact_service import (
    calculate_direct_loss,
    calculate_total_impact,
    calculate_rosi,
    get_severity_weight,
    estimate_rto_from_severity,
    estimate_hourly_cost
)


def translate_technical_to_business(vulnerability: Dict[str, Any]) -> str:
    """
    Translate technical vulnerability description to business-friendly language.
    
    Args:
        vulnerability: Vulnerability data with technical details
        
    Returns:
        Business-friendly explanation
    """
    # Common technical terms and their business translations
    translations = {
        "sql injection": "database manipulation that could expose customer data",
        "xss": "malicious code injection that could compromise user sessions",
        "cross-site scripting": "malicious code injection that could compromise user sessions",
        "buffer overflow": "system instability that could cause crashes or data theft",
        "authentication bypass": "unauthorized access to protected systems",
        "csrf": "unauthorized actions performed on behalf of legitimate users",
        "path traversal": "unauthorized file access that could expose sensitive data",
        "command injection": "system takeover that could compromise all data",
        "insecure deserialization": "code execution that could lead to system compromise",
        "sensitive data exposure": "unprotected customer or business information",
        "broken access control": "unauthorized access to restricted features or data",
        "security misconfiguration": "improper settings that create security gaps",
        "vulnerable dependency": "outdated software component with known security flaws",
        "hardcoded credentials": "embedded passwords that could grant unauthorized access",
        "weak cryptography": "inadequate data protection that could be easily broken"
    }
    
    # Get technical description
    tech_desc = (
        vulnerability.get("message", "") or 
        vulnerability.get("description", "") or 
        vulnerability.get("issue", "") or
        vulnerability.get("vulnerability", "")
    ).lower()
    
    # Find matching translation
    for tech_term, business_term in translations.items():
        if tech_term in tech_desc:
            return business_term
    
    # Default fallback
    return "security vulnerability that could compromise system integrity or data confidentiality"


def generate_executive_summary(
    vulnerability: Dict[str, Any],
    asset_name: str,
    financial_exposure: float
) -> str:
    """
    Generate a 2-sentence executive summary for C-level audience.
    
    Args:
        vulnerability: Vulnerability data
        asset_name: Name of affected business asset
        financial_exposure: Total financial risk in dollars
        
    Returns:
        2-sentence executive summary
    """
    business_impact = translate_technical_to_business(vulnerability)
    severity = vulnerability.get("severity", "unknown").upper()
    
    # Format financial exposure
    if financial_exposure >= 1000000:
        exposure_str = f"${financial_exposure/1000000:.1f}M"
    elif financial_exposure >= 1000:
        exposure_str = f"${financial_exposure/1000:.0f}K"
    else:
        exposure_str = f"${financial_exposure:.0f}"
    
    summary = (
        f"A {severity.lower()} security vulnerability has been identified in {asset_name}, "
        f"exposing the organization to {business_impact}. "
        f"The estimated financial impact is {exposure_str}, including potential downtime costs, "
        f"reputation damage, and regulatory penalties."
    )
    
    return summary


def generate_business_impact_statement(
    vulnerability: Dict[str, Any],
    asset: Optional[Dict[str, Any]]
) -> str:
    """
    Generate detailed business impact statement.
    
    Args:
        vulnerability: Vulnerability data
        asset: Matched business asset
        
    Returns:
        Business impact explanation
    """
    if asset and asset.get("business_impact"):
        # Use AI-generated business impact if available
        return asset["business_impact"]
    
    # Generate generic business impact
    asset_name = "this system"
    if asset:
        asset_name = asset.get("filename", "").replace(".xlsx", "").replace("_", " ").title()
    
    business_impact = translate_technical_to_business(vulnerability)
    severity = vulnerability.get("severity", "unknown").upper()
    
    impact_statement = (
        f"**{asset_name}** is a critical business component that, if compromised, could result in "
        f"{business_impact}. This {severity.lower()}-severity vulnerability creates a direct pathway "
        f"for attackers to exploit this weakness, potentially leading to:\n\n"
        f"- **Service Disruption**: System downtime affecting business operations\n"
        f"- **Data Breach**: Unauthorized access to sensitive customer or business data\n"
        f"- **Reputation Damage**: Loss of customer trust and brand value\n"
        f"- **Regulatory Penalties**: Potential fines for compliance violations\n"
        f"- **Competitive Disadvantage**: Loss of market position due to security incidents"
    )
    
    return impact_statement


def generate_risk_ticket(
    ticket_number: int,
    vulnerability: Dict[str, Any],
    enriched_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a complete Financial Risk Ticket.
    
    Args:
        ticket_number: Sequential ticket number
        vulnerability: Original vulnerability data
        enriched_data: Enriched data with asset mapping and financial context
        
    Returns:
        Complete risk ticket as dictionary
    """
    # Extract data
    # The 'matched_asset' from enriched_data contains the full asset details
    # The 'vulnerability' dict might also contain a 'matched_asset' key if it was added during enrichment
    matched_asset_from_enriched = enriched_data.get("matched_asset")
    financial_context = enriched_data.get("financial_context", {})
    severity = vulnerability.get("severity", "UNKNOWN")
    
    # Extract asset information, prioritizing 'asset_name' if available in the matched asset
    # The 'matched_asset' in 'vulnerability' is the same as 'matched_asset_from_enriched'
    # but we use 'vulnerability.get("matched_asset")' as per instruction for consistency
    matched_asset = vulnerability.get("matched_asset")
    if matched_asset:
        # Use extracted asset name from the matched row, fallback to filename
        asset_name = matched_asset.get("asset_name", matched_asset.get("filename", "Unknown Asset"))
        # Clean up the name if it's still a filename-like string
        if ".xlsx" in asset_name or "_" in asset_name:
            asset_name = asset_name.replace(".xlsx", "").replace("_", " ").title()
        confidence = matched_asset.get("confidence", 0)
    else:
        asset_name = "Unidentified System Component"
        confidence = 0
    
    # Calculate financial impact
    hourly_cost = financial_context.get("hourly_cost", 10000)
    rto_hours = financial_context.get("rto_hours", 24)
    has_pii = financial_context.get("has_pii_data", False)
    
    # Use severity-based RTO if not provided
    if rto_hours == 24:  # Default value
        asset_criticality = financial_context.get("asset_criticality", "medium")
        rto_hours = estimate_rto_from_severity(severity, asset_criticality)
    
    direct_loss = calculate_direct_loss(hourly_cost, rto_hours)
    impact_breakdown = calculate_total_impact(direct_loss, has_pii)
    total_exposure = impact_breakdown["total_impact"]
    
    # Calculate ROSI
    rosi_data = calculate_rosi(total_exposure, fix_cost=5000)
    
    # Generate summaries
    executive_summary = generate_executive_summary(vulnerability, asset_name, total_exposure)
    business_impact = generate_business_impact_statement(vulnerability, matched_asset)
    
    # Get severity emoji
    severity_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }
    emoji = severity_emoji.get(severity.upper(), "⚪")
    
    # Build ticket
    ticket = {
        "ticket_number": ticket_number,
        "severity": severity,
        "severity_emoji": emoji,
        "severity_weight": get_severity_weight(severity),
        "asset_name": asset_name,
        "asset_confidence": confidence,
        "business_impact": business_impact,
        "financial_exposure": {
            "total": total_exposure,
            "direct_loss": impact_breakdown["direct_loss"],
            "indirect_loss": impact_breakdown["indirect_loss"],
            "breach_penalty": impact_breakdown["breach_penalty"]
        },
        "executive_summary": executive_summary,
        "rosi": rosi_data,
        "technical_details": {
            "file": vulnerability.get("file", "N/A"),
            "line": vulnerability.get("line", "N/A"),
            "package": vulnerability.get("package", "N/A"),
            "rule_id": vulnerability.get("rule_id", "") or vulnerability.get("test_id", ""),
            "original_message": (
                vulnerability.get("message", "") or 
                vulnerability.get("issue", "") or 
                vulnerability.get("description", "")
            )
        },
        "matched_asset_details": matched_asset if matched_asset else None
    }
    
    return ticket


def format_ticket_as_markdown(ticket: Dict[str, Any]) -> str:
    """
    Format a risk ticket as markdown for reports.
    
    Args:
        ticket: Risk ticket dictionary
        
    Returns:
        Formatted markdown string
    """
    md = f"""
## {ticket['severity_emoji']} FINANCIAL RISK TICKET #{ticket['ticket_number']:03d}

**Severity:** {ticket['severity']} | **Asset:** {ticket['asset_name']}

---

### 🎯 BUSINESS IMPACT

{ticket['business_impact']}

---

### 💰 FINANCIAL EXPOSURE

**Total Potential Loss:** ${ticket['financial_exposure']['total']:,.2f}

**Breakdown:**
- Direct Costs (Downtime): ${ticket['financial_exposure']['direct_loss']:,.2f}
- Indirect Costs (Reputation/Churn): ${ticket['financial_exposure']['indirect_loss']:,.2f}
- Data Breach Penalty: ${ticket['financial_exposure']['breach_penalty']:,.2f}

---

### 👔 EXECUTIVE SUMMARY

{ticket['executive_summary']}

---

### 📊 RETURN ON SECURITY INVESTMENT (ROSI)

**Fix Cost:** ${ticket['rosi']['fix_cost']:,.2f}  
**Risk Reduction:** ${ticket['rosi']['risk_reduction']:,.2f}  
**Net Benefit:** ${ticket['rosi']['net_benefit']:,.2f}  
**ROSI:** {ticket['rosi']['rosi_percentage']:,.0f}%

**Recommendation:** {ticket['rosi']['recommendation']}

---

### 🔧 TECHNICAL DETAILS

- **Affected File:** `{ticket['technical_details']['file']}`
- **Line Number:** {ticket['technical_details']['line']}
- **Package:** {ticket['technical_details']['package']}
- **Rule ID:** {ticket['technical_details']['rule_id']}

**Technical Description:**  
{ticket['technical_details']['original_message']}

"""
    
    if ticket.get('matched_asset_details'):
        md += f"""
---

### 📋 ASSET MAPPING

**Confidence:** {ticket['asset_confidence']}%  
**Reasoning:** {ticket['matched_asset_details'].get('reasoning', 'N/A')}

"""
    
    return md


def generate_all_risk_tickets(enriched_vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate risk tickets for all vulnerabilities.
    
    Args:
        enriched_vulnerabilities: List of vulnerabilities enriched with asset mappings
        
    Returns:
        List of risk tickets, sorted by severity and financial impact
    """
    tickets = []
    
    for idx, vuln in enumerate(enriched_vulnerabilities, start=1):
        ticket = generate_risk_ticket(idx, vuln, vuln)
        tickets.append(ticket)
    
    # Sort by severity weight (descending) then by financial exposure (descending)
    tickets.sort(
        key=lambda t: (t['severity_weight'], t['financial_exposure']['total']),
        reverse=True
    )
    
    # Renumber tickets after sorting
    for idx, ticket in enumerate(tickets, start=1):
        ticket['ticket_number'] = idx
    
    return tickets
