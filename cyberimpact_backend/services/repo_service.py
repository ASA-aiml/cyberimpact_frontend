import os
import git
import uuid
from typing import List

def clone_repository(repo_url: str) -> str:
    """
    Clones a repository to a unique temporary directory.
    Returns the absolute path to the cloned repository.
    """
    base_dir = os.path.join(os.getcwd(), "cloned_repos")
    os.makedirs(base_dir, exist_ok=True)

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    unique_id = str(uuid.uuid4())[:8]
    clone_dir_name = f"{repo_name}_{unique_id}"
    clone_path = os.path.join(base_dir, clone_dir_name)
    
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
