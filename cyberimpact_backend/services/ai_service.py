import google.generativeai as genai
from config import GEMINI_API_KEY
import os

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def perform_ai_check(tool: str, file_path: str, content: str) -> str:
    """
    Uses Gemini to simulate a security tool check on a file.
    """
    if not GEMINI_API_KEY:
        return "AI Security Check unavailable (Quota/Key missing). In a real app, we would run the actual CLI tool here."

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        prompt = f"""
        Perform a "{tool}" on the following code file.
        Identify any security vulnerabilities or issues.
        Return a brief summary of findings. If safe, say "No issues found".
        
        File: {os.path.basename(file_path)}
        Content:
        {content[:5000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Analysis Failed: {str(e)}"
