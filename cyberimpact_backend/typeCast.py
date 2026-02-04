# cyberimpact_backend/typeCast.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class RepoRequest(BaseModel):
    repo_url: str

class SecurityCheckRequest(BaseModel):
    session_id: str
    selected_tools: List[str]

class DocumentMetadata(BaseModel):
    uploader_id: Optional[str] = None
    original_filename: str

class AssetInventoryResponse(BaseModel):
    id: str
    filename: str
    upload_date: str
    file_size: int
    message: str

class FinancialDocResponse(BaseModel):
    id: str
    filename: str
    upload_date: str
    file_size: int
    file_type: str
    message: str

class DocumentListItem(BaseModel):
    id: str
    filename: str
    upload_date: str
    file_size: int
    file_type: str
