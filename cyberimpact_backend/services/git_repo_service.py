"""
================================================================================
REPOSITORY INGESTION & TECH-STACK DETECTOR
================================================================================

DESCRIPTION:
    This module handles the 'Discovery' phase of the security pipeline. It is 
    responsible for safely cloning remote source code and intelligently 
    analyzing the project structure to determine which security tools are 
    applicable to the codebase.

CORE FUNCTIONS:
    1.  Secure Ingestion: 
        Clones remote Git repositories into isolated, unique directories using 
        UUIDs to prevent path collisions and ensure clean scan environments.
    2.  Heuristic Tech-Stack Analysis: 
        Scans for "fingerprint" files (e.g., package.json, requirements.txt, 
        pom.xml) to identify the programming languages and package managers used.
    3.  Dynamic Tool Mapping: 
        Maps detected technologies to specific security scanners:
        - Python: Bandit, Safety
        - Node.js: npm-audit, njsscan
        - Java/Go/Ruby: Dependency Check, Gosec, Brakeman
        - Universal: Semgrep, Secret Scanning

WORKFLOW:
    - Input: A remote repository URL.
    - Process: Clone -> Walk directory tree -> Match files to tool signatures.
    - Output: A local path for scanning and a list of optimized security tools.

USAGE:
    This is the first module executed in the pipeline. It provides the 
    foundation for the 'run_security_scan' module by defining what needs to 
    be scanned and which tools to use.

AUTHOR: ABhiram PS
DATE: 2026-01-14
================================================================================
"""

import os
import git
import uuid
from typing import List

def clone_repository(repo_url: str, session_repos_dir: str) -> str:
    """
    Clones a repository to the session-specific repos directory.
    
    Args:
        repo_url: Git repository URL to clone
        session_repos_dir: Session-specific repos directory path (from session manager)
    
    Returns:
        str: Absolute path to the cloned repository
    """
    # Extract repo name from URL
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    unique_id = str(uuid.uuid4())[:8]
    clone_dir_name = f"{repo_name}_{unique_id}"
    clone_path = os.path.join(session_repos_dir, clone_dir_name)
    
    # Clone the repository
    git.Repo.clone_from(repo_url, clone_path)
    return clone_path

def detect_tech_stack(repo_path: str) -> List[str]:
    """
    Detects the tech stack based on file existence and returns suggested tools.
    """
    suggested_tools = set()
    
    # Walk through the repo to find key files
    # Limit depth to avoid deep traversal
    for root, dirs, files in os.walk(repo_path):
        if ".git" in dirs:
            dirs.remove(".git")
            
        files_set = set(files)
        
        if "requirements.txt" in files_set or "Pipfile" in files_set or "pyproject.toml" in files_set:
            suggested_tools.add("bandit (python)")
            suggested_tools.add("safety (python-deps)")
            
        if "package.json" in files_set or "yarn.lock" in files_set:
            suggested_tools.add("npm-audit (node)")
            suggested_tools.add("njsscan (node)")
            
        if "pom.xml" in files_set or "build.gradle" in files_set:
            suggested_tools.add("dependency-check (java)")
            
        if "go.mod" in files_set:
            suggested_tools.add("gosec (go)")
            
        if "Gemfile" in files_set:
            suggested_tools.add("brakeman (ruby)")
            
        # Stop after checking root and one level deep to be fast
        if root.count(os.sep) - repo_path.count(os.sep) >= 1:
            break
            
    # Default tools
    suggested_tools.add("secret-scanning")
    suggested_tools.add("semgrep (sast)")
    
    return list(suggested_tools)
