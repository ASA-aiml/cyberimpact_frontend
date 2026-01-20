"use client";
import React, { useState } from "react";
import axios from "axios";
import { useUser } from "@/contexts/UserContext";
import { API_ENDPOINTS } from "@/config/api";

interface FinancialDocUploadProps {
    onUploadSuccess?: (data: any) => void;
}

export default function FinancialDocUpload({ onUploadSuccess }: FinancialDocUploadProps) {
    const { userUid, idToken } = useUser();
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [documents, setDocuments] = useState<any[]>([]);
    const [loadingDocs, setLoadingDocs] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            // Validate file type
            const validExtensions = ['.pdf', '.doc', '.docx'];
            const fileExt = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();

            if (!validExtensions.includes(fileExt)) {
                setError('Please select a valid .pdf, .doc, or .docx file');
                setFile(null);
                return;
            }

            // Validate file size (10MB)
            if (selectedFile.size > 10 * 1024 * 1024) {
                setError('File size must be less than 10MB');
                setFile(null);
                return;
            }

            setFile(selectedFile);
            setError(null);
            setUploadResult(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setError(null);
        setUploadResult(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            // Add uploader_id if user is logged in
            if (userUid) {
                formData.append('uploader_id', userUid);
            }

            const response = await axios.post(
                API_ENDPOINTS.uploadFinancialDoc,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                        'Authorization': `Bearer ${idToken}`,
                    },
                }
            );

            setUploadResult(response.data);
            setFile(null);

            // Reset file input
            const fileInput = document.getElementById('financial-file-input') as HTMLInputElement;
            if (fileInput) fileInput.value = '';

            // Callback
            if (onUploadSuccess) {
                onUploadSuccess(response.data);
            }

            // Refresh document list
            fetchDocuments();
        } catch (err: any) {
            console.error(err);
            setError(err?.response?.data?.detail || err.message || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    const fetchDocuments = async () => {
        setLoadingDocs(true);
        try {
            const response = await axios.get(API_ENDPOINTS.listFinancialDocs, {
                headers: {
                    'Authorization': `Bearer ${idToken}`,
                },
            });
            setDocuments(response.data.documents || []);
        } catch (err: any) {
            console.error('Failed to fetch documents:', err);
        } finally {
            setLoadingDocs(false);
        }
    };

    const deleteDocument = async (docId: string) => {
        if (!confirm('Are you sure you want to delete this document?')) return;

        try {
            await axios.delete(API_ENDPOINTS.deleteDocument(docId), {
                headers: {
                    'Authorization': `Bearer ${idToken}`,
                },
            });
            fetchDocuments();
        } catch (err: any) {
            console.error('Failed to delete document:', err);
            alert('Failed to delete document');
        }
    };

    const downloadDocument = async (docId: string, filename: string) => {
        try {
            const response = await axios.get(API_ENDPOINTS.getDocument(docId), {
                headers: {
                    'Authorization': `Bearer ${idToken}`,
                },
            });

            // Convert document data to JSON and create download
            const dataStr = JSON.stringify(response.data, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = window.URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${filename.replace(/\.(pdf|docx?|xlsx)$/i, '')}_data.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (err: any) {
            console.error('Failed to download document:', err);
            alert('Failed to download document');
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    const getFileIcon = (fileType: string) => {
        if (fileType === 'pdf') return '📄';
        if (fileType === 'doc' || fileType === 'docx') return '📝';
        return '📎';
    };

    React.useEffect(() => {
        fetchDocuments();
    }, []);

    return (
        <div className="space-y-6">
            <div className="bg-gray-900/60 backdrop-blur-md shadow-xl rounded-xl border border-gray-800 p-6">
                <h3 className="text-xl font-bold mb-4 text-green-300 flex items-center gap-2">
                    💼 Financial Document Upload
                </h3>

                <div className="space-y-4">
                    {/* File Input */}
                    <div>
                        <label className="block text-sm mb-2 font-semibold text-gray-300">
                            Select Document (.pdf, .doc, .docx)
                        </label>
                        <input
                            id="financial-file-input"
                            type="file"
                            accept=".pdf,.doc,.docx"
                            onChange={handleFileChange}
                            className="block w-full text-sm text-gray-300
                file:mr-4 file:py-2 file:px-4
                file:rounded-lg file:border-0
                file:text-sm file:font-semibold
                file:bg-green-600 file:text-white
                hover:file:bg-green-700
                file:cursor-pointer cursor-pointer
                bg-gray-800 rounded-lg border border-gray-700"
                        />
                        {file && (
                            <p className="mt-2 text-sm text-gray-400">
                                Selected: {file.name} ({formatFileSize(file.size)})
                            </p>
                        )}
                    </div>

                    {/* Upload Button */}
                    <button
                        onClick={handleUpload}
                        disabled={!file || uploading}
                        className={`w-full py-3 rounded-lg font-semibold transition ${!file || uploading
                            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                            : 'bg-green-600 hover:bg-green-700 text-white'
                            }`}
                    >
                        {uploading ? 'Uploading...' : 'Upload Financial Document'}
                    </button>

                    {/* Error Message */}
                    {error && (
                        <div className="p-4 bg-red-900/50 border border-red-800 rounded-lg text-red-200">
                            ❌ {error}
                        </div>
                    )}

                    {/* Success Message */}
                    {uploadResult && (
                        <div className="p-4 bg-green-900/50 border border-green-800 rounded-lg text-green-200">
                            <p className="font-semibold">✅ {uploadResult.message}</p>
                            <p className="text-sm mt-1">Document ID: <code className="bg-gray-800 px-1 rounded">{uploadResult.id}</code></p>
                            <p className="text-sm">Type: {uploadResult.file_type.toUpperCase()}</p>
                            <p className="text-sm">Uploaded: {formatDate(uploadResult.upload_date)}</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Document List */}
            <div className="bg-gray-900/60 backdrop-blur-md shadow-xl rounded-xl border border-gray-800 p-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold text-green-300">Uploaded Financial Documents</h3>
                    <button
                        onClick={fetchDocuments}
                        disabled={loadingDocs}
                        className="text-sm bg-gray-700 hover:bg-gray-600 text-gray-200 px-3 py-1 rounded-lg transition"
                    >
                        {loadingDocs ? 'Loading...' : '🔄 Refresh'}
                    </button>
                </div>

                {documents.length === 0 ? (
                    <p className="text-gray-500 italic">No documents uploaded yet.</p>
                ) : (
                    <div className="space-y-2">
                        {documents.map((doc) => (
                            <div
                                key={doc.id}
                                className="flex justify-between items-center p-4 bg-gray-800/50 rounded-lg border border-gray-700 hover:border-green-500 transition"
                            >
                                <div className="flex-1">
                                    <p className="font-semibold text-gray-200 flex items-center gap-2">
                                        {getFileIcon(doc.file_type)} {doc.filename}
                                    </p>
                                    <p className="text-sm text-gray-400">
                                        {doc.file_type.toUpperCase()} • {formatFileSize(doc.file_size)} • {formatDate(doc.upload_date)}
                                    </p>
                                    <p className="text-xs text-gray-500 font-mono">{doc.id}</p>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => downloadDocument(doc.id, doc.filename)}
                                        className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-lg text-sm transition"
                                    >
                                        📥 Download
                                    </button>
                                    <button
                                        onClick={() => deleteDocument(doc.id)}
                                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-lg text-sm transition"
                                    >
                                        🗑️ Delete
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
