import subprocess
import os
import json
import shutil
import sys

def run_command(command, cwd=None):
    try:
        # Update PATH to include venv bin
        env = os.environ.copy()
        venv_bin = os.path.dirname(sys.executable)
        env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
        
        result = subprocess.run(
            command, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            shell=True,
            env=env
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1

def run_security_scan(repo_path: str, tool: str) -> dict:
    """
    Runs a specific security tool on the repository.
    Returns a dictionary with the results including filtered essential data.
    """
    results = {"tool": tool, "output": "", "error": "", "essential": []}
    
    # Get venv bin path for python tools
    venv_bin = os.path.dirname(sys.executable)
    
    if "bandit" in tool:
        # Bandit for Python
        cmd = f"bandit -r . -f json"
        stdout, stderr, _ = run_command(cmd, cwd=repo_path)
        try:
            output = json.loads(stdout)
            results["output"] = output
            # Extract essential data
            if "results" in output:
                for issue in output["results"]:
                    results["essential"].append({
                        "file": issue.get("filename", ""),
                        "line": issue.get("line_number", ""),
                        "severity": issue.get("issue_severity", ""),
                        "confidence": issue.get("issue_confidence", ""),
                        "issue": issue.get("issue_text", ""),
                        "test_id": issue.get("test_id", "")
                    })
        except:
            results["output"] = stdout
            results["error"] = stderr

    elif "safety" in tool:
        # Safety for Python dependencies
        if os.path.exists(os.path.join(repo_path, "requirements.txt")):
            cmd = f"safety check -r requirements.txt --json"
            stdout, stderr, _ = run_command(cmd, cwd=repo_path)
            try:
                json_start = stdout.find("[")
                if json_start != -1:
                    output = json.loads(stdout[json_start:])
                    results["output"] = output
                    # Extract essential data
                    for vuln in output:
                        results["essential"].append({
                            "package": vuln.get("package", ""),
                            "installed_version": vuln.get("installed_version", ""),
                            "vulnerability": vuln.get("vulnerability", ""),
                            "severity": vuln.get("severity", ""),
                            "affected_versions": vuln.get("affected_versions", "")
                        })
                else:
                    results["output"] = stdout
            except:
                results["output"] = stdout
                results["error"] = stderr
        else:
            results["output"] = "No requirements.txt found."

    elif "npm-audit" in tool:
        # npm audit for Node.js
        if os.path.exists(os.path.join(repo_path, "package.json")):
            cmd = "npm audit --json"
            stdout, stderr, _ = run_command(cmd, cwd=repo_path)
            try:
                output = json.loads(stdout)
                results["output"] = output
                # Extract essential data
                if "vulnerabilities" in output:
                    for pkg, vuln in output["vulnerabilities"].items():
                        results["essential"].append({
                            "package": pkg,
                            "severity": vuln.get("severity", ""),
                            "via": vuln.get("via", ""),
                            "range": vuln.get("range", "")
                        })
            except:
                results["output"] = stdout
                results["error"] = stderr
        else:
            results["output"] = "No package.json found."

    elif "secret-scanning" in tool:
        # Simple regex based secret scanning
        findings = []
        import re
        secret_patterns = {
            "AWS Key": r"AKIA[0-9A-Z]{16}",
            "Generic API Key": r"api_key\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]",
        }
        
        for root, dirs, files in os.walk(repo_path):
            if ".git" in dirs: dirs.remove(".git")
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", errors="ignore") as f:
                        content = f.read()
                        for name, pattern in secret_patterns.items():
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                finding = {
                                    "type": name,
                                    "file": file,
                                    "match": match.group()[:20] + "..."  # Truncate for security
                                }
                                findings.append(f"Potential {name} found in {file}")
                                results["essential"].append(finding)
                except:
                    pass
        results["output"] = findings if findings else "No secrets found."

    elif "semgrep" in tool:
        # Semgrep (SAST)
        cmd = "semgrep scan --config=auto --json"
        stdout, stderr, _ = run_command(cmd, cwd=repo_path)
        try:
            output = json.loads(stdout)
            results["output"] = output
            # Extract essential data
            if "results" in output:
                for finding in output["results"]:
                    results["essential"].append({
                        "file": finding.get("path", ""),
                        "line": finding.get("start", {}).get("line", ""),
                        "severity": finding.get("extra", {}).get("severity", ""),
                        "message": finding.get("extra", {}).get("message", ""),
                        "rule_id": finding.get("check_id", "")
                    })
        except:
            results["output"] = stdout
            results["error"] = stderr

    elif "njsscan" in tool:
        # njsscan (Node.js SAST)
        cmd = f"njsscan . --json"
        stdout, stderr, _ = run_command(cmd, cwd=repo_path)
        try:
            output = json.loads(stdout)
            results["output"] = output
            # Extract essential data
            if isinstance(output, dict):
                for severity in ["ERROR", "WARNING", "INFO"]:
                    if severity.lower() in output:
                        for file, issues in output[severity.lower()].items():
                            for issue in issues:
                                results["essential"].append({
                                    "file": file,
                                    "severity": severity,
                                    "rule": issue.get("rule", ""),
                                    "line": issue.get("line", ""),
                                    "description": issue.get("description", "")
                                })
        except:
            results["output"] = stdout
            results["error"] = stderr

    else:
        results["output"] = "Tool not implemented or supported in this demo environment."

    return results


def generate_markdown_report(scan_results: list, output_file: str = "security_report.md"):
    """
    Generate a markdown report from security scan results.
    
    Args:
        scan_results: List of dictionaries containing scan results from run_security_scan
        output_file: Name of the output markdown file
    """
    with open(output_file, 'w') as f:
        # Header
        f.write("# Security Scan Report\n\n")
        f.write(f"Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        f.write(f"Total tools executed: {len(scan_results)}\n\n")
        
        total_issues = sum(len(result.get("essential", [])) for result in scan_results)
        f.write(f"Total issues found: {total_issues}\n\n")
        f.write("---\n\n")
        
        # Detailed Results
        for result in scan_results:
            tool_name = result.get("tool", "Unknown Tool")
            f.write(f"## {tool_name}\n\n")
            
            essential = result.get("essential", [])
            error = result.get("error", "")
            
            if error:
                f.write(f"**Error:** {error}\n\n")
            
            if not essential or (isinstance(essential, list) and len(essential) == 0):
                f.write("✅ No issues found.\n\n")
            else:
                f.write(f"**Issues found:** {len(essential)}\n\n")
                
                # Format based on tool type
                if "bandit" in tool_name.lower():
                    for idx, issue in enumerate(essential, 1):
                        f.write(f"### Issue {idx}\n")
                        f.write(f"- **File:** `{issue.get('file', 'N/A')}`\n")
                        f.write(f"- **Line:** {issue.get('line', 'N/A')}\n")
                        f.write(f"- **Severity:** {issue.get('severity', 'N/A')}\n")
                        f.write(f"- **Confidence:** {issue.get('confidence', 'N/A')}\n")
                        f.write(f"- **Issue:** {issue.get('issue', 'N/A')}\n")
                        f.write(f"- **Test ID:** {issue.get('test_id', 'N/A')}\n\n")
                
                elif "safety" in tool_name.lower():
                    for idx, vuln in enumerate(essential, 1):
                        f.write(f"### Vulnerability {idx}\n")
                        f.write(f"- **Package:** `{vuln.get('package', 'N/A')}`\n")
                        f.write(f"- **Installed Version:** {vuln.get('installed_version', 'N/A')}\n")
                        f.write(f"- **Severity:** {vuln.get('severity', 'N/A')}\n")
                        f.write(f"- **Vulnerability:** {vuln.get('vulnerability', 'N/A')}\n")
                        f.write(f"- **Affected Versions:** {vuln.get('affected_versions', 'N/A')}\n\n")
                
                elif "npm-audit" in tool_name.lower():
                    for idx, vuln in enumerate(essential, 1):
                        f.write(f"### Vulnerability {idx}\n")
                        f.write(f"- **Package:** `{vuln.get('package', 'N/A')}`\n")
                        f.write(f"- **Severity:** {vuln.get('severity', 'N/A')}\n")
                        f.write(f"- **Via:** {vuln.get('via', 'N/A')}\n")
                        f.write(f"- **Range:** {vuln.get('range', 'N/A')}\n\n")
                
                elif "secret" in tool_name.lower():
                    for idx, secret in enumerate(essential, 1):
                        f.write(f"### Secret {idx}\n")
                        f.write(f"- **Type:** {secret.get('type', 'N/A')}\n")
                        f.write(f"- **File:** `{secret.get('file', 'N/A')}`\n")
                        f.write(f"- **Match:** `{secret.get('match', 'N/A')}`\n\n")
                
                elif "semgrep" in tool_name.lower():
                    for idx, finding in enumerate(essential, 1):
                        f.write(f"### Finding {idx}\n")
                        f.write(f"- **File:** `{finding.get('file', 'N/A')}`\n")
                        f.write(f"- **Line:** {finding.get('line', 'N/A')}\n")
                        f.write(f"- **Severity:** {finding.get('severity', 'N/A')}\n")
                        f.write(f"- **Rule ID:** {finding.get('rule_id', 'N/A')}\n")
                        f.write(f"- **Message:** {finding.get('message', 'N/A')}\n\n")
                
                elif "njsscan" in tool_name.lower():
                    for idx, issue in enumerate(essential, 1):
                        f.write(f"### Issue {idx}\n")
                        f.write(f"- **File:** `{issue.get('file', 'N/A')}`\n")
                        f.write(f"- **Line:** {issue.get('line', 'N/A')}\n")
                        f.write(f"- **Severity:** {issue.get('severity', 'N/A')}\n")
                        f.write(f"- **Rule:** {issue.get('rule', 'N/A')}\n")
                        f.write(f"- **Description:** {issue.get('description', 'N/A')}\n\n")
                
                else:
                    # Generic format for other tools
                    for idx, item in enumerate(essential, 1):
                        f.write(f"### Item {idx}\n")
                        for key, value in item.items():
                            f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
                        f.write("\n")
            
            f.write("---\n\n")
        
        # Footer
        f.write("## Recommendations\n\n")
        f.write("- Review all high and critical severity issues immediately\n")
        f.write("- Update vulnerable dependencies to patched versions\n")
        f.write("- Remove or secure any exposed secrets\n")
        f.write("- Follow secure coding practices to prevent future issues\n\n")
        f.write("---\n\n")
        f.write("*End of Report*\n")
    
    print(f"Markdown report generated: {output_file}")
    return output_file