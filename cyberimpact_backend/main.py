from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import tempfile
import git
import uuid

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RepoRequest(BaseModel):
    repo_url: str

@app.post("/scan/clone")
async def clone_repo(request: RepoRequest):
    try:
        # Define the base directory for cloned repos
        base_dir = os.path.join(os.getcwd(), "cloned_repos")
        os.makedirs(base_dir, exist_ok=True)

        # Create a unique directory for this specific clone
        # Using UUID to ensure uniqueness
        repo_name = request.repo_url.split("/")[-1].replace(".git", "")
        unique_id = str(uuid.uuid4())[:8]
        clone_dir_name = f"{repo_name}_{unique_id}"
        clone_path = os.path.join(base_dir, clone_dir_name)
        
        # Clone the repository
        git.Repo.clone_from(request.repo_url, clone_path)
        
        return {
            "message": "Repository cloned successfully",
            "temp_path": clone_path,
            "repo_url": request.repo_url
        }
    except git.GitCommandError as e:
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "CyberImpact Backend is running"}
