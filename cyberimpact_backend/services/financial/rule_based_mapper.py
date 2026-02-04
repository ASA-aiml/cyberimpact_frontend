"""
================================================================================
RULE-BASED ASSET MAPPER
================================================================================

DESCRIPTION:
    Fast, deterministic asset mapping using hard-coded rules and keyword matching.
    This is Tier 1 and Tier 2 of the hybrid mapping system.
    
    Tier 1: Hard-coded path rules (instant, 100% accurate)
    Tier 2: Keyword fuzzy matching (fast, flexible)

BENEFITS:
    - Zero AI cost
    - Instant mapping (<1ms)
    - 100% reliable (no rate limits)
    - Easy to configure via JSON

AUTHOR: ABhiram PS
DATE: 2026-02-04
================================================================================
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class RuleBasedMapper:
    """Rule-based asset mapper using configuration file"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the rule-based mapper.
        
        Args:
            config_path: Path to asset_mapping_rules.json
        """
        if config_path is None:
            # Default to config directory
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "config" / "asset_mapping_rules.json"
        
        self.config_path = config_path
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load mapping rules from JSON configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Asset mapping rules not found at {self.config_path}")
            return self._get_default_rules()
        except json.JSONDecodeError as e:
            print(f"⚠️ Error parsing asset mapping rules: {e}")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """Return default rules if config file is missing"""
        return {
            "path_rules": {"rules": {}},
            "keyword_rules": {"rules": {}},
            "tier_config": {
                "use_hard_rules": True,
                "use_keyword_matching": True,
                "use_ai_fallback": True
            }
        }
    
    def map_with_hard_rules(
        self,
        vulnerability: Dict[str, Any],
        assets: List[Dict[str, Any]]
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Tier 1: Map using hard-coded path rules.
        
        Args:
            vulnerability: Vulnerability data with file path
            assets: List of available assets
            
        Returns:
            Tuple of (matched_asset, mapping_metadata) or None
        """
        tier_config = self.rules.get("tier_config", {})
        if not tier_config.get("use_hard_path_rules", tier_config.get("use_hard_rules", True)):
            return None
        
        file_path = vulnerability.get("file", "").lower()
        if not file_path:
            return None
        
        # Parse nested path rules structure
        path_rules_config = self.rules.get("path_rules", {})
        
        # Handle both old flat structure and new nested structure
        if "rules" in path_rules_config:
            # New nested structure: {"CORE_BANKING": {"services/payments": "APP-001"}}
            nested_rules = path_rules_config["rules"]
            
            # Flatten the nested structure
            flat_rules = {}
            for category, mappings in nested_rules.items():
                if isinstance(mappings, dict):
                    flat_rules.update(mappings)
            
            # Check each rule
            for rule_path, asset_id in flat_rules.items():
                if rule_path.lower() in file_path:
                    # Find matching asset by ID
                    matched_asset = self._find_asset_by_id(asset_id, assets)
                    if matched_asset:
                        metadata = {
                            "tier": "hard_rules",
                            "confidence": 100,
                            "match_reason": f"Path rule matched: '{rule_path}' → '{asset_id}'",
                            "rule_used": rule_path,
                            "asset_id": asset_id
                        }
                        return (matched_asset, metadata)
        
        return None
    
    def map_with_keywords(
        self,
        vulnerability: Dict[str, Any],
        assets: List[Dict[str, Any]]
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Tier 2: Map using keyword fuzzy matching.
        
        Args:
            vulnerability: Vulnerability data
            assets: List of available assets
            
        Returns:
            Tuple of (matched_asset, mapping_metadata) or None
        """
        if not self.rules.get("tier_config", {}).get("use_keyword_matching", True):
            return None
        
        # Extract searchable text from vulnerability
        vuln_text = " ".join([
            str(vulnerability.get("file", "")),
            str(vulnerability.get("package", "")),
            str(vulnerability.get("message", "")),
            str(vulnerability.get("description", "")),
        ]).lower()
        
        if not vuln_text.strip():
            return None
        
        keyword_rules_config = self.rules.get("keyword_rules", {})
        
        # Handle both old and new keyword structure
        keyword_mappings = keyword_rules_config.get("mappings", keyword_rules_config.get("rules", {}))
        
        # New structure: {"APP-001": ["payment", "transaction"]}
        # Score each asset by keyword matches
        asset_scores = {}
        matched_keywords = {}
        
        for asset_id, keywords in keyword_mappings.items():
            if isinstance(keywords, list):
                score = 0
                matches = []
                for keyword in keywords:
                    if keyword.lower() in vuln_text:
                        score += 1
                        matches.append(keyword)
                
                if score > 0:
                    asset_scores[asset_id] = score
                    matched_keywords[asset_id] = matches
        
        if not asset_scores:
            return None
        
        # Get best match
        best_asset_id = max(asset_scores, key=asset_scores.get)
        match_count = asset_scores[best_asset_id]
        keywords_found = matched_keywords[best_asset_id]
        
        # Find matching asset by ID
        matched_asset = self._find_asset_by_id(best_asset_id, assets)
        if matched_asset:
            # Calculate confidence based on number of keyword matches
            confidence = min(60 + (match_count * 10), 90)  # 60-90% range
            
            metadata = {
                "tier": "keywords",
                "confidence": confidence,
                "match_reason": f"Keyword matching: {match_count} keyword(s) matched '{best_asset_id}' ({', '.join(keywords_found)})",
                "keywords_matched": match_count,
                "asset_id": best_asset_id
            }
            return (matched_asset, metadata)
        
        return None
    
    
    def _find_asset_by_id(
        self,
        asset_id: str,
        assets: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find asset by asset ID and extract the specific row data.
        
        Args:
            asset_id: Asset ID to search for
            assets: List of available assets
            
        Returns:
            Matched asset with extracted row data, or None
        """
        asset_id_lower = asset_id.lower()
        
        for asset in assets:
            asset_data = asset.get("data", {})
            
            # Handle Excel structure: {"sheets": [{"rows": [[...]]}]}
            if isinstance(asset_data, dict) and "sheets" in asset_data:
                sheets = asset_data.get("sheets", [])
                for sheet in sheets:
                    rows = sheet.get("rows", [])
                    if not rows or len(rows) < 2:  # Need header + at least one data row
                        continue
                    
                    # First row is header
                    header = rows[0]
                    
                    # Find column indices
                    asset_id_col_idx = None
                    asset_name_col_idx = None
                    hourly_cost_col_idx = None
                    rto_col_idx = None
                    
                    for idx, col_name in enumerate(header):
                        col_lower = str(col_name).lower()
                        if "asset" in col_lower and "id" in col_lower:
                            asset_id_col_idx = idx
                        elif "asset" in col_lower and "name" in col_lower:
                            asset_name_col_idx = idx
                        elif "hourly" in col_lower or ("cost" in col_lower and "hour" in col_lower):
                            hourly_cost_col_idx = idx
                        elif "rto" in col_lower:
                            rto_col_idx = idx
                    
                    if asset_id_col_idx is None:
                        continue
                    
                    # Search data rows for matching asset ID
                    for row in rows[1:]:  # Skip header
                        if len(row) > asset_id_col_idx:
                            row_asset_id = str(row[asset_id_col_idx]).strip().lower()
                            if row_asset_id == asset_id_lower:
                                # Found a match! Extract row data
                                matched_asset = asset.copy()
                                
                                # Extract asset name
                                if asset_name_col_idx is not None and len(row) > asset_name_col_idx:
                                    matched_asset["extracted_asset_name"] = str(row[asset_name_col_idx])
                                
                                # Extract financial data
                                matched_asset["extracted_financial_data"] = {}
                                
                                if hourly_cost_col_idx is not None and len(row) > hourly_cost_col_idx:
                                    try:
                                        cost_str = str(row[hourly_cost_col_idx]).replace("$", "").replace(",", "").strip()
                                        matched_asset["extracted_financial_data"]["hourly_cost"] = float(cost_str)
                                    except (ValueError, AttributeError):
                                        pass
                                
                                if rto_col_idx is not None and len(row) > rto_col_idx:
                                    try:
                                        rto_str = str(row[rto_col_idx]).replace("hours", "").replace("hour", "").strip()
                                        matched_asset["extracted_financial_data"]["rto_hours"] = float(rto_str)
                                    except (ValueError, AttributeError):
                                        pass
                                
                                return matched_asset
            
            # Fallback: Handle dict structure (if asset data is already parsed as dict)
            if isinstance(asset_data, dict):
                for key in ["asset_id", "id", "asset_code", "code", "application_id"]:
                    value = str(asset_data.get(key, "")).lower()
                    if value == asset_id_lower:
                        return asset
            
            # Fallback: Handle list of records structure
            if isinstance(asset_data, list) and len(asset_data) > 0:
                first_record = asset_data[0]
                if isinstance(first_record, dict):
                    for key in ["asset_id", "id", "asset_code", "code", "application_id"]:
                        value = str(first_record.get(key, "")).lower()
                        if value == asset_id_lower:
                            return asset
        
        # No match found
        return None
    
    def _find_asset_by_name(
        self,
        asset_name: str,
        assets: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find asset by name (fuzzy matching).
        
        Args:
            asset_name: Name to search for
            assets: List of available assets
            
        Returns:
            Matched asset or None
        """
        asset_name_lower = asset_name.lower()
        
        for asset in assets:
            # Check filename
            filename = asset.get("filename", "").lower()
            if asset_name_lower in filename or filename in asset_name_lower:
                return asset
            
            # Check asset data for name fields
            asset_data = asset.get("data", {})
            if isinstance(asset_data, dict):
                # Look for common name fields
                for key in ["name", "asset_name", "service_name", "application"]:
                    value = str(asset_data.get(key, "")).lower()
                    if value and (asset_name_lower in value or value in asset_name_lower):
                        return asset
            
            # Check if asset data is a list of records
            if isinstance(asset_data, list) and len(asset_data) > 0:
                first_record = asset_data[0]
                if isinstance(first_record, dict):
                    for key in ["name", "asset_name", "service_name", "application"]:
                        value = str(first_record.get(key, "")).lower()
                        if value and (asset_name_lower in value or value in asset_name_lower):
                            return asset
        
        return None
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.rules
    
    def reload_rules(self):
        """Reload rules from configuration file"""
        self.rules = self._load_rules()
        print("✅ Asset mapping rules reloaded")


# Global instance
rule_mapper = RuleBasedMapper()
