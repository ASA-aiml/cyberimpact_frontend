"""
Financial Impact Analysis Services

This module provides financial impact analysis for security vulnerabilities,
including asset mapping, risk calculation, and executive reporting.
"""

from .financial_impact_service import (
    calculate_direct_loss,
    calculate_total_impact,
    calculate_rosi,
    get_severity_weight
)

from .financial_pipeline import process_scan_results

__all__ = [
    'calculate_direct_loss',
    'calculate_total_impact',
    'calculate_rosi',
    'get_severity_weight',
    'process_scan_results'
]
