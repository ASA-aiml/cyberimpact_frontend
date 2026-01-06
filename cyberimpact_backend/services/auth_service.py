# cyberimpact_backend/services/auth_service.py
import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin
try:
    # Check if FIREBASE_CREDENTIALS_JSON is set
    firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    
    if firebase_creds_json:
        cred = credentials.Certificate(json.loads(firebase_creds_json))
    else:
        # Fallback to looking for a file path or default credentials if needed
        # For now, we expect the JSON content in the env var
        print("Warning: FIREBASE_CREDENTIALS_JSON not found. Firebase Admin not initialized.")
        cred = None

    if cred and not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Error initializing Firebase Admin: {e}")

def verify_token(token: str):
    # Check if Firebase was actually initialized
    if not firebase_admin._apps:
        print("CRITICAL: Firebase Admin not initialized!")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Admin not initialized"
        )

    try:
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        
        # --- THIS IS YOUR CONSOLE LOG ---
        print("\n" + "🚀" * 15)
        print("USER LOGIN SUCCESSFUL")
        print(f"UUID (uid): {decoded_token.get('uid')}")
        print(f"Email:      {decoded_token.get('email')}")
        print(f"Provider:   {decoded_token.get('firebase', {}).get('sign_in_provider')}")
        print("🚀" * 15 + "\n")
        
        return decoded_token
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials: {str(e)}"
        )