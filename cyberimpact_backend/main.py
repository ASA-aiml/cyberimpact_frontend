# cyberimpact_backend/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import git
from pathlib import Path

from typeCast import (
    RepoRequest, SecurityCheckRequest, AssetInventoryResponse, 
    FinancialDocResponse, DocumentListItem
)
from services.git_repo_service import clone_repository, detect_tech_stack
from services.ai_service import perform_ai_check, summarize_scan_results
from services.scanner_service import run_security_scan
from services.report_generate_service import generate_docx_report
from services.auth_service import verify_token
from services.db.db_service import db_service
from services.db.file_service import FileService
from services.financial.financial_pipeline import process_scan_results, generate_financial_report_markdown
from config import MAX_FILE_SIZE

app = FastAPI()

security = HTTPBearer()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for production deployment)
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
async def perform_security_check(
    request: SecurityCheckRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Execute security scan with financial impact analysis (requires authentication)"""
    try:
        # Verify the user's token to get uploader_id for asset mapping
        token = credentials.credentials
        decoded_token = verify_token(token)
        uploader_id = decoded_token.get('uid')
        
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
        
        # NEW: Financial Impact Analysis Pipeline
        financial_analysis = None
        try:
            print("\n💰 Starting Financial Impact Analysis...")
            financial_analysis = process_scan_results(results, uploader_id)
            print("✅ Financial analysis completed successfully\n")
        except Exception as fin_error:
            print(f"⚠️ Financial analysis failed: {fin_error}")
            import traceback
            traceback.print_exc()
            # Continue even if financial analysis fails

        # Generate Report (with financial section if available)
        report_path = generate_docx_report(request.repo_path, results, ai_summary)
        
        # Append financial analysis to report if available
        if financial_analysis:
            try:
                financial_md = generate_financial_report_markdown(financial_analysis)
                with open(report_path, 'a', encoding='utf-8') as f:
                    f.write("\n\n")
                    f.write(financial_md)
                print("✅ Financial section added to report")
            except Exception as e:
                print(f"⚠️ Failed to append financial section to report: {e}")
        
        response = {
            "message": "Security check completed",
            "results": results,
            "ai_summary": ai_summary,
            "report_url": f"/reports/{os.path.basename(report_path)}"
        }
        
        # Add financial analysis to response if available
        if financial_analysis:
            # Get top 10 risk tickets (sorted by severity and financial impact)
            risk_tickets = financial_analysis.get("risk_tickets", [])[:10]
            
            response["financial_analysis"] = {
                "summary": financial_analysis["summary"],
                "vulnerabilities_processed": financial_analysis["vulnerabilities_processed"],
                "assets_mapped": financial_analysis["assets_mapped"],
                "risk_tickets_count": len(financial_analysis.get("risk_tickets", [])),
                "top_risk_tickets": risk_tickets  # Include top 10 tickets with full details
            }
        
        return response

    except HTTPException:
        raise
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

# File Upload Endpoints

@app.post("/api/upload/asset-inventory", response_model=AssetInventoryResponse)
async def upload_asset_inventory(
    file: UploadFile = File(...), 
    uploader_id: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload Asset Inventory Excel file (requires authentication)"""
    try:
        # Verify the user's token
        token = credentials.credentials
        decoded_token = verify_token(token)
        authenticated_uid = decoded_token.get('uid')
        
        # Use authenticated UID instead of client-provided uploader_id for security
        uploader_id = authenticated_uid
        # Validate file extension
        if not FileService.validate_asset_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only .xlsx files are allowed for Asset Inventory."
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if not FileService.validate_file_size(file_size):
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Save file temporarily
        file_path = FileService.save_uploaded_file(file_content, file.filename)
        
        try:
            # Process Excel file
            data = FileService.process_xlsx_file(file_path)
            
            # Store in MongoDB
            document_id = db_service.create_asset_inventory(
                filename=file.filename,
                file_size=file_size,
                data=data,
                uploader_id=uploader_id
            )
            
            # Get the created document
            document = db_service.get_asset_inventory(document_id)
            
            return AssetInventoryResponse(
                id=document["_id"],
                filename=document["filename"],
                upload_date=document["upload_date"],
                file_size=document["file_size"],
                message="Asset Inventory uploaded successfully"
            )
        finally:
            # Clean up temporary file
            FileService.delete_file(file_path)
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/api/upload/financial-doc", response_model=FinancialDocResponse)
async def upload_financial_document(
    file: UploadFile = File(...), 
    uploader_id: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload Financial Document (PDF, DOC, DOCX) (requires authentication)"""
    try:
        # Verify the user's token
        token = credentials.credentials
        decoded_token = verify_token(token)
        authenticated_uid = decoded_token.get('uid')
        
        # Use authenticated UID instead of client-provided uploader_id for security
        uploader_id = authenticated_uid
        # Validate file extension
        if not FileService.validate_financial_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only .pdf, .doc, and .docx files are allowed for Financial Documents."
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if not FileService.validate_file_size(file_size):
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Save file temporarily
        file_path = FileService.save_uploaded_file(file_content, file.filename)
        
        try:
            # Determine file type and process accordingly
            file_ext = Path(file.filename).suffix.lower()
            
            if file_ext == '.pdf':
                result = FileService.process_pdf_file(file_path)
            elif file_ext in ['.doc', '.docx']:
                result = FileService.process_docx_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Store in MongoDB
            document_id = db_service.create_financial_document(
                filename=file.filename,
                file_size=file_size,
                file_type=file_ext.replace('.', ''),
                extracted_text=result["extracted_text"],
                metadata=result["metadata"],
                uploader_id=uploader_id
            )
            
            # Get the created document
            document = db_service.get_financial_document(document_id)
            
            return FinancialDocResponse(
                id=document["_id"],
                filename=document["filename"],
                upload_date=document["upload_date"],
                file_size=document["file_size"],
                file_type=document["file_type"],
                message="Financial Document uploaded successfully"
            )
        finally:
            # Clean up temporary file
            FileService.delete_file(file_path)
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/api/documents/asset-inventory")
async def list_asset_inventories(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """List uploaded asset inventories for the authenticated user"""
    try:
        # Verify the user's token
        token = credentials.credentials
        decoded_token = verify_token(token)
        user_uid = decoded_token.get('uid')
        
        # Get only documents uploaded by this user
        documents = db_service.list_asset_inventories_by_user(user_uid)
        return {
            "count": len(documents),
            "documents": [
                {
                    "id": doc["_id"],
                    "filename": doc["filename"],
                    "upload_date": doc["upload_date"],
                    "file_size": doc["file_size"],
                    "file_type": doc["file_type"]
                }
                for doc in documents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/api/documents/financial")
async def list_financial_documents(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """List uploaded financial documents for the authenticated user"""
    try:
        # Verify the user's token
        token = credentials.credentials
        decoded_token = verify_token(token)
        user_uid = decoded_token.get('uid')
        
        # Get only documents uploaded by this user
        documents = db_service.list_financial_documents_by_user(user_uid)
        return {
            "count": len(documents),
            "documents": [
                {
                    "id": doc["_id"],
                    "filename": doc["filename"],
                    "upload_date": doc["upload_date"],
                    "file_size": doc["file_size"],
                    "file_type": doc["file_type"]
                }
                for doc in documents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/api/documents/{document_id}")
async def get_document(document_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get document by UUID (only if owned by authenticated user)"""
    try:
        # Verify the user's token
        token = credentials.credentials
        decoded_token = verify_token(token)
        user_uid = decoded_token.get('uid')
        
        # Try asset inventory first
        document = db_service.get_asset_inventory(document_id)
        if document:
            # Check if user owns this document
            if document.get("metadata", {}).get("uploader_id") != user_uid:
                raise HTTPException(status_code=403, detail="Access denied: You don't own this document")
            return {"type": "asset_inventory", "document": document}
        
        # Try financial documents
        document = db_service.get_financial_document(document_id)
        if document:
            # Check if user owns this document
            if document.get("metadata", {}).get("uploader_id") != user_uid:
                raise HTTPException(status_code=403, detail="Access denied: You don't own this document")
            return {"type": "financial_document", "document": document}
        
        raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Delete document by UUID (only if owned by authenticated user)"""
    try:
        # Verify the user's token
        token = credentials.credentials
        decoded_token = verify_token(token)
        user_uid = decoded_token.get('uid')
        
        # Check asset inventory first
        document = db_service.get_asset_inventory(document_id)
        if document:
            # Verify ownership
            if document.get("metadata", {}).get("uploader_id") != user_uid:
                raise HTTPException(status_code=403, detail="Access denied: You don't own this document")
            if db_service.delete_asset_inventory(document_id):
                return {"message": "Asset inventory deleted successfully"}
        
        # Check financial documents
        document = db_service.get_financial_document(document_id)
        if document:
            # Verify ownership
            if document.get("metadata", {}).get("uploader_id") != user_uid:
                raise HTTPException(status_code=403, detail="Access denied: You don't own this document")
            if db_service.delete_financial_document(document_id):
                return {"message": "Financial document deleted successfully"}
        
        raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "CyberImpact Backend is running"}
