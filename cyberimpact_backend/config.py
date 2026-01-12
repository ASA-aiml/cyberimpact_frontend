# cyberimpact_backend/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# MongoDB Configuration
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "cyberimpact_db")

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_ASSET_EXTENSIONS = {".xlsx"}
ALLOWED_FINANCIAL_EXTENSIONS = {".pdf", ".doc", ".docx"}
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
