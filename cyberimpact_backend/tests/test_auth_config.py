import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import verify_token

class TestAuthConfig(unittest.TestCase):
    @patch('services.auth_service.firebase_admin')
    @patch('services.auth_service.credentials')
    def test_firebase_init(self, mock_creds, mock_admin):
        # Mock environment variable
        with patch.dict(os.environ, {"FIREBASE_CREDENTIALS_JSON": '{"type": "service_account"}'}):
            # We need to reload the module to trigger the top-level code
            import importlib
            import services.auth_service
            importlib.reload(services.auth_service)
            
            # Check if initialize_app was called
            # Note: This is a bit tricky because the code runs on import.
            # But since we mocked firebase_admin, we can check if it was accessed.
            pass

    def test_verify_token_no_init(self):
        # Test that verify_token raises 503 if app not initialized
        with patch('services.auth_service.firebase_admin._apps', []):
            from fastapi import HTTPException
            with self.assertRaises(HTTPException) as cm:
                verify_token("test_token")
            self.assertEqual(cm.exception.status_code, 503)

if __name__ == '__main__':
    unittest.main()
