/**
 * Author Upload Page.
 *
 * Interface for authors to upload new books.
 * Similar to admin upload but uses author endpoints.
 */

import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Upload,
  File,
  CheckCircle,
  XCircle,
  Loader,
  AlertCircle,
  BookOpen,
  User,
  FileText,
  Image,
  Clock,
  Mic,
  Eye,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import toast from 'react-hot-toast';

interface UploadedBook {
  book_id: string;
  title: string;
  status: 'processing' | 'ready' | 'error';
  message: string;
  chapters_extracted: number;
  processing_time_seconds?: number;
  uploaded_at: string;
  processing_stage?: string;
  processing_progress?: number;
  processing_message?: string;
}

export default function AuthorUploadPage() {
	useEffect(() => {
		document.title = 'Upload Book - InkWave';
	}, []);

  const navigate = useNavigate();
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingBookId, setProcessingBookId] = useState<string | null>(null);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [processingStage, setProcessingStage] = useState('');
  const [processingMessage, setProcessingMessage] = useState('');
  const [recentUploads, setRecentUploads] = useState<UploadedBook[]>([]);

  // Form state
  const [file, setFile] = useState<File | null>(null);
  const [coverImage, setCoverImage] = useState<File | null>(null);
  const [coverPreview, setCoverPreview] = useState<string>('');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [description, setDescription] = useState('');
  const [coverUrl, setCoverUrl] = useState('');
  const [durationMinutes, setDurationMinutes] = useState('');
  const [narrator, setNarrator] = useState('');
  const [useAiChapters, setUseAiChapters] = useState(true);

  // Duplicate check state
  const [checkingDuplicate, setCheckingDuplicate] = useState(false);
  const [duplicateResults, setDuplicateResults] = useState<{
    exists: boolean;
    duplicates: any[];
    similar: any[];
    total_count: number;
    message: string;
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const coverImageInputRef = useRef<HTMLInputElement>(null);

  // Check for duplicate titles with debouncing
  useEffect(() => {
    const checkDuplicate = async () => {
      if (!title || title.trim().length < 3) {
        setDuplicateResults(null);
        return;
      }

      try {
        setCheckingDuplicate(true);
        const response = await api.books.checkDuplicateTitle(title.trim());
        setDuplicateResults(response.data);
      } catch (error) {
        console.error('Error checking duplicate:', error);
        setDuplicateResults(null);
      } finally {
        setCheckingDuplicate(false);
      }
    };

    // Debounce: wait 500ms after user stops typing
    const timeoutId = setTimeout(checkDuplicate, 500);
    return () => clearTimeout(timeoutId);
  }, [title]);

  // Start polling for processing progress
  const startProcessingPolling = (bookId: string, bookTitle: string) => {
    let pollIntervalRef: NodeJS.Timeout | null = null;

    const pollStatus = async () => {
      try {
        const response = await api.books.getProcessingStatus(bookId);
        const status = response.data;

        console.log(`[Processing] ${bookId}: stage=${status.processing_stage}, progress=${status.processing_progress}, status=${status.status}`);

        // Only update progress if it's greater than current (avoid going backwards)
        const newProgress = status.processing_progress ?? 0;
        setProcessingProgress(prev => {
          // Don't go backwards - always use the higher value
          return Math.max(prev, newProgress);
        });
        setProcessingStage(status.processing_stage || '');
        setProcessingMessage(status.processing_message || 'Processing...');

        // Update recent uploads
        setRecentUploads(prev => prev.map(book =>
          book.book_id === bookId
            ? {
                ...book,
                status: status.status,
                processing_stage: status.processing_stage,
                processing_progress: status.processing_progress,
                processing_message: status.processing_message,
              }
            : book
        ));

        // Stop polling if processing is complete or errored
        if (status.status === 'ready' || status.status === 'error') {
          if (pollIntervalRef) {
            clearInterval(pollIntervalRef);
          }
          setProcessingBookId(null);
          if (status.status === 'ready') {
            setProcessingProgress(100);
            toast.success(`Book "${bookTitle}" is ready!`);
            setTimeout(() => {
              resetForm();
            }, 2000);
          } else {
            toast.error(`Processing failed: ${status.processing_error || 'Unknown error'}`);
          }
          return true; // Signal to stop polling
        }
        return false;
      } catch (error) {
        console.error('Failed to poll processing status:', error);
        if (pollIntervalRef) {
          clearInterval(pollIntervalRef);
        }
        return true; // Stop on error
      }
    };

    // Immediate first poll
    pollStatus().then((shouldStop) => {
      if (!shouldStop) {
        // Start interval polling only if not already complete
        pollIntervalRef = setInterval(async () => {
          const shouldStop = await pollStatus();
          if (shouldStop && pollIntervalRef) {
            clearInterval(pollIntervalRef);
            pollIntervalRef = null;
          }
        }, 2000);
      }
    });
  };

  // Poll for processing status of recent uploads (legacy - for existing uploads)
  useEffect(() => {
    const processingBooks = recentUploads.filter(b => b.status === 'processing' && b.book_id !== processingBookId);
    if (processingBooks.length === 0) return;

    const interval = setInterval(async () => {
      for (const book of processingBooks) {
        try {
          const response = await api.books.getProcessingStatus(book.book_id);
          const status = response.data.status;

          if (status !== 'processing') {
            setRecentUploads(prev => prev.map(b =>
              b.book_id === book.book_id
                ? { ...b, status, message: status === 'ready' ? 'Book is ready!' : 'Processing failed' }
                : b
            ));
          }
        } catch (error) {
          console.error('Failed to check status:', error);
        }
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [recentUploads]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    const allowedTypes = ['application/pdf', 'application/epub+zip'];
    const maxSize = 100 * 1024 * 1024; // 100MB

    if (!allowedTypes.includes(selectedFile.type)) {
      toast.error('Invalid file type. Please upload a PDF or EPUB file.');
      return;
    }

    if (selectedFile.size > maxSize) {
      toast.error('File too large. Maximum size is 100MB.');
      return;
    }

    setFile(selectedFile);
    // Auto-populate title if empty
    if (!title) {
      const fileName = selectedFile.name.replace(/\.(pdf|epub)$/i, '');
      setTitle(fileName);
    }
  };

  const handleCoverImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetCoverImage(selectedFile);
    }
  };

  const validateAndSetCoverImage = (selectedFile: File) => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    const maxSize = 5 * 1024 * 1024; // 5MB

    if (!allowedTypes.includes(selectedFile.type)) {
      toast.error('Invalid image format. Please upload JPG, PNG, or WebP.');
      return;
    }

    if (selectedFile.size > maxSize) {
      toast.error('Image too large. Maximum size is 5MB.');
      return;
    }

    setCoverImage(selectedFile);

    // Generate preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setCoverPreview(reader.result as string);
    };
    reader.readAsDataURL(selectedFile);

    // Clear coverUrl if using file upload
    setCoverUrl('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      toast.error('Please select a file to upload.');
      return;
    }

    if (!title || !author || !description) {
      toast.error('Please fill in all required fields.');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('author', author);
      formData.append('description', description);

      // Add cover image or URL
      if (coverImage) {
        formData.append('cover_image', coverImage);
      } else if (coverUrl) {
        formData.append('cover_url', coverUrl);
      }

      if (durationMinutes) formData.append('duration_minutes', durationMinutes);
      if (narrator) formData.append('narrator', narrator);
      formData.append('use_ai_chapters', useAiChapters.toString());

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) return prev;
          return prev + 10;
        });
      }, 200);

      const response = await api.books.upload(formData);

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Add to recent uploads
      const uploadedBook: UploadedBook = {
        ...response.data,
        uploaded_at: new Date().toISOString(),
        processing_stage: 'uploading',
        processing_progress: 100,
      };
      setRecentUploads([uploadedBook, ...recentUploads]);

      // Start tracking processing progress
      if (response.data.status === 'processing') {
        setProcessingBookId(response.data.book_id);
        // Use the processing progress from backend response (should be 10 initially)
        const initialProgress = response.data.processing_progress ?? 10;
        const initialStage = response.data.processing_stage || 'uploading';
        const initialMessage = response.data.processing_message || 'Files uploaded, starting text extraction...';
        
        console.log(`[Upload Complete] Setting initial processing state:`, {
          progress: initialProgress,
          stage: initialStage,
          message: initialMessage
        });
        
        setProcessingProgress(initialProgress);
        setProcessingStage(initialStage);
        setProcessingMessage(initialMessage);
        
        // Start polling immediately - first poll will happen right away
        startProcessingPolling(response.data.book_id, title);
      } else {
        toast.success(`Book "${title}" uploaded successfully!`);
        setTimeout(() => {
          resetForm();
        }, 1000);
      }

    } catch (error: any) {
      console.error('Upload failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload book. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const getStageProgress = (currentStage: string, overallProgress: number, stageIndex: number): number => {
    const stages = ['initializing', 'extracting', 'chunking', 'embedding', 'finalizing'];
    const currentIndex = stages.indexOf(currentStage);
    
    if (currentIndex > stageIndex) return 100;
    if (currentIndex < stageIndex) return 0;
    
    // Current stage - calculate progress within stage
    const stageRanges = [0, 20, 60, 80, 95, 100];
    const stageStart = stageRanges[stageIndex];
    const stageEnd = stageRanges[stageIndex + 1];
    const stageRange = stageEnd - stageStart;
    const progressInStage = Math.max(0, Math.min(100, ((overallProgress - stageStart) / stageRange) * 100));
    
    return progressInStage;
  };

  const resetForm = () => {
    setFile(null);
    setCoverImage(null);
    setCoverPreview('');
    setTitle('');
    setAuthor('');
    setDescription('');
    setCoverUrl('');
    setDurationMinutes('');
    setNarrator('');
    setUseAiChapters(false);
    setUploadProgress(0);
    setProcessingBookId(null);
    setProcessingProgress(0);
    setProcessingStage('');
    setProcessingMessage('');
    setDuplicateResults(null);
    setCheckingDuplicate(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (coverImageInputRef.current) {
      coverImageInputRef.current.value = '';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'processing':
        return <Loader className="w-5 h-5 text-yellow-400 animate-spin" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'processing':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'error':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 sm:gap-4 min-w-0">
              <Link
                to="/my-books"
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors flex-shrink-0"
              >
                <ArrowLeft className="w-5 h-5 sm:w-6 sm:h-6 text-gray-400" />
              </Link>
              <div className="min-w-0">
                <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-white flex items-center gap-2 sm:gap-3">
                  <Upload className="w-6 h-6 sm:w-8 sm:h-8 text-purple-400 flex-shrink-0" />
                  <span className="truncate">Upload Book</span>
                </h1>
                <p className="text-gray-400 mt-1 text-sm sm:text-base hidden sm:block">
                  Upload and publish your book as an audiobook
                </p>
              </div>
            </div>

            <Link
              to="/my-books"
              className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors flex-shrink-0 text-sm sm:text-base"
            >
              <Eye className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="hidden sm:inline">View My Books</span>
              <span className="sm:hidden">My Books</span>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
          {/* Upload Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-4 sm:p-6"
          >
            <h2 className="text-lg sm:text-xl font-bold text-white mb-4 sm:mb-6">Upload New Book</h2>

            <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
              {/* File Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-4 sm:p-8 text-center cursor-pointer transition-all ${
                  dragging
                    ? 'border-purple-500 bg-purple-500/10'
                    : file
                    ? 'border-green-500 bg-green-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.epub"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <File className="w-8 h-8 text-green-400" />
                    <div>
                      <p className="text-white font-semibold">{file.name}</p>
                      <p className="text-gray-400 text-sm">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-white font-semibold mb-1">
                      Drop your file here or click to browse
                    </p>
                    <p className="text-gray-400 text-sm">
                      Supports PDF and EPUB (max 100MB)
                    </p>
                  </div>
                )}
              </div>

              {/* Combined Upload + Processing Progress - Seamless transition */}
              {(uploading || processingBookId) && (
                <div className="mt-4 space-y-3 p-4 bg-gray-800/50 rounded-lg border border-purple-500/20">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-300 font-medium">
                      {processingBookId 
                        ? (processingMessage || 'Processing book...')
                        : 'Uploading file...'}
                    </span>
                    <span className="text-purple-400 font-semibold">
                      {processingBookId ? processingProgress : uploadProgress}%
                    </span>
                  </div>
                  
                  {/* Progress Bar - Smooth transition from upload to processing */}
                  <div className="w-full bg-gray-700 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-purple-500 to-pink-500 h-full transition-all duration-500 ease-out"
                      style={{ 
                        width: processingBookId 
                          ? `${processingProgress}%` 
                          : `${uploadProgress}%` 
                      }}
                    />
                  </div>
                  
                  {/* Stage Indicator - Only show during processing */}
                  {processingBookId && processingStage && (
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <Loader className="w-3 h-3 animate-spin" />
                      <span className="capitalize">{processingStage.replace('_', ' ')}</span>
                    </div>
                  )}
                  
                  {/* Stage Steps - Only show during processing */}
                  {processingBookId && (
                    <div className="grid grid-cols-5 gap-1 mt-2">
                      {['initializing', 'extracting', 'chunking', 'embedding', 'finalizing'].map((stage, idx) => {
                        const stageProgress = getStageProgress(processingStage, processingProgress, idx);
                        return (
                          <div
                            key={stage}
                            className={`h-1 rounded transition-all ${
                              stageProgress === 100
                                ? 'bg-green-500'
                                : stageProgress > 0
                                ? 'bg-purple-500'
                                : 'bg-gray-700'
                            }`}
                            style={{ width: '100%' }}
                            title={stage}
                          />
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* Title */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
                  <BookOpen className="w-4 h-4" />
                  Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter book title"
                  className={`w-full px-4 py-3 bg-gray-900/50 border rounded-lg text-white placeholder-gray-500 focus:outline-none transition-colors ${
                    duplicateResults && duplicateResults.exists
                      ? 'border-orange-500 focus:border-orange-400'
                      : 'border-gray-700 focus:border-purple-500'
                  }`}
                  required
                />

                {/* Duplicate Check Results */}
                {checkingDuplicate && (
                  <div className="mt-2 flex items-center gap-2 text-sm text-gray-400">
                    <Loader className="w-4 h-4 animate-spin" />
                    Checking for duplicates...
                  </div>
                )}

                {duplicateResults && duplicateResults.total_count > 0 && (
                  <div className="mt-3 space-y-2">
                    {/* Exact matches warning */}
                    {duplicateResults.exists && duplicateResults.duplicates.length > 0 && (
                      <div className="p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-orange-400 mb-1">
                              {duplicateResults.duplicates.length} book(s) with this exact title found!
                            </p>
                            <div className="space-y-1.5">
                              {duplicateResults.duplicates.map((book: any) => (
                                <div key={book.book_id} className="text-xs text-gray-300 bg-gray-900/50 p-2 rounded">
                                  <div className="flex justify-between items-start">
                                    <div>
                                      <p className="font-medium">{book.title}</p>
                                      <p className="text-gray-400">by {book.author}</p>
                                    </div>
                                    {book.is_own_book && (
                                      <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded">
                                        Your book
                                      </span>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                            <p className="text-xs text-gray-400 mt-2">
                              Consider using a different title to avoid confusion.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Similar titles info */}
                    {duplicateResults.similar.length > 0 && (
                      <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-blue-400 mb-1">
                              {duplicateResults.similar.length} similar title(s) found
                            </p>
                            <div className="space-y-1.5">
                              {duplicateResults.similar.slice(0, 3).map((book: any) => (
                                <div key={book.book_id} className="text-xs text-gray-300">
                                  <span className="font-medium">{book.title}</span>
                                  <span className="text-gray-400"> by {book.author}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Author */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
                  <User className="w-4 h-4" />
                  Author *
                </label>
                <input
                  type="text"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  placeholder="Enter author name"
                  className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
                  <FileText className="w-4 h-4" />
                  Description *
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter book description"
                  rows={4}
                  className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors resize-none"
                  required
                />
              </div>

              {/* Cover Image Upload */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
                  <Image className="w-4 h-4" />
                  Cover Image (optional)
                </label>

                <div className="flex gap-4">
                  {/* Cover preview or upload button */}
                  <div
                    onClick={() => coverImageInputRef.current?.click()}
                    className="w-32 h-48 border-2 border-dashed border-gray-600 hover:border-purple-500 rounded-lg flex items-center justify-center cursor-pointer transition-colors overflow-hidden bg-gray-900/50"
                  >
                    {coverPreview ? (
                      <img
                        src={coverPreview}
                        alt="Cover preview"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="text-center p-4">
                        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-xs text-gray-400">Upload Cover</p>
                      </div>
                    )}
                  </div>

                  <input
                    ref={coverImageInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleCoverImageSelect}
                    className="hidden"
                  />

                  {/* Cover URL alternative */}
                  <div className="flex-1">
                    <p className="text-xs text-gray-400 mb-2">Or paste image URL:</p>
                    <input
                      type="url"
                      value={coverUrl}
                      onChange={(e) => {
                        setCoverUrl(e.target.value);
                        if (e.target.value) {
                          setCoverImage(null);
                          setCoverPreview('');
                        }
                      }}
                      placeholder="https://example.com/cover.jpg"
                      disabled={!!coverImage}
                      className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    />
                    <p className="text-xs text-gray-500 mt-1">JPG, PNG, or WebP (max 5MB)</p>
                  </div>
                </div>

                {(coverImage || coverPreview) && (
                  <button
                    type="button"
                    onClick={() => {
                      setCoverImage(null);
                      setCoverPreview('');
                      if (coverImageInputRef.current) {
                        coverImageInputRef.current.value = '';
                      }
                    }}
                    className="mt-2 text-sm text-red-400 hover:text-red-300"
                  >
                    Remove cover image
                  </button>
                )}
              </div>

              {/* Duration */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
                  <Clock className="w-4 h-4" />
                  Estimated Duration (minutes, optional)
                </label>
                <input
                  type="number"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(e.target.value)}
                  placeholder="120"
                  min="0"
                  className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>

              {/* Narrator */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-2">
                  <Mic className="w-4 h-4" />
                  Narrator (optional)
                </label>
                <input
                  type="text"
                  value={narrator}
                  onChange={(e) => setNarrator(e.target.value)}
                  placeholder="AI Voice - Default"
                  className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>

              {/* AI Chapter Detection Toggle */}
              <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500/20 rounded-lg">
                      <Sparkles className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <label className="text-sm font-semibold text-white cursor-pointer">
                        AI-Enhanced Chapter Detection
                      </label>
                      <p className="text-xs text-gray-400 mt-0.5">
                        Uses Gemini AI for books with non-standard chapter formats
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={useAiChapters}
                    onClick={() => setUseAiChapters(!useAiChapters)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800 ${
                      useAiChapters ? 'bg-purple-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        useAiChapters ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
                {useAiChapters && (
                  <p className="text-xs text-purple-300 mt-3 pl-12">
                    Recommended for creative chapter titles, multi-language content, or unique formatting.
                  </p>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={!file || uploading || !!processingBookId}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {(uploading || processingBookId) ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      {processingBookId ? 'Processing...' : 'Uploading...'}
                    </>
                  ) : (
                    'Upload Book'
                  )}
                </button>
                <button
                  type="button"
                  onClick={resetForm}
                  disabled={uploading}
                  className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
                >
                  Reset
                </button>
              </div>
            </form>
          </motion.div>

          {/* Recent Uploads */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6"
          >
            <h2 className="text-xl font-bold text-white mb-6">Recent Uploads</h2>

            {recentUploads.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">No recent uploads</p>
                <p className="text-gray-500 text-sm mt-1">
                  Uploaded books will appear here
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {recentUploads.map((book, index) => (
                  <motion.div
                    key={book.book_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="bg-gray-900/50 border border-gray-700 rounded-lg p-4"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="font-semibold text-white mb-1">{book.title}</h3>
                        <p className="text-sm text-gray-400">{book.message}</p>
                      </div>
                      {getStatusIcon(book.status)}
                    </div>

                    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-semibold ${getStatusColor(book.status)}`}>
                      {book.status.toUpperCase()}
                    </div>

                    <div className="mt-3 flex items-center justify-between">
                      <div className="flex items-center gap-4 text-sm text-gray-400">
                        <span>{book.chapters_extracted} chapters</span>
                        {book.processing_time_seconds && (
                          <span>
                            {book.processing_time_seconds.toFixed(1)}s processing
                          </span>
                        )}
                      </div>

                      {book.status === 'ready' && (
                        <button
                          onClick={() => navigate(`/book/${book.book_id}`)}
                          className="text-sm text-purple-400 hover:text-purple-300"
                        >
                          View Book
                        </button>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        </div>

        {/* Info Box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-purple-900/20 border border-purple-500/30 rounded-xl p-6 mt-8"
        >
          <div className="flex gap-4">
            <AlertCircle className="w-6 h-6 text-purple-400 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-bold text-white mb-2">Upload Guidelines</h3>
              <ul className="text-gray-300 space-y-2 text-sm">
                <li>Supported formats: PDF and EPUB (max 100MB)</li>
                <li>Processing includes automatic chapter extraction and embedding generation for Q&A</li>
                <li>Books are processed asynchronously and will be available shortly</li>
                <li>Fill in all required fields (title, author, description) for best results</li>
                <li>Cover images improve discoverability in the library</li>
                <li>You can manage and edit your books from the "My Books" page</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
