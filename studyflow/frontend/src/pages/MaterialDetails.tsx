/**
 * Material Details Page
 *
 * View and edit details of a specific study material with:
 * - Document preview
 * - Extracted topics
 * - File information
 * - Generate Exercise section (inline, responsive)
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { materialsApi, exercisesApi, API_BASE_URL } from '../lib/api';
import mammoth from 'mammoth';
import {
  Zap,
  BookOpen,
  FileText,
  Download,
  ArrowLeft,
  Loader2,
  AlertCircle,
  Mic,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import VoiceChatPanel from '../components/VoiceChatPanel';

interface Material {
  id: string;
  title: string;
  subject: string;
  grade?: number;
  topics: string[];
  file_path?: string;  // Optional - may be undefined during upload
  file_type?: string;  // Optional - may be undefined initially
  file_size: number;
  chunks_count?: number;
  status: string;
  description?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  processed_at?: string;
}

export default function MaterialDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [material, setMaterial] = useState<Material | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Preview state
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewHtml, setPreviewHtml] = useState<string | null>(null); // For DOCX preview
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  // Generate Exercise State (inline section, not dialog)
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [generateSuccess, setGenerateSuccess] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    selectedTopics: [] as string[],
    difficulty: 'medium' as 'beginner' | 'easy' | 'medium' | 'hard' | 'expert',
    numQuestions: 10,
    questionTypes: ['multiple_choice'] as string[],
    timeLimitMinutes: 30,
  });

  // Voice Chat State
  const [showVoiceChatPanel, setShowVoiceChatPanel] = useState(false);

  useEffect(() => {
    if (id) {
      loadMaterial(id);
    }
  }, [id]);

  // Load preview when material is ready
  useEffect(() => {
    if (material?.status === 'completed') {
      const fileType = (material.file_type?.toLowerCase() ?? '') as string;
      const filePath = (material.file_path?.toLowerCase() ?? '') as string;

      // Check if it's a previewable file (PDF or DOCX)
      if (fileType === 'pdf' || (filePath && filePath.endsWith('.pdf')) ||
          fileType === 'docx' || (filePath && filePath.endsWith('.docx')) ||
          fileType === 'doc' || (filePath && filePath.endsWith('.doc'))) {
        loadPreview();
      }
    }
  }, [material?.id, material?.status]);

  const loadMaterial = async (materialId: string) => {
    try {
      setLoading(true);
      const data = await materialsApi.get(materialId);
      setMaterial(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load material');
    } finally {
      setLoading(false);
    }
  };

  const loadPreview = async () => {
    if (!material?.id) return;

    try {
      setPreviewLoading(true);
      setPreviewError(null);
      setPreviewUrl(null);
      setPreviewHtml(null);

      const token = localStorage.getItem('auth_token');
      const organizationId = localStorage.getItem('current_organization_id');

      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      if (organizationId) {
        headers['X-Organization-Id'] = organizationId;
      }

      const response = await fetch(`${API_BASE_URL}/materials/${material.id}/download`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to load preview: ${response.status}`);
      }

      const blob = await response.blob();

      // Determine file type
      const fileType = (material.file_type?.toLowerCase() ?? '') as string;
      const filePath = (material.file_path?.toLowerCase() ?? '') as string;

      // Handle PDF files
      if (fileType === 'pdf' || (filePath && filePath.endsWith('.pdf'))) {
        const url = window.URL.createObjectURL(blob);
        setPreviewUrl(url);
      }
      // Handle DOCX/DOC files
      else if (fileType === 'docx' || (filePath && filePath.endsWith('.docx')) ||
               fileType === 'doc' || (filePath && filePath.endsWith('.doc'))) {
        // Convert DOCX to HTML using mammoth
        const arrayBuffer = await blob.arrayBuffer();
        const result = await mammoth.convertToHtml({ arrayBuffer });
        setPreviewHtml(result.value);

        // Log any conversion warnings/errors
        if (result.messages.length > 0) {
          console.warn('Mammoth conversion messages:', result.messages);
        }
      }
    } catch (err) {
      console.error('Preview error:', err);
      setPreviewError(err instanceof Error ? err.message : 'Failed to load preview');
    } finally {
      setPreviewLoading(false);
    }
  };

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) {
        window.URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleDelete = async () => {
    if (!material || !confirm('Are you sure you want to delete this material? This action cannot be undone.')) {
      return;
    }

    try {
      setDeleting(true);
      await materialsApi.delete(material.id);
      navigate('/materials', { replace: true });
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete material');
      setDeleting(false);
    }
  };

  const handleGenerateExercise = async () => {
    if (!material) return;

    // Validation
    if (generateForm.selectedTopics.length === 0) {
      setGenerateError('Please select at least one topic');
      return;
    }
    if (generateForm.questionTypes.length === 0) {
      setGenerateError('Please select at least one question type');
      return;
    }
    if (generateForm.numQuestions < 1 || generateForm.numQuestions > 50) {
      setGenerateError('Number of questions must be between 1 and 50');
      return;
    }

    try {
      setGenerating(true);
      setGenerateError(null);
      setGenerateSuccess(false);

      const result = await exercisesApi.generate({
        material_id: material.id,
        num_questions: generateForm.numQuestions,
        difficulty: generateForm.difficulty,
        question_types: generateForm.questionTypes,
        topics: generateForm.selectedTopics,
        time_limit_minutes: generateForm.timeLimitMinutes || undefined,
      });

      setGenerateSuccess(true);
      // Navigate to the generated exercise after a brief delay
      setTimeout(() => {
        navigate(`/exercises/${result.id}/take`);
      }, 1500);
    } catch (err: any) {
      console.error('Failed to generate exercise:', err);
      setGenerateError(err.message || 'Failed to generate exercise');
    } finally {
      setGenerating(false);
    }
  };

  const toggleTopic = (topic: string) => {
    setGenerateForm((prev) => ({
      ...prev,
      selectedTopics: prev.selectedTopics.includes(topic)
        ? prev.selectedTopics.filter((t) => t !== topic)
        : [...prev.selectedTopics, topic],
    }));
  };

  const toggleQuestionType = (type: string) => {
    setGenerateForm((prev) => ({
      ...prev,
      questionTypes: prev.questionTypes.includes(type)
        ? prev.questionTypes.filter((t) => t !== type)
        : [...prev.questionTypes, type],
    }));
  };

  const resetGenerateForm = () => {
    setGenerateForm({
      selectedTopics: [],
      difficulty: 'medium',
      numQuestions: 10,
      questionTypes: ['multiple_choice'],
      timeLimitMinutes: 30,
    });
    setGenerateError(null);
    setGenerateSuccess(false);
  };

  const handleDownload = async () => {
    if (!material?.id) return;

    try {
      const token = localStorage.getItem('auth_token');
      const organizationId = localStorage.getItem('current_organization_id');

      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      if (organizationId) {
        headers['X-Organization-Id'] = organizationId;
      }

      const response = await fetch(`${API_BASE_URL}/materials/${material.id}/download`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error('Download failed');
      }

      // Get filename from Content-Disposition header or use material title
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = material.title || 'download';
      if (contentDisposition) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
        if (matches && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Download error:', err);
      alert('Failed to download file. Please try again.');
    }
  };


  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string) => {
    // Handle null/undefined status
    const safeStatus = status || 'pending';

    const statusConfig = {
      completed: {
        bg: 'bg-green-100',
        text: 'text-green-800',
        icon: '✓',
        description: 'Material has been successfully processed and is ready for use.',
      },
      processed: {
        bg: 'bg-green-100',
        text: 'text-green-800',
        icon: '✓',
        description: 'Material has been successfully processed and is ready for use.',
      },
      processing: {
        bg: 'bg-yellow-100',
        text: 'text-yellow-800',
        icon: '⟳',
        description: 'Material is currently being processed. This may take a few minutes.',
      },
      failed: {
        bg: 'bg-red-100',
        text: 'text-red-800',
        icon: '✗',
        description: 'Processing failed. Please check the error message below.',
      },
      pending: {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        icon: '○',
        description: 'Material is waiting to be processed.',
      },
    };

    const config = statusConfig[safeStatus as keyof typeof statusConfig] || statusConfig.pending;

    return (
      <div className={`${config.bg} rounded-lg p-4`}>
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-xl">{config.icon}</span>
          <span className={`font-semibold ${config.text}`}>
            {safeStatus.charAt(0).toUpperCase() + safeStatus.slice(1)}
          </span>
        </div>
        <p className={`text-sm ${config.text}`}>{config.description}</p>
      </div>
    );
  };

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading material...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error || !material) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <button
              onClick={() => navigate('/materials')}
              className="text-gray-600 hover:text-gray-900"
            >
              ← Back to Library
            </button>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-900 mb-2">Error Loading Material</h2>
            <p className="text-red-800">{error || 'Material not found'}</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
          {/* Back button and title */}
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <Button
              variant="outline"
              onClick={() => navigate('/materials')}
              className="gap-2 shrink-0"
              size="sm"
            >
              <ArrowLeft size={18} />
              <span className="hidden sm:inline">Back</span>
            </Button>
            <div className="min-w-0 flex-1">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 truncate">
                {material?.title || 'Untitled'}
              </h1>
              <p className="text-xs sm:text-sm text-gray-600">
                {material?.subject || 'Unknown Subject'} {material?.grade && `• Grade ${material.grade}`}
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <Download size={16} />
              <span className="hidden sm:inline">Download</span>
            </button>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Preview & Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Document Preview Section */}
            <Card className="p-4 sm:p-6">
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                Document Preview
              </h2>
              {material.status === 'completed' ? (
                <div className="border-2 border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                  {(() => {
                    const fileType = (material.file_type?.toLowerCase() ?? '') as string;
                    const filePath = (material.file_path?.toLowerCase() ?? '') as string;
                    const isPreviewable = fileType === 'pdf' || (filePath && filePath.endsWith('.pdf')) ||
                                        fileType === 'docx' || (filePath && filePath.endsWith('.docx')) ||
                                        fileType === 'doc' || (filePath && filePath.endsWith('.doc'));

                    if (!isPreviewable) {
                      return (
                        <div className="flex flex-col items-center justify-center h-[400px] text-center p-8">
                          <FileText className="h-16 w-16 text-gray-400 mb-4" />
                          <p className="text-gray-600 mb-4">
                            Preview not available for {material.file_type?.toUpperCase() || 'this file type'}
                          </p>
                          <p className="text-sm text-gray-500 mb-4">
                            This file type cannot be previewed in the browser. Download it to view on your device.
                          </p>
                          <button
                            onClick={handleDownload}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                          >
                            <Download size={16} />
                            Download to View
                          </button>
                        </div>
                      );
                    }

                    return (
                      <div className="w-full h-[calc(100vh-400px)] sm:h-[calc(100vh-300px)] min-h-[400px] sm:min-h-[600px] max-h-[1200px]">
                        {previewLoading ? (
                          <div className="flex flex-col items-center justify-center h-full">
                            <Loader2 className="h-8 w-8 sm:h-12 sm:w-12 text-blue-600 animate-spin mb-4" />
                            <p className="text-sm sm:text-base text-gray-600">Loading preview...</p>
                          </div>
                        ) : previewError ? (
                          <div className="flex flex-col items-center justify-center h-full text-center p-8">
                            <AlertCircle className="h-16 w-16 text-red-400 mb-4" />
                            <p className="text-gray-900 font-medium mb-2">Failed to load preview</p>
                            <p className="text-sm text-gray-600 mb-4">{previewError}</p>
                            <div className="flex gap-2">
                              <button
                                onClick={loadPreview}
                                className="flex items-center gap-2 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors font-medium"
                              >
                                <Loader2 size={16} />
                                Try Again
                              </button>
                              <button
                                onClick={handleDownload}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                              >
                                <Download size={16} />
                                Download Instead
                              </button>
                            </div>
                          </div>
                        ) : previewUrl ? (
                          // PDF Preview
                          <iframe
                            src={previewUrl}
                            className="w-full h-full"
                            title="Document Preview"
                          />
                        ) : previewHtml ? (
                          // DOCX Preview
                          <div
                            className="w-full h-full overflow-auto bg-white p-8"
                            dangerouslySetInnerHTML={{ __html: previewHtml }}
                          />
                        ) : (
                          <div className="flex flex-col items-center justify-center h-full">
                            <FileText className="h-16 w-16 text-gray-400 mb-4" />
                            <p className="text-gray-600">No preview available</p>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              ) : (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                  <Loader2 className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
                  <p className="text-gray-600">Document is being processed...</p>
                  <p className="text-sm text-gray-500 mt-2">Preview will be available once processing is complete</p>
                </div>
              )}
            </Card>

            {/* Topics Section */}
            {material.topics && material.topics.length > 0 && (
              <Card className="p-4 sm:p-6">
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-blue-600" />
                  Topics Covered
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  {material.topics.length} {material.topics.length === 1 ? 'topic' : 'topics'} extracted from this document
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
                  {material.topics.map((topic, index) => (
                    <div
                      key={index}
                      className="px-3 py-2 sm:px-4 sm:py-3 bg-blue-50 text-blue-800 rounded-lg text-xs sm:text-sm font-medium border border-blue-200 hover:bg-blue-100 transition-colors text-center"
                    >
                      {topic}
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* File Information */}
            <Card className="p-4 sm:p-6">
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4">File Information</h2>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="border-b sm:border-b-0 pb-3 sm:pb-0">
                  <dt className="text-xs sm:text-sm font-medium text-gray-600 mb-1">File Type</dt>
                  <dd className="text-sm sm:text-base text-gray-900 uppercase font-mono">{material.file_type}</dd>
                </div>
                <div className="border-b sm:border-b-0 pb-3 sm:pb-0">
                  <dt className="text-xs sm:text-sm font-medium text-gray-600 mb-1">File Size</dt>
                  <dd className="text-sm sm:text-base text-gray-900">{formatFileSize(material.file_size)}</dd>
                </div>
                {material.chunks_count && material.chunks_count > 0 && (
                  <div className="border-b sm:border-b-0 pb-3 sm:pb-0">
                    <dt className="text-xs sm:text-sm font-medium text-gray-600 mb-1">Content Chunks</dt>
                    <dd className="text-sm sm:text-base text-gray-900">{material.chunks_count} chunks</dd>
                  </div>
                )}
                <div className="border-b sm:border-b-0 pb-3 sm:pb-0">
                  <dt className="text-xs sm:text-sm font-medium text-gray-600 mb-1">Status</dt>
                  <dd className="mt-1">
                    {getStatusBadge(material.status)}
                  </dd>
                </div>
                <div className="border-b sm:border-b-0 pb-3 sm:pb-0">
                  <dt className="text-xs sm:text-sm font-medium text-gray-600 mb-1">Uploaded</dt>
                  <dd className="text-xs sm:text-sm text-gray-900">{formatDate(material.created_at)}</dd>
                </div>
                {material.processed_at && (
                  <div>
                    <dt className="text-xs sm:text-sm font-medium text-gray-600 mb-1">Processed</dt>
                    <dd className="text-xs sm:text-sm text-gray-900">{formatDate(material.processed_at)}</dd>
                  </div>
                )}
              </dl>
            </Card>
          </div>

          {/* Right Column - Generate Exercise */}
          <div className="lg:col-span-1">
            <Card className="p-4 sm:p-6">
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <Zap className="h-5 w-5 text-blue-600" />
                Generate Exercise
              </h2>
              <p className="text-xs sm:text-sm text-gray-600 mb-4 sm:mb-6">
                Create AI-generated questions from this material
              </p>

              {material.status !== 'completed' ? (
                <div className="text-center p-8 border-2 border-dashed border-gray-300 rounded-lg">
                  <Loader2 className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-3" />
                  <p className="text-sm text-gray-600">Processing material...</p>
                  <p className="text-xs text-gray-500 mt-2">
                    Exercise generation will be available once processing is complete
                  </p>
                </div>
              ) : (
                <div className="space-y-4 sm:space-y-6">
                  {/* Success Message */}
                  {generateSuccess && (
                    <div className="p-3 sm:p-4 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-xs sm:text-sm text-green-800 font-medium">Exercise generated successfully!</p>
                      <p className="text-xs text-green-600 mt-1">Redirecting...</p>
                    </div>
                  )}

                  {/* Error Message */}
                  {generateError && (
                    <div className="p-3 sm:p-4 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-xs sm:text-sm text-red-800">{generateError}</p>
                    </div>
                  )}

                  {/* Topics Selection */}
                  {material.topics && material.topics.length > 0 ? (
                    <div>
                      <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
                        Topics <span className="text-red-500">*</span>
                      </label>
                      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                        {material.topics.map((topic) => (
                          <label
                            key={topic}
                            className={`flex items-center p-2 sm:p-3 border-2 rounded-lg cursor-pointer transition-colors ${
                              generateForm.selectedTopics.includes(topic)
                                ? 'border-blue-600 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={generateForm.selectedTopics.includes(topic)}
                              onChange={() => toggleTopic(topic)}
                              className="mr-2 sm:mr-3 h-4 w-4 text-blue-600 rounded shrink-0"
                            />
                            <span className="text-xs sm:text-sm font-medium text-gray-900 break-words">{topic}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 sm:p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-xs sm:text-sm text-blue-800">
                        <strong>Note:</strong> This material has no specific topics defined.
                        The exercise will be generated from the entire material content.
                      </p>
                    </div>
                  )}

                  {/* Difficulty Selection */}
                  <div>
                    <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
                      Difficulty
                    </label>
                    <select
                      value={generateForm.difficulty}
                      onChange={(e) =>
                        setGenerateForm((prev) => ({ ...prev, difficulty: e.target.value as any }))
                      }
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                    >
                      <option value="beginner">Beginner</option>
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                      <option value="expert">Expert</option>
                    </select>
                  </div>

                  {/* Number of Questions and Time Limit - Side by Side on larger screens */}
                  <div className="grid grid-cols-2 gap-3 sm:gap-4">
                    <div>
                      <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
                        Questions
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={generateForm.numQuestions}
                        onChange={(e) =>
                          setGenerateForm((prev) => ({
                            ...prev,
                            numQuestions: parseInt(e.target.value) || 0,
                          }))
                        }
                        className="w-full px-2 sm:px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
                        Time (min)
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={generateForm.timeLimitMinutes}
                        onChange={(e) =>
                          setGenerateForm((prev) => ({
                            ...prev,
                            timeLimitMinutes: parseInt(e.target.value) || 0,
                          }))
                        }
                        className="w-full px-2 sm:px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                      />
                    </div>
                  </div>

                  {/* Question Types */}
                  <div>
                    <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
                      Question Types
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { value: 'multiple_choice', label: 'Multiple Choice' },
                        { value: 'short_answer', label: 'Short Answer' },
                        { value: 'essay', label: 'Essay' },
                        { value: 'true_false', label: 'True/False' },
                      ].map((type) => (
                        <label
                          key={type.value}
                          className={`flex items-center p-2 border-2 rounded-lg cursor-pointer transition-colors ${
                            generateForm.questionTypes.includes(type.value)
                              ? 'border-blue-600 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={generateForm.questionTypes.includes(type.value)}
                            onChange={() => toggleQuestionType(type.value)}
                            className="mr-2 h-4 w-4 text-blue-600 rounded shrink-0"
                          />
                          <span className="text-xs sm:text-sm">{type.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Generate Button */}
                  <button
                    onClick={handleGenerateExercise}
                    disabled={generating || generateSuccess}
                    className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        Generating...
                      </>
                    ) : generateSuccess ? (
                      <>Success!</>
                    ) : (
                      <>
                        <Zap className="h-5 w-5" />
                        Generate Exercise
                      </>
                    )}
                  </button>
                </div>
              )}
            </Card>

            {/* Voice Chat Section */}
            <Card className="p-4 sm:p-6 mt-6">
              <div className="space-y-4">
                <div>
                  <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <Mic className="h-5 w-5 sm:h-6 sm:w-6 text-purple-600 flex-shrink-0" />
                    <span>Voice Chat</span>
                  </h2>
                  <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">
                    Ask questions about this material using your voice. Get instant answers based on the document content.
                  </p>
                </div>

                <button
                  onClick={() => setShowVoiceChatPanel(true)}
                  disabled={material.status !== 'completed'}
                  className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 sm:py-3 rounded-lg text-sm sm:text-base font-medium transition-all duration-200 ${
                    material.status === 'completed'
                      ? 'bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white shadow-sm hover:shadow-md'
                      : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  <Mic className="h-4 w-4 sm:h-5 sm:w-5" />
                  <span>Start Voice Chat</span>
                </button>

                {material.status !== 'completed' && (
                  <p className="text-xs text-gray-500 text-center leading-tight">
                    Material must be processed before using voice chat
                  </p>
                )}
              </div>
            </Card>
          </div>
        </div>
      </main>

      {/* Voice Chat Panel */}
      {material && (
        <VoiceChatPanel
          materialId={material.id}
          materialTitle={material.title}
          isOpen={showVoiceChatPanel}
          onClose={() => setShowVoiceChatPanel(false)}
        />
      )}
    </div>
  );
}

function getStatusBadge(status: string) {
  const safeStatus = status || 'pending';
  const config: Record<string, { bg: string; text: string; label: string }> = {
    completed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Completed' },
    processed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Processed' },
    processing: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Processing' },
    failed: { bg: 'bg-red-100', text: 'text-red-800', label: 'Failed' },
    pending: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Pending' },
  };

  const c = config[safeStatus] || config.pending;

  return (
    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  );
}
