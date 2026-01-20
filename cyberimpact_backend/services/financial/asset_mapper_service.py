"""
================================================================================
AI-POWERED ASSET MAPPING SERVICE
================================================================================

DESCRIPTION:
    Intelligent asset mapping service that uses AI to understand context and
    match vulnerabilities to business assets, even when naming conventions vary.
    
    Instead of relying on exact string matching, this service uses Google's
    Gemini AI to understand the semantic relationship between vulnerabilities
    and business assets.

KEY FEATURES:
    1. Contextual Understanding: AI analyzes vulnerability descriptions and
       asset information to find meaningful connections
    2. Flexible Matching: Works regardless of naming conventions
    3. Business Context Enrichment: Adds business impact context to technical findings
    4. Confidence Scoring: Provides confidence levels for asset mappings

WORKFLOW:
    1. Fetch asset inventory from MongoDB
    2. Extract financial parameters from financial documents
    3. Use AI to match vulnerabilities to assets based on context
    4. Enrich vulnerabilities with business metadata

AUTHOR: ABhiram PS
DATE: 2026-01-15
================================================================================
"""

from typing import Dict, Any, List, Optional
import json
from services.db.db_service import db_service
from services.ai_service import perform_ai_check
import os


def fetch_user_assets(uploader_id: str) -> List[Dict[str, Any]]:
    """
    Fetch asset inventory from MongoDB for a specific user.
    
    Args:
        uploader_id: Firebase UID of the user
        
    Returns:
        List of asset inventory documents
    """
    try:
        assets = db_service.list_asset_inventories_by_user(uploader_id, limit=100)
        return assets
    except Exception as e:
        print(f"⚠️ Error fetching assets: {e}")
        return []


def fetch_financial_parameters(uploader_id: str) -> Dict[str, Any]:
    """
    Fetch financial parameters from financial documents.
    
    Args:
        uploader_id: Firebase UID of the user
        
    Returns:
        Dictionary with financial parameters (RTO, hourly costs, etc.)
    """
    try:
        financial_docs = db_service.list_financial_documents_by_user(uploader_id, limit=10)
        
        # Extract financial parameters from documents
        # This is a simplified version - you may want to parse the extracted_text
        # for specific financial metrics
        parameters = {
            "default_hourly_cost": 10000,  # Default fallback
            "default_rto_hours": 24,
            "has_pii_data": False,
            "documents": financial_docs
        }
        
        return parameters
    except Exception as e:
        print(f"⚠️ Error fetching financial parameters: {e}")
        return {
            "default_hourly_cost": 10000,
            "default_rto_hours": 24,
            "has_pii_data": False,
            "documents": []
        }


def map_vulnerability_to_asset_with_ai(
    vulnerability: Dict[str, Any],
    assets: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Use AI to intelligently map a vulnerability to the most relevant business asset.
    
    This function uses contextual understanding rather than exact string matching,
    making it robust to varying naming conventions.
    
    Args:
        vulnerability: Vulnerability data with file, package, description, etc.
        assets: List of asset inventory documents from database
        
    Returns:
        Best matching asset with confidence score, or None if no good match
    """
    if not assets:
        return None
    
    # Prepare vulnerability context for AI
    vuln_context = {
        "file": vulnerability.get("file", ""),
        "package": vulnerability.get("package", ""),
        "message": vulnerability.get("message", ""),
        "description": vulnerability.get("description", ""),
        "issue": vulnerability.get("issue", ""),
        "rule": vulnerability.get("rule", ""),
        "severity": vulnerability.get("severity", "")
    }
    
    # Prepare asset context for AI
    asset_summaries = []
    for idx, asset in enumerate(assets):
        asset_data = asset.get("data", {})
        
        # Extract key information from asset
        asset_summary = {
            "index": idx,
            "filename": asset.get("filename", ""),
            "data_preview": str(asset_data)[:500]  # First 500 chars
        }
        asset_summaries.append(asset_summary)
    
    # Create AI prompt for contextual matching
    prompt = f"""You are a cybersecurity analyst mapping technical vulnerabilities to business assets.

VULNERABILITY DETAILS:
{json.dumps(vuln_context, indent=2)}

AVAILABLE BUSINESS ASSETS:
{json.dumps(asset_summaries, indent=2)}

TASK:
Analyze the vulnerability and determine which business asset (if any) is most likely affected.
Consider:
- File paths and their relationship to asset names/purposes
- Package names and their business context
- Vulnerability descriptions and asset functionality
- Technical components mentioned in the vulnerability

Respond with ONLY a JSON object in this exact format:
{{
    "matched": true/false,
    "asset_index": <index of matched asset or -1>,
    "confidence": <0-100>,
    "reasoning": "<brief explanation of why this asset matches>",
    "business_impact": "<1-2 sentence explanation of business impact>"
}}

If no asset is a good match, set matched to false and asset_index to -1.
"""
    
    try:
        # Call AI service
        ai_response = perform_ai_check(prompt)
        
        # Parse AI response
        # Try to extract JSON from response
        response_text = ai_response.strip()
        
        # Find JSON in response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # Validate result
            if result.get("matched") and result.get("asset_index", -1) >= 0:
                asset_idx = result["asset_index"]
                if 0 <= asset_idx < len(assets):
                    matched_asset = assets[asset_idx].copy()
                    matched_asset["mapping_confidence"] = result.get("confidence", 0)
                    matched_asset["mapping_reasoning"] = result.get("reasoning", "")
                    matched_asset["business_impact"] = result.get("business_impact", "")
                    return matched_asset
        
        return None
        
    except Exception as e:
        print(f"⚠️ AI mapping error: {e}")
        # Fallback to simple keyword matching
        return map_vulnerability_to_asset_simple(vulnerability, assets)


def map_vulnerability_to_asset_simple(
    vulnerability: Dict[str, Any],
    assets: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Fallback simple keyword-based matching when AI is unavailable.
    
    Args:
        vulnerability: Vulnerability data
        assets: List of asset inventory documents
        
    Returns:
        Best matching asset or None
    """
    if not assets:
        return None
    
    # Extract searchable text from vulnerability
    vuln_text = " ".join([
        str(vulnerability.get("file", "")),
        str(vulnerability.get("package", "")),
        str(vulnerability.get("message", "")),
        str(vulnerability.get("description", "")),
        str(vulnerability.get("issue", "")),
    ]).lower()
    
    best_match = None
    best_score = 0
    
    for asset in assets:
        score = 0
        asset_data = asset.get("data", {})
        asset_filename = asset.get("filename", "").lower()
        
        # Simple keyword matching
        # Check if asset filename appears in vulnerability
        if asset_filename and asset_filename.replace(".xlsx", "") in vuln_text:
            score += 5
        
        # Check for common keywords
        keywords = ["payment", "api", "auth", "database", "user", "admin"]
        for keyword in keywords:
            if keyword in vuln_text and keyword in str(asset_data).lower():
                score += 2
        
        if score > best_score:
            best_score = score
            best_match = asset.copy()
            best_match["mapping_confidence"] = min(score * 10, 70)  # Max 70% for simple matching
            best_match["mapping_reasoning"] = "Keyword-based matching (AI unavailable)"
    
    return best_match if best_score > 0 else None


def enrich_vulnerability_with_asset(
    vulnerability: Dict[str, Any],
    asset: Optional[Dict[str, Any]],
    financial_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enrich vulnerability with business context from matched asset.
    
    Args:
        vulnerability: Original vulnerability data
        asset: Matched asset (or None)
        financial_params: Financial parameters from user's documents
        
    Returns:
        Enriched vulnerability with business metadata
    """
    enriched = vulnerability.copy()
    
    if asset:
        enriched["matched_asset"] = {
            "id": asset.get("_id"),
            "filename": asset.get("filename"),
            "confidence": asset.get("mapping_confidence", 0),
            "reasoning": asset.get("mapping_reasoning", ""),
            "business_impact": asset.get("business_impact", ""),
            "data": asset.get("data", {})
        }
        
        # Extract asset-specific financial parameters if available
        asset_data = asset.get("data", {})
        
        # Try to find RTO and hourly cost in asset data
        # This assumes asset inventory might have columns like "RTO", "Hourly_Cost", etc.
        enriched["financial_context"] = {
            "hourly_cost": financial_params.get("default_hourly_cost", 10000),
            "rto_hours": financial_params.get("default_rto_hours", 24),
            "has_pii_data": financial_params.get("has_pii_data", False),
            "asset_criticality": "medium"  # Default, could be extracted from asset data
        }
    else:
        enriched["matched_asset"] = None
        enriched["financial_context"] = {
            "hourly_cost": financial_params.get("default_hourly_cost", 10000),
            "rto_hours": financial_params.get("default_rto_hours", 24),
            "has_pii_data": False,
            "asset_criticality": "low"
        }
    
    return enriched


def map_all_vulnerabilities(
    vulnerabilities: List[Dict[str, Any]],
    uploader_id: str
) -> List[Dict[str, Any]]:
    """
    Map all vulnerabilities to business assets using AI-powered contextual understanding.
    
    Args:
        vulnerabilities: List of vulnerabilities from scan results
        uploader_id: Firebase UID to fetch user's assets
        
    Returns:
        List of enriched vulnerabilities with asset mappings
    """
    # Fetch user's assets and financial parameters
    assets = fetch_user_assets(uploader_id)
    financial_params = fetch_financial_parameters(uploader_id)
    
    print(f"📊 Found {len(assets)} assets for user {uploader_id}")
    
    enriched_vulnerabilities = []
    
    for vuln in vulnerabilities:
        # Use AI to map vulnerability to asset
        matched_asset = map_vulnerability_to_asset_with_ai(vuln, assets)
        
        # Enrich vulnerability with asset and financial context
        enriched_vuln = enrich_vulnerability_with_asset(vuln, matched_asset, financial_params)
        enriched_vulnerabilities.append(enriched_vuln)
    
    # Log mapping statistics
    mapped_count = sum(1 for v in enriched_vulnerabilities if v.get("matched_asset"))
    print(f"✅ Mapped {mapped_count}/{len(vulnerabilities)} vulnerabilities to assets")
    
    return enriched_vulnerabilities
