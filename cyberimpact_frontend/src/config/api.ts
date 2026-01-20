// API Configuration
// For production, set NEXT_PUBLIC_API_URL environment variable
// For local development, it defaults to localhost:8000

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
    verifyAuth: `${API_URL}/api/verify-auth`,
    scanAnalyze: `${API_URL}/scan/analyze`,
    scanExecute: `${API_URL}/scan/execute`,
    uploadAssetInventory: `${API_URL}/api/upload/asset-inventory`,
    uploadFinancialDoc: `${API_URL}/api/upload/financial-doc`,
    listAssetInventories: `${API_URL}/api/documents/asset-inventory`,
    listFinancialDocs: `${API_URL}/api/documents/financial`,
    getDocument: (id: string) => `${API_URL}/api/documents/${id}`,
    deleteDocument: (id: string) => `${API_URL}/api/documents/${id}`,
    getReport: (url: string) => `${API_URL}${url}`,
};
