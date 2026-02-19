/**
 * Resource Contribution Form Component
 *
 * Allows users to contribute resources to the platform:
 * - File uploads (drag & drop)
 * - External link submission
 * - Notebook uploads (.ipynb)
 * - Form validation
 * - Upload progress tracking
 */

import React, { useState, useCallback } from 'react';
import { apiClient } from '../lib/api';

type ContributionType = 'file' | 'link' | 'notebook';
type ResourceType = 'dataset' | 'model' | 'notebook' | 'paper' | 'tool';

interface UploadProgress {
  filename: string;
  progress: number;
  status: 'uploading' | 'complete' | 'error';
  error?: string;
}

export const ResourceContributionForm: React.FC = () => {
  const [contributionType, setContributionType] = useState<ContributionType>('file');
  const [resourceType, setResourceType] = useState<ResourceType>('dataset');

  // Form fields
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [languageCode, setLanguageCode] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');

  // File upload
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Map<string, UploadProgress>>(new Map());
  const [isDragging, setIsDragging] = useState(false);

  // External link
  const [externalUrl, setExternalUrl] = useState('');
  const [sourceAttribution, setSourceAttribution] = useState('');

  // Notebook specific
  const [notebookFile, setNotebookFile] = useState<File | null>(null);

  // Submission
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFilesSelected(droppedFiles);
  }, []);

  const handleFilesSelected = (selectedFiles: File[]) => {
    if (contributionType === 'notebook') {
      // Only allow .ipynb files for notebooks
      const notebookFiles = selectedFiles.filter(f => f.name.endsWith('.ipynb'));
      if (notebookFiles.length > 0) {
        setNotebookFile(notebookFiles[0]);
      } else {
        alert('Please select a .ipynb (Jupyter Notebook) file');
      }
    } else {
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const addTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const validateForm = (): string | null => {
    if (!title.trim()) return 'Title is required';
    if (!description.trim()) return 'Description is required';
    if (!languageCode) return 'Language is required';

    if (contributionType === 'file' && files.length === 0) {
      return 'Please select at least one file';
    }

    if (contributionType === 'link' && !externalUrl.trim()) {
      return 'External URL is required';
    }

    if (contributionType === 'notebook' && !notebookFile) {
      return 'Please select a notebook file';
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validationError = validateForm();
    if (validationError) {
      setSubmitError(validationError);
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      if (contributionType === 'file') {
        await handleFileUpload();
      } else if (contributionType === 'link') {
        await handleLinkSubmission();
      } else if (contributionType === 'notebook') {
        await handleNotebookUpload();
      }

      setSubmitSuccess(true);
      // Reset form after 2 seconds
      setTimeout(() => {
        resetForm();
      }, 2000);

    } catch (error: any) {
      setSubmitError(error.message || 'Submission failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileUpload = async () => {
    const progressMap = new Map<string, UploadProgress>();

    for (const file of files) {
      progressMap.set(file.name, {
        filename: file.name,
        progress: 0,
        status: 'uploading'
      });
      setUploadProgress(new Map(progressMap));

      try {
        // Upload file
        await apiClient.uploadDatasetFile(
          file,
          {
            title,
            description,
            language_code: languageCode,
            resource_type: resourceType,
            tags
          },
          (progress) => {
            progressMap.set(file.name, {
              filename: file.name,
              progress,
              status: 'uploading'
            });
            setUploadProgress(new Map(progressMap));
          }
        );

        progressMap.set(file.name, {
          filename: file.name,
          progress: 100,
          status: 'complete'
        });
        setUploadProgress(new Map(progressMap));

      } catch (error: any) {
        progressMap.set(file.name, {
          filename: file.name,
          progress: 0,
          status: 'error',
          error: error.message
        });
        setUploadProgress(new Map(progressMap));
        throw error;
      }
    }
  };

  const handleLinkSubmission = async () => {
    await apiClient.submitResourceLink({
      title,
      description,
      url: externalUrl,
      language_code: languageCode,
      resource_type: resourceType,
      source_attribution: sourceAttribution,
      tags
    });
  };

  const handleNotebookUpload = async () => {
    if (!notebookFile) return;

    await apiClient.uploadNotebook(
      notebookFile,
      {
        title,
        description,
        language_code: languageCode,
        tags
      },
      (progress) => {
        setUploadProgress(new Map([[notebookFile.name, {
          filename: notebookFile.name,
          progress,
          status: 'uploading'
        }]]));
      }
    );
  };

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setLanguageCode('');
    setTags([]);
    setFiles([]);
    setExternalUrl('');
    setSourceAttribution('');
    setNotebookFile(null);
    setUploadProgress(new Map());
    setSubmitSuccess(false);
    setSubmitError(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="resource-contribution-form">
      <h2>Contribute a Resource</h2>
      <p className="form-description">
        Share datasets, models, notebooks, papers, or tools with the community
      </p>

      {submitSuccess && (
        <div className="alert alert-success">
          ✅ Resource submitted successfully! Thank you for your contribution.
        </div>
      )}

      {submitError && (
        <div className="alert alert-error">
          ❌ {submitError}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Contribution Type Selection */}
        <div className="form-group">
          <label>Contribution Type *</label>
          <div className="contribution-type-selector">
            <button
              type="button"
              className={contributionType === 'file' ? 'active' : ''}
              onClick={() => setContributionType('file')}
            >
              📁 File Upload
            </button>
            <button
              type="button"
              className={contributionType === 'link' ? 'active' : ''}
              onClick={() => setContributionType('link')}
            >
              🔗 External Link
            </button>
            <button
              type="button"
              className={contributionType === 'notebook' ? 'active' : ''}
              onClick={() => setContributionType('notebook')}
            >
              📓 Jupyter Notebook
            </button>
          </div>
        </div>

        {/* Resource Type */}
        <div className="form-group">
          <label htmlFor="resourceType">Resource Type *</label>
          <select
            id="resourceType"
            value={resourceType}
            onChange={(e) => setResourceType(e.target.value as ResourceType)}
            required
          >
            <option value="dataset">Dataset</option>
            <option value="model">Model</option>
            <option value="notebook">Notebook</option>
            <option value="paper">Research Paper</option>
            <option value="tool">Tool/Library</option>
          </select>
        </div>

        {/* Title */}
        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Twi Speech Dataset 2024"
            required
          />
        </div>

        {/* Description */}
        <div className="form-group">
          <label htmlFor="description">Description *</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the resource, its contents, and how it can be used..."
            rows={4}
            required
          />
        </div>

        {/* Language */}
        <div className="form-group">
          <label htmlFor="language">Language *</label>
          <select
            id="language"
            value={languageCode}
            onChange={(e) => setLanguageCode(e.target.value)}
            required
          >
            <option value="">Select a language</option>
            <option value="twi">Twi</option>
            <option value="yo">Yoruba</option>
            <option value="ha">Hausa</option>
            <option value="ig">Igbo</option>
            <option value="sw">Swahili</option>
            <option value="am">Amharic</option>
          </select>
        </div>

        {/* File Upload Section */}
        {contributionType === 'file' && (
          <div className="form-group">
            <label>Files *</label>
            <div
              className={`drop-zone ${isDragging ? 'dragging' : ''}`}
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="drop-zone-content">
                <p>📤 Drag and drop files here</p>
                <p>or</p>
                <input
                  type="file"
                  multiple
                  onChange={(e) => e.target.files && handleFilesSelected(Array.from(e.target.files))}
                  style={{ display: 'none' }}
                  id="file-input"
                />
                <label htmlFor="file-input" className="btn btn-secondary">
                  Browse Files
                </label>
              </div>
            </div>

            {files.length > 0 && (
              <div className="file-list">
                <h4>Selected Files ({files.length})</h4>
                {files.map((file, index) => {
                  const progress = uploadProgress.get(file.name);
                  return (
                    <div key={index} className="file-item">
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">{formatFileSize(file.size)}</span>
                      {progress && (
                        <div className="upload-progress">
                          <div
                            className="progress-bar"
                            style={{ width: `${progress.progress}%` }}
                          />
                          <span>{progress.progress}%</span>
                        </div>
                      )}
                      {!progress && (
                        <button
                          type="button"
                          onClick={() => removeFile(index)}
                          className="btn-remove"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* External Link Section */}
        {contributionType === 'link' && (
          <>
            <div className="form-group">
              <label htmlFor="url">External URL *</label>
              <input
                id="url"
                type="url"
                value={externalUrl}
                onChange={(e) => setExternalUrl(e.target.value)}
                placeholder="https://example.com/dataset"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="attribution">Source Attribution</label>
              <input
                id="attribution"
                type="text"
                value={sourceAttribution}
                onChange={(e) => setSourceAttribution(e.target.value)}
                placeholder="Original source or author"
              />
            </div>
          </>
        )}

        {/* Notebook Upload Section */}
        {contributionType === 'notebook' && (
          <div className="form-group">
            <label>Notebook File (.ipynb) *</label>
            <input
              type="file"
              accept=".ipynb"
              onChange={(e) => e.target.files && setNotebookFile(e.target.files[0])}
              required
            />
            {notebookFile && (
              <div className="file-info">
                Selected: {notebookFile.name} ({formatFileSize(notebookFile.size)})
              </div>
            )}
          </div>
        )}

        {/* Tags */}
        <div className="form-group">
          <label htmlFor="tags">Tags</label>
          <div className="tag-input">
            <input
              id="tags"
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
              placeholder="Add tags (press Enter)"
            />
            <button type="button" onClick={addTag} className="btn-add-tag">
              Add
            </button>
          </div>
          {tags.length > 0 && (
            <div className="tag-list">
              {tags.map(tag => (
                <span key={tag} className="tag">
                  {tag}
                  <button type="button" onClick={() => removeTag(tag)}>✕</button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Contribution'}
          </button>
          <button
            type="button"
            onClick={resetForm}
            className="btn btn-secondary"
            disabled={isSubmitting}
          >
            Reset
          </button>
        </div>
      </form>
    </div>
  );
};

export default ResourceContributionForm;
