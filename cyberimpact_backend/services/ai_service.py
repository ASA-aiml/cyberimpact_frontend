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

def summarize_scan_results(scan_results: dict) -> str:
    """
    Summarizes the overall scan results using Gemini.
    """
    if not GEMINI_API_KEY:
        return "AI Summary unavailable (Quota/Key missing)."

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Prepare a summary of findings for the prompt
        findings_summary = ""
        for tool, result in scan_results.items():
            output = result.get("output")
            if isinstance(output, (dict, list)):
                findings_summary += f"\nTool: {tool}\nOutput: {str(output)[:2000]}...\n" # Truncate to avoid token limits
            else:
                findings_summary += f"\nTool: {tool}\nOutput: {str(output)[:500]}\n"

        prompt = f"""
        You are a Cyber Security Expert. Analyze the following security scan results and provide a user-friendly Executive Summary.
        
        1. Highlight the most critical vulnerabilities found (if any).
        2. Explain what they mean in simple terms.
        3. Recommend immediate next steps.
        4. If no major issues are found, confirm the code looks relatively safe but suggest general best practices.
        
        Keep the tone professional but helpful.
        
        Scan Results:
        {findings_summary}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Summarization Failed: {str(e)}"
