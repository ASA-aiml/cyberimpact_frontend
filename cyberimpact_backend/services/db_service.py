# cyberimpact_backend/services/db_service.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from config import MONGODB_URI, DATABASE_NAME
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBService:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self.connect()

    def connect(self):
        """Initialize MongoDB connection"""
        try:
            self._client = MongoClient(MONGODB_URI)
            # Test the connection
            self._client.admin.command('ping')
            self._db = self._client[DATABASE_NAME]
            print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        if self._db is None:
            self.connect()
        return self._db[collection_name]

    # Asset Inventory Operations
    def create_asset_inventory(self, filename: str, file_size: int, data: Dict[str, Any], uploader_id: Optional[str] = None) -> str:
        """Create a new asset inventory document"""
        collection = self.get_collection("asset_inventory")
        
        document = {
            "_id": str(uuid.uuid4()),
            "filename": filename,
            "upload_date": datetime.utcnow().isoformat(),
            "file_size": file_size,
            "file_type": "xlsx",
            "data": data,
            "metadata": {
                "uploader_id": uploader_id,
                "original_filename": filename
            }
        }
        
        collection.insert_one(document)
        return document["_id"]

    def get_asset_inventory(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get asset inventory by UUID"""
        collection = self.get_collection("asset_inventory")
        return collection.find_one({"_id": document_id})

    def list_asset_inventories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all asset inventories"""
        collection = self.get_collection("asset_inventory")
        return list(collection.find().limit(limit))
    
    def list_asset_inventories_by_user(self, uploader_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """List asset inventories for a specific user"""
        collection = self.get_collection("asset_inventory")
        return list(collection.find({"metadata.uploader_id": uploader_id}).limit(limit))

    def delete_asset_inventory(self, document_id: str) -> bool:
        """Delete asset inventory by UUID"""
        collection = self.get_collection("asset_inventory")
        result = collection.delete_one({"_id": document_id})
        return result.deleted_count > 0

    # Financial Document Operations
    def create_financial_document(self, filename: str, file_size: int, file_type: str, 
                                  extracted_text: str, metadata: Dict[str, Any], 
                                  uploader_id: Optional[str] = None) -> str:
        """Create a new financial document"""
        collection = self.get_collection("financial_documents")
        
        document = {
            "_id": str(uuid.uuid4()),
            "filename": filename,
            "upload_date": datetime.utcnow().isoformat(),
            "file_size": file_size,
            "file_type": file_type,
            "extracted_text": extracted_text,
            "metadata": {
                "uploader_id": uploader_id,
                "original_filename": filename,
                **metadata
            }
        }
        
        collection.insert_one(document)
        return document["_id"]

    def get_financial_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get financial document by UUID"""
        collection = self.get_collection("financial_documents")
        return collection.find_one({"_id": document_id})

    def list_financial_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all financial documents"""
        collection = self.get_collection("financial_documents")
        return list(collection.find().limit(limit))
    
    def list_financial_documents_by_user(self, uploader_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """List financial documents for a specific user"""
        collection = self.get_collection("financial_documents")
        return list(collection.find({"metadata.uploader_id": uploader_id}).limit(limit))

    def delete_financial_document(self, document_id: str) -> bool:
        """Delete financial document by UUID"""
        collection = self.get_collection("financial_documents")
        result = collection.delete_one({"_id": document_id})
        return result.deleted_count > 0

    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            print("MongoDB connection closed")

# Singleton instance
db_service = MongoDBService()
