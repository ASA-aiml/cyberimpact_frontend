from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import git
from schemas import RepoRequest, SecurityCheckRequest
from services.repo_service import clone_repository, detect_tech_stack
from services.ai_service import perform_ai_check, summarize_scan_results
from services.scanner_service import run_security_scan
from services.report_service import generate_docx_report
from services.auth_service import verify_token

app = FastAPI()

security = HTTPBearer()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/verify-auth")
async def verify_authentication(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    decoded_token = verify_token(token)
    return {"message": "Authentication successful", "user": decoded_token}

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
        
        # Run selected tools
        for tool in request.selected_tools:
            # Check if it's a known static analysis tool
            if any(x in tool for x in ["bandit", "safety", "npm-audit", "secret-scanning", "semgrep", "njsscan"]):
                 results[tool] = run_security_scan(request.repo_path, tool)
            else:
                # Fallback to AI check for other/generic tools or if specific file analysis was requested
                # For now, we will just use the scanner service for everything we support
                # and maybe add a generic AI scan as an "extra" tool if requested.
                # But per user request, we focus on static tools.
                results[tool] = {"output": "Tool not supported for static scan yet."}

        # Generate AI Summary
        ai_summary = summarize_scan_results(results)

        # Generate Report
        report_path = generate_docx_report(request.repo_path, results, ai_summary) # Using repo path as URL proxy for now in report
        
        return {
            "message": "Security check completed",
            "results": results,
            "ai_summary": ai_summary,
            "report_url": f"/reports/{os.path.basename(report_path)}"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/reports/{report_filename}")
async def download_report(report_filename: str):
    file_path = os.path.join(os.getcwd(), "reports", report_filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=report_filename)
    raise HTTPException(status_code=404, detail="Report not found")

@app.get("/")
def read_root():
    return {"message": "CyberImpact Backend is running"}
