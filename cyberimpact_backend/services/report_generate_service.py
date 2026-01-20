"""
================================================================================
SECURITY REPORT GENERATOR (MARKDOWN)
================================================================================

DESCRIPTION:
    This module is responsible for the 'Finalization' phase of the security
    scanning pipeline. It takes raw findings from multiple SAST and dependency 
    auditing tools, calculates severity statistics, and compiles them into a 
    structured, professional Markdown report.

KEY FEATURES:
    1.  Severity Aggregation: 
        Automatically calculates a breakdown of Critical, High, Moderate, and 
        Low severity issues using color-coded indicators (🔴, 🟠, 🟡, 🟢).
    2.  AI Integration: 
        Includes a dedicated section for an 'AI Executive Summary' to provide
        high-level context alongside technical findings.
    3.  Tool-Specific Formatting: 
        Features custom parsing logic for various security tools (Bandit, 
        npm-audit, Safety, Semgrep, etc.) to ensure that file paths, line numbers, 
        and vulnerability URLs are presented clearly.
    4.  Automated Recommendations: 
        Dynamically generates a 'Priority Action Plan' based on the specific 
        threat levels found during the scan.

REPORT STRUCTURE:
    - Metadata (Repo URL, Timestamp)
    - AI Executive Summary
    - Statistical Summary (Severity Counts)
    - Detailed Findings (Filtered 'Essential' data per tool)
    - Remediation Recommendations

USAGE:
    Called after all security tools have finished execution. The resulting 
    '.md' file is saved in the /reports directory and is ideal for PR comments, 
    compliance documentation, or stakeholder updates.

AUTHOR: ABhiram PS
DATE: 2026-01-14
================================================================================
"""

import os
import datetime
import json

def generate_docx_report(repo_url: str, scan_results: dict, ai_summary: str = "") -> str:
    
    # Generates a Markdown report from scan results with focus on essential findings.
    # Returns the path to the generated file.
   
    
    # Create reports directory
    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    file_path = os.path.join(reports_dir, filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        # Title
        f.write('# Security Scan Report\n\n')
        
        # Metadata
        f.write(f'**Repository:** {repo_url}\n\n')
        f.write(f'**Date:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        f.write('---\n\n')
        
        # AI Summary
        if ai_summary:
            f.write('## AI Executive Summary\n\n')
            f.write(f'{ai_summary}\n\n')
        else:
            f.write('## AI Executive Summary\n\n')
            f.write('AI Summary unavailable (Quota/Key missing).\n\n')
        
        f.write('---\n\n')
        
        # Summary Statistics
        f.write('## Summary\n\n')
        total_issues = 0
        critical_count = 0
        high_count = 0
        moderate_count = 0
        low_count = 0
        
        for tool, result in scan_results.items():
            essential = result.get("essential", [])
            if essential and len(essential) > 0:
                total_issues += len(essential)
                # Count severity levels
                for item in essential:
                    severity = str(item.get("severity", "")).lower()
                    if "critical" in severity:
                        critical_count += 1
                    elif "high" in severity:
                        high_count += 1
                    elif "moderate" in severity or "medium" in severity:
                        moderate_count += 1
                    elif "low" in severity or "warning" in severity:
                        low_count += 1
        
        f.write(f'**Total Issues Found:** {total_issues}\n\n')
        if total_issues > 0:
            f.write('**Severity Breakdown:**\n')
            if critical_count > 0:
                f.write(f'- 🔴 Critical: {critical_count}\n')
            if high_count > 0:
                f.write(f'- 🟠 High: {high_count}\n')
            if moderate_count > 0:
                f.write(f'- 🟡 Moderate: {moderate_count}\n')
            if low_count > 0:
                f.write(f'- 🟢 Low/Warning: {low_count}\n')
            f.write('\n')
        
        f.write('---\n\n')
        
        # Detailed Findings - Essential Data Only
        f.write('## Detailed Findings\n\n')
        
        # Results for each tool
        for tool, result in scan_results.items():
            f.write(f'## Tool: {tool}\n\n')
            
            error = result.get("error")
            essential = result.get("essential", [])
            
            # Display errors if any
            if error:
                f.write(f'**⚠️ Error executing tool:**\n\n')
                f.write(f'```\n{error}\n```\n\n')
            
            # Display essential findings if available
            if essential and len(essential) > 0:
                f.write(f'### Essential Findings ({len(essential)} issues)\n\n')
                
                for idx, item in enumerate(essential, 1):
                    # Add severity emoji
                    severity = str(item.get("severity", "")).lower()
                    emoji = "🔴" if "critical" in severity else "🟠" if "high" in severity else "🟡" if "moderate" in severity or "medium" in severity else "🟢"
                    
                    f.write(f'#### {emoji} Finding {idx}\n\n')
                    
                    # Format based on tool type for better readability
                    if "npm-audit" in tool.lower():
                        f.write(f'- **Package:** `{item.get("package", "N/A")}`\n')
                        f.write(f'- **Severity:** {item.get("severity", "N/A")}\n')
                        f.write(f'- **Affected Range:** {item.get("range", "N/A")}\n')
                        
                        # Extract vulnerability details from 'via' if it's a list
                        via = item.get("via", [])
                        if isinstance(via, list) and len(via) > 0:
                            f.write(f'- **Vulnerabilities:**\n')
                            for v in via:
                                if isinstance(v, dict):
                                    f.write(f'  - **{v.get("title", "Unknown")}**\n')
                                    f.write(f'    - URL: {v.get("url", "N/A")}\n')
                                    if "cvss" in v:
                                        f.write(f'    - CVSS Score: {v.get("cvss", {}).get("score", "N/A")}\n')
                                    if "cwe" in v:
                                        f.write(f'    - CWE: {", ".join(v.get("cwe", []))}\n')
                        else:
                            f.write(f'- **Via:** {via}\n')
                    
                    elif "bandit" in tool.lower():
                        f.write(f'- **File:** `{item.get("file", "N/A")}`\n')
                        f.write(f'- **Line:** {item.get("line", "N/A")}\n')
                        f.write(f'- **Severity:** {item.get("severity", "N/A")}\n')
                        f.write(f'- **Confidence:** {item.get("confidence", "N/A")}\n')
                        f.write(f'- **Issue:** {item.get("issue", "N/A")}\n')
                        f.write(f'- **Test ID:** {item.get("test_id", "N/A")}\n')
                    
                    elif "safety" in tool.lower():
                        f.write(f'- **Package:** `{item.get("package", "N/A")}`\n')
                        f.write(f'- **Installed Version:** {item.get("installed_version", "N/A")}\n')
                        f.write(f'- **Severity:** {item.get("severity", "N/A")}\n')
                        f.write(f'- **Vulnerability:** {item.get("vulnerability", "N/A")}\n')
                        f.write(f'- **Affected Versions:** {item.get("affected_versions", "N/A")}\n')
                    
                    elif "secret" in tool.lower():
                        f.write(f'- **Type:** {item.get("type", "N/A")}\n')
                        f.write(f'- **File:** `{item.get("file", "N/A")}`\n')
                        f.write(f'- **Match:** `{item.get("match", "N/A")}`\n')
                    
                    elif "semgrep" in tool.lower():
                        f.write(f'- **File:** `{item.get("file", "N/A")}`\n')
                        f.write(f'- **Line:** {item.get("line", "N/A")}\n')
                        f.write(f'- **Severity:** {item.get("severity", "N/A")}\n')
                        f.write(f'- **Rule ID:** {item.get("rule_id", "N/A")}\n')
                        f.write(f'- **Message:** {item.get("message", "N/A")}\n')
                    
                    elif "njsscan" in tool.lower():
                        f.write(f'- **File:** `{item.get("file", "N/A")}`\n')
                        f.write(f'- **Line:** {item.get("line", "N/A")}\n')
                        f.write(f'- **Severity:** {item.get("severity", "N/A")}\n')
                        f.write(f'- **Rule:** {item.get("rule", "N/A")}\n')
                        f.write(f'- **Description:** {item.get("description", "N/A")}\n')
                    
                    else:
                        # Generic format for other tools
                        for key, value in item.items():
                            f.write(f'- **{key.replace("_", " ").title()}:** {value}\n')
                    
                    f.write('\n')
                
            else:
                # No issues found
                output = result.get("output", "")
                if isinstance(output, str) and ("no" in output.lower() and "found" in output.lower()):
                    f.write('✅ No issues found.\n\n')
                elif isinstance(output, dict) and output.get("results") == []:
                    f.write('✅ No issues found.\n\n')
                else:
                    f.write('ℹ️ No essential findings extracted.\n\n')
            
            f.write('---\n\n')
        
        # Recommendations
        f.write('## Recommendations\n\n')
        
        if critical_count > 0:
            f.write('### 🔴 Critical Priority\n\n')
            f.write('- **IMMEDIATE ACTION REQUIRED**: Address all critical severity vulnerabilities\n')
            f.write('- Review and patch critical vulnerabilities in dependencies\n')
            f.write('- Consider blocking deployment until critical issues are resolved\n\n')
        
        if high_count > 0:
            f.write('### 🟠 High Priority\n\n')
            f.write('- Address high severity issues within 24-48 hours\n')
            f.write('- Update vulnerable dependencies to patched versions\n')
            f.write('- Review security configurations\n\n')
        
        if moderate_count > 0 or low_count > 0:
            f.write('### 🟡 Medium/Low Priority\n\n')
            f.write('- Schedule fixes for moderate and low severity issues\n')
            f.write('- Include in next sprint or maintenance cycle\n\n')
        
        f.write('### General Recommendations\n\n')
        f.write('- Keep all dependencies up to date regularly\n')
        f.write('- Remove or properly secure any exposed secrets or credentials\n')
        f.write('- Implement secure coding practices and conduct code reviews\n')
        f.write('- Integrate security scanning into your CI/CD pipeline\n')
        f.write('- Conduct regular security audits and penetration testing\n')
        f.write('- Monitor security advisories for used dependencies\n\n')
        
        f.write('---\n\n')
        f.write('*End of Report*\n')
    
    print(f"✅ Markdown report generated: {file_path}")
    return file_path