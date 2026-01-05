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
    if not firebase_admin._apps:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Admin not initialized"
        )

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}"
        )
