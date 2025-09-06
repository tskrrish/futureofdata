import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  Calendar, 
  AlertTriangle, 
  Shield, 
  Eye,
  Download,
  Trash2,
  RefreshCw,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react';

const VaultTab = ({ userId = 'demo-user' }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [dashboard, setDashboard] = useState({});

  // Mock data for demo (in production, this would come from API)
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      const mockDocuments = [
        {
          id: '1',
          document_name: 'Liability Waiver - Blue Ash YMCA',
          document_type: 'waiver',
          status: 'active',
          signed_date: '2024-01-15T10:00:00Z',
          expiry_date: '2025-01-15T10:00:00Z',
          is_expired: false,
          days_until_expiry: 45,
          file_size: 125000,
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: '2',
          document_name: 'CPR Certification',
          document_type: 'certification',
          status: 'active',
          signed_date: '2024-03-20T14:30:00Z',
          expiry_date: '2024-12-20T14:30:00Z',
          is_expired: false,
          days_until_expiry: 8,
          file_size: 89000,
          created_at: '2024-03-20T14:30:00Z'
        },
        {
          id: '3',
          document_name: 'Background Check',
          document_type: 'background_check',
          status: 'expired',
          signed_date: '2023-06-10T09:00:00Z',
          expiry_date: '2024-06-10T09:00:00Z',
          is_expired: true,
          days_until_expiry: -150,
          file_size: 67000,
          created_at: '2023-06-10T09:00:00Z'
        }
      ];

      const mockDashboard = {
        total_documents: 3,
        active_documents: 2,
        expiring_soon: 1,
        expired_documents: 1,
        documents_by_type: {
          waiver: 1,
          certification: 1,
          background_check: 1
        }
      };

      setDocuments(mockDocuments);
      setDashboard(mockDashboard);
      setLoading(false);
    }, 1000);
  }, []);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    
    // Mock upload process
    setTimeout(() => {
      const newDocument = {
        id: Date.now().toString(),
        document_name: file.name,
        document_type: 'waiver',
        status: 'active',
        signed_date: new Date().toISOString(),
        expiry_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1 year from now
        is_expired: false,
        days_until_expiry: 365,
        file_size: file.size,
        created_at: new Date().toISOString()
      };
      
      setDocuments(prev => [newDocument, ...prev]);
      setDashboard(prev => ({
        ...prev,
        total_documents: prev.total_documents + 1,
        active_documents: prev.active_documents + 1
      }));
      setUploading(false);
      setShowUploadForm(false);
    }, 2000);
  };

  const getDocumentIcon = (type) => {
    switch (type) {
      case 'waiver': return <Shield className="w-4 h-4" />;
      case 'certification': return <CheckCircle className="w-4 h-4" />;
      case 'background_check': return <FileText className="w-4 h-4" />;
      default: return <FileText className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status, daysUntilExpiry) => {
    if (status === 'expired') return 'text-red-600 bg-red-100';
    if (daysUntilExpiry <= 7) return 'text-red-600 bg-red-100';
    if (daysUntilExpiry <= 30) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getStatusText = (status, daysUntilExpiry) => {
    if (status === 'expired') return 'Expired';
    if (daysUntilExpiry <= 0) return 'Expired';
    if (daysUntilExpiry <= 7) return `Expires in ${daysUntilExpiry} days`;
    if (daysUntilExpiry <= 30) return `Expires in ${daysUntilExpiry} days`;
    return 'Active';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="mt-6 space-y-6">
        <div className="bg-white rounded-2xl border p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-8 bg-gray-200 rounded w-full"></div>
            <div className="h-8 bg-gray-200 rounded w-full"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 space-y-6">
      {/* Dashboard Cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl border p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Documents</p>
              <p className="text-2xl font-bold">{dashboard.total_documents}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Documents</p>
              <p className="text-2xl font-bold">{dashboard.active_documents}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Expiring Soon</p>
              <p className="text-2xl font-bold">{dashboard.expiring_soon}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <XCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Expired</p>
              <p className="text-2xl font-bold">{dashboard.expired_documents}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="bg-white rounded-2xl border">
        <div className="p-6 border-b">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">E-Sign Vault</h2>
              <p className="text-gray-600 text-sm">Secure storage for waivers, certifications, and documents</p>
            </div>
            <button
              onClick={() => setShowUploadForm(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Document</span>
            </button>
          </div>
        </div>

        {/* Upload Form */}
        {showUploadForm && (
          <div className="p-6 border-b bg-blue-50">
            <div className="max-w-md">
              <h3 className="font-medium mb-4">Upload New Document</h3>
              <input
                type="file"
                onChange={handleFileUpload}
                accept=".pdf,.jpg,.jpeg,.png"
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                disabled={uploading}
              />
              {uploading && (
                <div className="mt-2 text-sm text-blue-600 flex items-center space-x-2">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Uploading and encrypting document...</span>
                </div>
              )}
              <div className="mt-2 flex space-x-2">
                <button
                  onClick={() => setShowUploadForm(false)}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
                  disabled={uploading}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Documents List */}
        <div className="p-6">
          {documents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No documents uploaded yet</p>
              <p className="text-sm">Upload your first document to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      {getDocumentIcon(doc.document_type)}
                    </div>
                    <div>
                      <h4 className="font-medium">{doc.document_name}</h4>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span className="capitalize">{doc.document_type.replace('_', ' ')}</span>
                        <span>{formatFileSize(doc.file_size)}</span>
                        <span>Signed {new Date(doc.signed_date).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(doc.status, doc.days_until_expiry)}`}
                    >
                      {getStatusText(doc.status, doc.days_until_expiry)}
                    </span>

                    <div className="flex space-x-2">
                      <button
                        onClick={() => setSelectedDocument(doc)}
                        className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          // Mock download
                          console.log('Downloading document:', doc.document_name);
                        }}
                        className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                        title="Download"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Document Details Modal */}
      {selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b flex items-center justify-between">
              <h3 className="text-xl font-bold">Document Details</h3>
              <button
                onClick={() => setSelectedDocument(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Document Name</label>
                  <p className="mt-1">{selectedDocument.document_name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Type</label>
                  <p className="mt-1 capitalize">{selectedDocument.document_type.replace('_', ' ')}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Status</label>
                  <p className={`mt-1 px-2 py-1 rounded-full text-xs font-medium inline-block ${getStatusColor(selectedDocument.status, selectedDocument.days_until_expiry)}`}>
                    {getStatusText(selectedDocument.status, selectedDocument.days_until_expiry)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">File Size</label>
                  <p className="mt-1">{formatFileSize(selectedDocument.file_size)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Signed Date</label>
                  <p className="mt-1">{new Date(selectedDocument.signed_date).toLocaleDateString()}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Expiry Date</label>
                  <p className="mt-1">
                    {selectedDocument.expiry_date 
                      ? new Date(selectedDocument.expiry_date).toLocaleDateString()
                      : 'No expiry'
                    }
                  </p>
                </div>
              </div>

              {selectedDocument.days_until_expiry <= 30 && selectedDocument.days_until_expiry > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-600" />
                    <h4 className="font-medium text-yellow-800">Renewal Required Soon</h4>
                  </div>
                  <p className="text-yellow-700 text-sm mt-2">
                    This document expires in {selectedDocument.days_until_expiry} days. 
                    Please contact your volunteer coordinator to begin the renewal process.
                  </p>
                </div>
              )}

              {selectedDocument.is_expired && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <XCircle className="w-5 h-5 text-red-600" />
                    <h4 className="font-medium text-red-800">Document Expired</h4>
                  </div>
                  <p className="text-red-700 text-sm mt-2">
                    This document has expired and needs immediate renewal. 
                    Contact your volunteer coordinator to update your documentation.
                  </p>
                </div>
              )}
            </div>

            <div className="p-6 border-t bg-gray-50 flex space-x-3">
              <button
                onClick={() => console.log('Downloading document:', selectedDocument.document_name)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Download</span>
              </button>
              <button
                onClick={() => setSelectedDocument(null)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VaultTab;