"""
================================================================================
FINANCIAL IMPACT CALCULATION SERVICE
================================================================================

DESCRIPTION:
    Core financial calculation engine that transforms security vulnerabilities
    into quantifiable business risks. Implements industry-standard formulas for
    downtime costs, breach impacts, and return on security investment (ROSI).

KEY FEATURES:
    1. Direct Loss Calculation: RTO-based downtime cost estimation
    2. Total Impact Assessment: 4%/96% split for long-term reputation damage
    3. ROSI Analysis: Investment justification for security fixes
    4. Severity Weighting: Numerical ranking for prioritization

FORMULAS:
    - Direct Loss = Hourly Downtime Cost × RTO (Recovery Time Objective)
    - Secondary Loss = $1,000,000 for PCI/PII data breaches
    - Total Impact = Direct Loss / 0.04 (accounts for 96% indirect costs)
    - ROSI = (Risk Reduction / Fix Cost) × 100

AUTHOR: ABhiram PS
DATE: 2026-01-15
================================================================================
"""

from typing import Dict, Any, Optional
from enum import Enum


class SeverityLevel(Enum):
    """Severity levels with numerical weights for prioritization"""
    CRITICAL = 10
    HIGH = 7
    MEDIUM = 4
    LOW = 2
    INFO = 1
    UNKNOWN = 0


def get_severity_weight(severity: str) -> int:
    """
    Convert severity string to numerical weight for prioritization.
    
    Args:
        severity: Severity level as string (case-insensitive)
        
    Returns:
        Numerical weight (0-10)
    """
    severity_normalized = severity.upper().strip()
    
    if "CRITICAL" in severity_normalized:
        return SeverityLevel.CRITICAL.value
    elif "HIGH" in severity_normalized:
        return SeverityLevel.HIGH.value
    elif "MEDIUM" in severity_normalized or "MODERATE" in severity_normalized:
        return SeverityLevel.MEDIUM.value
    elif "LOW" in severity_normalized or "WARNING" in severity_normalized:
        return SeverityLevel.LOW.value
    elif "INFO" in severity_normalized:
        return SeverityLevel.INFO.value
    else:
        return SeverityLevel.UNKNOWN.value


def calculate_direct_loss(hourly_cost: float, rto_hours: float) -> float:
    """
    Calculate direct financial loss from system downtime.
    
    Formula: Direct Loss = Hourly Downtime Cost × RTO
    
    Args:
        hourly_cost: Cost per hour of system downtime (in dollars)
        rto_hours: Recovery Time Objective in hours
        
    Returns:
        Direct financial loss in dollars
        
    Example:
        >>> calculate_direct_loss(10000, 4)
        40000.0
    """
    return hourly_cost * rto_hours


def calculate_total_impact(
    direct_loss: float, 
    has_pii_breach: bool = False,
    secondary_loss: float = 1000000.0
) -> Dict[str, float]:
    """
    Calculate total financial impact including indirect costs.
    
    The 4%/96% split accounts for:
    - 4%: Direct costs (downtime, immediate response)
    - 96%: Indirect costs (reputation damage, customer churn, legal fees)
    
    Args:
        direct_loss: Direct financial loss from downtime
        has_pii_breach: Whether vulnerability involves PCI/PII data
        secondary_loss: Fixed cost for data breach (default: $1M)
        
    Returns:
        Dictionary with breakdown:
        - direct_loss: Immediate costs
        - indirect_loss: Long-term reputation/churn costs
        - breach_penalty: Additional cost if PII/PCI involved
        - total_impact: Sum of all costs
        
    Example:
        >>> calculate_total_impact(40000, has_pii_breach=True)
        {
            'direct_loss': 40000.0,
            'indirect_loss': 960000.0,
            'breach_penalty': 1000000.0,
            'total_impact': 2000000.0
        }
    """
    # Calculate indirect costs (96% of total long-term impact)
    # If direct is 4%, then total = direct / 0.04
    total_from_downtime = direct_loss / 0.04
    indirect_loss = total_from_downtime - direct_loss
    
    # Add breach penalty if PII/PCI data is involved
    breach_penalty = secondary_loss if has_pii_breach else 0.0
    
    total_impact = direct_loss + indirect_loss + breach_penalty
    
    return {
        "direct_loss": round(direct_loss, 2),
        "indirect_loss": round(indirect_loss, 2),
        "breach_penalty": round(breach_penalty, 2),
        "total_impact": round(total_impact, 2)
    }


def calculate_rosi(total_risk: float, fix_cost: float = 5000.0) -> Dict[str, Any]:
    """
    Calculate Return on Security Investment (ROSI).
    
    ROSI helps justify security spending by showing the financial benefit
    of fixing a vulnerability relative to its cost.
    
    Formula: ROSI = ((Risk Reduction - Fix Cost) / Fix Cost) × 100
    
    Args:
        total_risk: Total financial exposure from vulnerability
        fix_cost: Estimated cost to fix the vulnerability (default: $5,000)
        
    Returns:
        Dictionary with:
        - fix_cost: Cost to remediate
        - risk_reduction: Financial risk eliminated
        - net_benefit: Risk reduction minus fix cost
        - rosi_percentage: Return on investment as percentage
        - recommendation: Investment recommendation
        
    Example:
        >>> calculate_rosi(2000000, 5000)
        {
            'fix_cost': 5000.0,
            'risk_reduction': 2000000.0,
            'net_benefit': 1995000.0,
            'rosi_percentage': 39900.0,
            'recommendation': 'CRITICAL INVESTMENT - Immediate action required'
        }
    """
    risk_reduction = total_risk
    net_benefit = risk_reduction - fix_cost
    rosi_percentage = (net_benefit / fix_cost) * 100 if fix_cost > 0 else 0
    
    # Generate recommendation based on ROSI
    if rosi_percentage > 10000:
        recommendation = "CRITICAL INVESTMENT - Immediate action required"
    elif rosi_percentage > 1000:
        recommendation = "HIGH PRIORITY - Strong financial justification"
    elif rosi_percentage > 100:
        recommendation = "RECOMMENDED - Positive return on investment"
    elif rosi_percentage > 0:
        recommendation = "CONSIDER - Marginal positive return"
    else:
        recommendation = "LOW PRIORITY - Cost exceeds immediate risk"
    
    return {
        "fix_cost": round(fix_cost, 2),
        "risk_reduction": round(risk_reduction, 2),
        "net_benefit": round(net_benefit, 2),
        "rosi_percentage": round(rosi_percentage, 2),
        "recommendation": recommendation
    }


def estimate_rto_from_severity(severity: str, asset_criticality: str = "medium") -> float:
    """
    Estimate Recovery Time Objective (RTO) based on vulnerability severity
    and asset criticality when actual RTO data is not available.
    
    Args:
        severity: Vulnerability severity level
        asset_criticality: Asset importance (critical/high/medium/low)
        
    Returns:
        Estimated RTO in hours
    """
    # Base RTO estimates by severity
    base_rto = {
        "CRITICAL": 24,  # 1 day
        "HIGH": 72,      # 3 days
        "MEDIUM": 168,   # 1 week
        "LOW": 720       # 1 month
    }
    
    severity_weight = get_severity_weight(severity)
    
    # Adjust based on asset criticality
    criticality_multiplier = {
        "critical": 0.5,  # Faster recovery needed
        "high": 0.75,
        "medium": 1.0,
        "low": 1.5
    }
    
    # Get base RTO
    if severity_weight >= SeverityLevel.CRITICAL.value:
        rto = base_rto["CRITICAL"]
    elif severity_weight >= SeverityLevel.HIGH.value:
        rto = base_rto["HIGH"]
    elif severity_weight >= SeverityLevel.MEDIUM.value:
        rto = base_rto["MEDIUM"]
    else:
        rto = base_rto["LOW"]
    
    # Apply criticality multiplier
    multiplier = criticality_multiplier.get(asset_criticality.lower(), 1.0)
    
    return rto * multiplier


def estimate_hourly_cost(asset_type: str = "general") -> float:
    """
    Estimate hourly downtime cost based on asset type.
    
    These are conservative industry averages. Organizations should
    provide actual values in their financial documents.
    
    Args:
        asset_type: Type of asset (e.g., 'payment', 'api', 'database', 'general')
        
    Returns:
        Estimated hourly cost in dollars
    """
    # Industry average estimates
    cost_estimates = {
        "payment": 50000,      # Payment processing systems
        "ecommerce": 40000,    # E-commerce platforms
        "api": 25000,          # Critical API services
        "database": 30000,     # Database systems
        "authentication": 35000,  # Auth/login systems
        "general": 10000       # General applications
    }
    
    return cost_estimates.get(asset_type.lower(), cost_estimates["general"])
