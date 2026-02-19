/**
 * Material Upload Page
 *
 * Allows admins to upload study materials with drag-and-drop functionality.
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { materialsApi } from '../lib/api';

interface UploadFormData {
  title: string;
  subject: string;
  grade: number;
  description: string;
  topics: string[];
}

export default function MaterialUpload() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState<UploadFormData>({
    title: '',
    subject: '',
    grade: 10,
    description: '',
    topics: [],
  });
  const [topicInput, setTopicInput] = useState('');

  // Handle drag events
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  }, []);

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  // Validate and set file
  const validateAndSetFile = (selectedFile: File) => {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Invalid file type. Please upload PDF, DOCX, or TXT files.');
      return;
    }

    const maxSize = 100 * 1024 * 1024; // 100MB
    if (selectedFile.size > maxSize) {
      setError('File too large. Maximum size is 100MB.');
      return;
    }

    setFile(selectedFile);
    setError(null);

    // Auto-fill title if empty
    if (!formData.title) {
      const fileName = selectedFile.name.replace(/\.[^/.]+$/, '');
      setFormData(prev => ({ ...prev, title: fileName }));
    }
  };

  // Add topic
  const handleAddTopic = () => {
    const topic = topicInput.trim();
    if (topic && !formData.topics.includes(topic)) {
      setFormData(prev => ({
        ...prev,
        topics: [...prev.topics, topic],
      }));
      setTopicInput('');
    }
  };

  // Remove topic
  const handleRemoveTopic = (index: number) => {
    setFormData(prev => ({
      ...prev,
      topics: prev.topics.filter((_, i) => i !== index),
    }));
  };

  // Submit upload
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    if (!formData.title || !formData.subject) {
      setError('Please fill in all required fields.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await materialsApi.upload(file, {
        title: formData.title,
        subject: formData.subject,
        grade: formData.grade,
        description: formData.description || undefined,
        topics: formData.topics.length > 0 ? formData.topics : undefined,
      });

      setSuccess(true);

      // Reset form after 2 seconds and navigate to materials library
      setTimeout(() => {
        navigate('/materials');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-600 hover:text-gray-900"
            >
              ← Back
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Upload Study Material</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Drop Zone */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                File *
              </label>
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
                  border-2 border-dashed rounded-lg p-8 text-center transition-colors
                  ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
                  ${file ? 'bg-green-50 border-green-500' : ''}
                `}
              >
                {file ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-center">
                      <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <p className="text-lg font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <button
                      type="button"
                      onClick={() => setFile(null)}
                      className="text-sm text-red-600 hover:text-red-700 font-medium"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <svg className="w-12 h-12 text-gray-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-lg text-gray-700">
                      Drag and drop your file here, or{' '}
                      <label className="text-blue-600 hover:text-blue-700 cursor-pointer font-medium">
                        browse
                        <input
                          type="file"
                          className="hidden"
                          onChange={handleFileSelect}
                          accept=".pdf,.docx,.txt"
                        />
                      </label>
                    </p>
                    <p className="text-sm text-gray-500">
                      Supported formats: PDF, DOCX, TXT (max 100MB)
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Introduction to Algebra"
                required
              />
            </div>

            {/* Subject */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subject *
              </label>
              <select
                value={formData.subject}
                onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select a subject</option>
                <option value="Mathematics">Mathematics</option>
                <option value="Science">Science</option>
                <option value="English">English</option>
                <option value="History">History</option>
                <option value="Geography">Geography</option>
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
                <option value="Biology">Biology</option>
                <option value="Computer Science">Computer Science</option>
              </select>
            </div>

            {/* Grade Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Grade Level *
              </label>
              <input
                type="number"
                value={formData.grade}
                onChange={(e) => setFormData(prev => ({ ...prev, grade: parseInt(e.target.value) }))}
                min="1"
                max="12"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description (Optional)
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Brief description of the material..."
                rows={3}
              />
            </div>

            {/* Topics */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Topics (Optional)
              </label>
              <div className="flex space-x-2 mb-2">
                <input
                  type="text"
                  value={topicInput}
                  onChange={(e) => setTopicInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTopic())}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Linear Equations"
                />
                <button
                  type="button"
                  onClick={handleAddTopic}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                >
                  Add
                </button>
              </div>
              {formData.topics.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.topics.map((topic, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {topic}
                      <button
                        type="button"
                        onClick={() => handleRemoveTopic(index)}
                        className="ml-2 text-blue-600 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800 text-sm">
                  Material uploaded successfully! Redirecting to library...
                </p>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => navigate('/materials')}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                disabled={uploading}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={uploading || !file}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {uploading ? 'Uploading...' : 'Upload Material'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
