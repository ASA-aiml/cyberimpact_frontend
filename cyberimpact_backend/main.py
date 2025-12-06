# cyberimpact_backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import git
from schemas import RepoRequest, SecurityCheckRequest
from services.repo_service import clone_repository, detect_tech_stack
from services.ai_service import perform_ai_check

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/scan/analyze")
async def analyze_repo(request: RepoRequest):
    try:
        # Clone the repository
        clone_path = clone_repository(request.repo_url)
        
        # Detect tech stack using heuristics
        suggested_tools = detect_tech_stack(clone_path)

        return {
            "message": "Repository analyzed successfully",
            "repo_path": clone_path,
            "repo_url": request.repo_url,
            "suggested_tools": suggested_tools
        }
    except git.GitCommandError as e:
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/scan/execute")
async def perform_security_check(request: SecurityCheckRequest):
    try:
        results = {}
        
        files_to_check = []
        for root, dirs, files in os.walk(request.repo_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.go', '.rb', '.php')):
                     files_to_check.append(os.path.join(root, file))
        
        # Limit to first 3 files for performance
        files_to_check = files_to_check[:3] 
        
        for tool in request.selected_tools:
            tool_results = []
            for file_path in files_to_check:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    analysis = perform_ai_check(tool, file_path, content)

                    tool_results.append({
                        "file": os.path.basename(file_path),
                        "analysis": analysis
                    })
                except Exception as e:
                    tool_results.append({
                        "file": os.path.basename(file_path),
                        "error": str(e)
                    })
            results[tool] = tool_results

        return {
            "message": "Security check completed",
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "CyberImpact Backend is running"}
