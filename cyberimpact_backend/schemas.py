from pydantic import BaseModel
from typing import List

class RepoRequest(BaseModel):
    repo_url: str

class SecurityCheckRequest(BaseModel):
    repo_path: str
    selected_tools: List[str]
