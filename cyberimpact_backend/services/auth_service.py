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
        # WORKAROUND: Firebase SDK is too strict about clock skew
        # Manually decode and validate the token with custom clock skew tolerance
        import jwt
        import time
        from jwt import PyJWKClient
        
        # Get Firebase project ID from credentials
        firebase_app = firebase_admin.get_app()
        project_id = firebase_app.project_id
        
        # Decode token WITHOUT verification first to check timing
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        
        # Check if token is issued in the future (clock skew issue)
        current_time = int(time.time())
        iat = unverified_payload.get('iat', 0)
        
        # Allow up to 10 seconds of clock skew
        CLOCK_SKEW_SECONDS = 10
        
        if iat > current_time + CLOCK_SKEW_SECONDS:
            print(f"⚠️ Token issued too far in future: iat={iat}, now={current_time}, diff={iat-current_time}s")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token issued too far in the future"
            )
        
        # If clock skew is within tolerance, use Firebase's verify_id_token
        # but catch the clock skew error and allow it if within our tolerance
        try:
            decoded_token = auth.verify_id_token(token, check_revoked=False)
        except Exception as e:
            error_msg = str(e)
            
            # Check if it's a clock skew error within our tolerance
            if "Token used too early" in error_msg or "used before issued" in error_msg:
                if iat <= current_time + CLOCK_SKEW_SECONDS:
                    # Clock skew is acceptable, manually verify the token
                    print(f"⚠️ Accepting token with {iat - current_time}s clock skew (within {CLOCK_SKEW_SECONDS}s tolerance)")
                    
                    # Verify signature using Firebase's public keys
                    jwks_url = f"https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"
                    jwks_client = PyJWKClient(jwks_url)
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    
                    # Verify with custom options allowing clock skew
                    decoded_token = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=["RS256"],
                        audience=project_id,
                        issuer=f"https://securetoken.google.com/{project_id}",
                        options={
                            "verify_exp": True,
                            "verify_iat": False,  # Skip strict iat check
                            "verify_aud": True,
                        },
                        leeway=CLOCK_SKEW_SECONDS  # Allow clock skew
                    )
                else:
                    raise
            else:
                raise
        
        # --- THIS IS YOUR CONSOLE LOG ---
        print("\n" + "🚀" * 15)
        print("USER LOGIN SUCCESSFUL")
        print(f"UUID (uid): {decoded_token.get('uid')}")
        print(f"Email:      {decoded_token.get('email')}")
        print(f"Provider:   {decoded_token.get('firebase', {}).get('sign_in_provider', 'N/A')}")
        print("🚀" * 15 + "\n")
        
        return decoded_token
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials: {str(e)}"
        )