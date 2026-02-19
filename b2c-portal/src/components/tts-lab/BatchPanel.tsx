/**
 * Batch Panel Component
 *
 * Interface for batch TTS synthesis from CSV files.
 * Allows users to upload CSV, track progress, and download ZIP.
 *
 * Created: 2025-10-27
 * Sprint 4: Advanced Features (Phase 9)
 */

import React, { useState, useEffect } from 'react';
import { TTSProvider } from '../../config/tts-providers';
import { useBatchSynthesis } from '../../hooks/useBatchSynthesis';

interface BatchPanelProps {
  provider: TTSProvider;
  getLanguages: () => Promise<string[]>;
  getSpeakers: (language?: string) => Promise<string[]>;
}

interface BatchJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_items: number;
  completed_items: number;
  failed_items: number;
  total_cost: number;
  zip_filename: string | null;
  created_at: string;
  completed_at: string | null;
}

export const BatchPanel: React.FC<BatchPanelProps> = ({
  provider,
  getLanguages,
  getSpeakers,
}) => {
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [language, setLanguage] = useState('en');
  const [speaker, setSpeaker] = useState<string>('0');
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);
  const [dragActive, setDragActive] = useState(false);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [availableSpeakers, setAvailableSpeakers] = useState<string[]>([]);

  // Batch jobs state
  const [currentBatchJob, setCurrentBatchJob] = useState<BatchJob | null>(null);
  const [batchHistory, setBatchHistory] = useState<BatchJob[]>([]);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  const { uploadBatch, getBatchJob, listBatchJobs, downloadBatch, deleteBatch, isLoading, error } = useBatchSynthesis();

  // Load available languages
  useEffect(() => {
    const loadLanguages = async () => {
      const langs = await getLanguages();
      setAvailableLanguages(langs);
      if (langs.length > 0) {
        setLanguage(langs[0]);
      }
    };
    loadLanguages();
  }, [provider.id, getLanguages]);

  // Load available speakers when language changes
  useEffect(() => {
    if (provider.capabilities.multiSpeaker) {
      const loadSpeakers = async () => {
        const speakers = await getSpeakers(language);
        setAvailableSpeakers(speakers);
        if (speakers.length > 0) {
          setSpeaker('0');
        }
      };
      loadSpeakers();
    }
  }, [language, provider.id, provider.capabilities.multiSpeaker, getSpeakers]);

  // Load batch history on mount
  useEffect(() => {
    const loadHistory = async () => {
      const jobs = await listBatchJobs();
      setBatchHistory(jobs);
    };
    loadHistory();
  }, []);

  // Poll for batch job updates
  useEffect(() => {
    if (currentBatchJob && (currentBatchJob.status === 'pending' || currentBatchJob.status === 'processing')) {
      const interval = setInterval(async () => {
        const updatedJob = await getBatchJob(currentBatchJob.id);
        if (updatedJob) {
          setCurrentBatchJob(updatedJob);

          // Stop polling if job is completed or failed
          if (updatedJob.status === 'completed' || updatedJob.status === 'failed') {
            clearInterval(interval);
            setPollingInterval(null);

            // Refresh history
            const jobs = await listBatchJobs();
            setBatchHistory(jobs);
          }
        }
      }, 2000); // Poll every 2 seconds

      setPollingInterval(interval);

      return () => {
        clearInterval(interval);
      };
    }
  }, [currentBatchJob?.id, currentBatchJob?.status]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.name.endsWith('.csv')) {
      setCsvFile(file);
    } else {
      alert('Please select a CSV file');
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file && file.name.endsWith('.csv')) {
      setCsvFile(file);
    } else {
      alert('Please drop a CSV file');
    }
  };

  const handleUpload = async () => {
    if (!csvFile) {
      alert('Please select a CSV file');
      return;
    }

    const voiceId = provider.capabilities.multiSpeaker ? speaker : undefined;

    const job = await uploadBatch(
      csvFile,
      provider.id,
      language,
      voiceId,
      speed,
      pitch
    );

    if (job) {
      setCurrentBatchJob(job);
      setCsvFile(null); // Clear file after upload
    }
  };

  const handleDownload = async (job: BatchJob) => {
    if (job.zip_filename) {
      await downloadBatch(job.id, job.zip_filename);
    }
  };

  const handleDelete = async (jobId: string) => {
    if (confirm('Are you sure you want to delete this batch job?')) {
      try {
        await deleteBatch(jobId);
        // Refresh history
        const jobs = await listBatchJobs();
        setBatchHistory(jobs);

        // Clear current job if it was deleted
        if (currentBatchJob?.id === jobId) {
          setCurrentBatchJob(null);
        }
      } catch (err) {
        console.error('Failed to delete batch job:', err);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-700';
      case 'processing':
        return 'bg-blue-100 text-blue-700';
      case 'completed':
        return 'bg-green-100 text-green-700';
      case 'failed':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getProgressPercentage = (job: BatchJob) => {
    if (job.total_items === 0) return 0;
    return Math.round((job.completed_items / job.total_items) * 100);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <span className="text-blue-600 text-xl">ℹ️</span>
          <div>
            <h4 className="font-medium text-blue-900 text-sm">Batch Synthesis from CSV</h4>
            <p className="text-xs text-blue-700 mt-1">
              Upload a CSV file with text entries to synthesize multiple audio files at once.
              The CSV should have a "text" column and optionally a "filename" column.
            </p>
            <div className="mt-2 text-xs text-blue-600">
              <p className="font-mono">Example CSV format:</p>
              <pre className="mt-1 bg-blue-100 p-2 rounded">
{`text,filename
"Hello world","greeting.wav"
"Another text","output2.wav"`}
              </pre>
            </div>
          </div>
        </div>
      </div>

      {/* CSV Upload */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload CSV File
        </label>
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-indigo-500 bg-indigo-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
            id="csv-upload"
          />
          {csvFile ? (
            <div className="space-y-2">
              <div className="text-green-600 text-lg">✓</div>
              <p className="text-sm font-medium text-gray-900">{csvFile.name}</p>
              <p className="text-xs text-gray-500">{(csvFile.size / 1024).toFixed(2)} KB</p>
              <button
                onClick={() => setCsvFile(null)}
                className="text-sm text-red-600 hover:text-red-700 underline"
              >
                Remove
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="text-gray-400 text-4xl">📄</div>
              <div>
                <label
                  htmlFor="csv-upload"
                  className="text-sm text-indigo-600 hover:text-indigo-700 cursor-pointer font-medium"
                >
                  Click to upload
                </label>
                <span className="text-sm text-gray-500"> or drag and drop</span>
              </div>
              <p className="text-xs text-gray-500">CSV file (max 1000 entries)</p>
            </div>
          )}
        </div>
      </div>

      {/* Settings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Language Selection */}
        {provider.capabilities.multiLanguage && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900"
            >
              {availableLanguages.map((lang) => (
                <option key={lang} value={lang}>
                  {lang.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Speaker Selection */}
        {provider.capabilities.multiSpeaker && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Speaker
            </label>
            <select
              value={speaker}
              onChange={(e) => setSpeaker(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900"
            >
              {availableSpeakers.length > 0 ? (
                availableSpeakers.map((spk, idx) => (
                  <option key={idx} value={idx.toString()}>
                    {spk || `Speaker ${idx}`}
                  </option>
                ))
              ) : (
                Array.from({ length: 5 }, (_, i) => (
                  <option key={i} value={i.toString()}>
                    Speaker {i}
                  </option>
                ))
              )}
            </select>
          </div>
        )}

        {/* Speed Control */}
        {provider.capabilities.speedControl && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Speed: {speed.toFixed(1)}x
            </label>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
          </div>
        )}
      </div>

      {/* Upload Button */}
      <div>
        <button
          onClick={handleUpload}
          disabled={isLoading || !csvFile}
          className={`
            w-full px-6 py-3 rounded-lg font-medium text-white
            ${
              isLoading || !csvFile
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800'
            }
            transition-colors duration-200
          `}
        >
          {isLoading ? 'Uploading...' : 'Start Batch Synthesis'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-red-600 mr-2">⚠️</span>
            <div>
              <h4 className="font-medium text-red-900">Error</h4>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Current Batch Job */}
      {currentBatchJob && (
        <div className="bg-white border border-gray-300 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">Current Batch Job</h4>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(currentBatchJob.status)}`}>
              {currentBatchJob.status.toUpperCase()}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-700">
                {currentBatchJob.completed_items} / {currentBatchJob.total_items} items completed
              </span>
              <span className="text-gray-600">{getProgressPercentage(currentBatchJob)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${getProgressPercentage(currentBatchJob)}%` }}
              />
            </div>
          </div>

          {/* Job Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Failed Items:</span>
              <span className="ml-2 font-medium text-gray-900">{currentBatchJob.failed_items}</span>
            </div>
            <div>
              <span className="text-gray-600">Total Cost:</span>
              <span className="ml-2 font-medium text-gray-900">${currentBatchJob.total_cost.toFixed(4)}</span>
            </div>
          </div>

          {/* Download Button */}
          {currentBatchJob.status === 'completed' && currentBatchJob.zip_filename && (
            <div className="mt-4">
              <button
                onClick={() => handleDownload(currentBatchJob)}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
              >
                Download ZIP ({currentBatchJob.zip_filename})
              </button>
            </div>
          )}
        </div>
      )}

      {/* Batch History */}
      {batchHistory.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Batch History</h4>
          <div className="space-y-3">
            {batchHistory.map((job) => (
              <div
                key={job.id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                    {job.status.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(job.created_at).toLocaleString()}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs text-gray-600 mb-2">
                  <div>Items: {job.completed_items}/{job.total_items}</div>
                  <div>Failed: {job.failed_items}</div>
                  <div>Cost: ${job.total_cost.toFixed(4)}</div>
                </div>

                <div className="flex items-center space-x-2">
                  {job.status === 'completed' && job.zip_filename && (
                    <button
                      onClick={() => handleDownload(job)}
                      className="flex-1 px-3 py-1.5 bg-indigo-600 text-white rounded text-xs font-medium hover:bg-indigo-700 transition-colors"
                    >
                      Download
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(job.id)}
                    className="px-3 py-1.5 bg-red-100 text-red-700 rounded text-xs font-medium hover:bg-red-200 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
