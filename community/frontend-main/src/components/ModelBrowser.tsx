/**
 * Model Browser Component
 *
 * Displays ML models with filtering, search, and download capabilities.
 * Features:
 * - Grid/List view toggle
 * - Filters: type, language, version
 * - Performance metrics display
 * - Download interface with authentication
 * - Model comparison tool
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';

// Types
interface Model {
  model_uuid: string;
  name: string;
  model_type: 'asr' | 'tts' | 'llm';
  architecture: string;
  languages: string[];
  primary_language: string;
  version: string;
  description?: string;
  performance_metrics?: {
    accuracy?: number;
    wer?: number;
    loss?: number;
    [key: string]: any;
  };
  file_size?: number;
  download_count?: number;
  created_at: string;
  owner_id?: string;
  is_public: boolean;
  storage_path?: string;
}

type ViewMode = 'grid' | 'list';
type ModelType = 'all' | 'asr' | 'tts' | 'llm';

export const ModelBrowser: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [filteredModels, setFilteredModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');

  // Filters
  const [selectedType, setSelectedType] = useState<ModelType>('all');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'downloads'>('date');

  // Comparison
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedForComparison, setSelectedForComparison] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    filterAndSortModels();
  }, [models, selectedType, selectedLanguage, searchQuery, sortBy]);

  const loadModels = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getModels();
      setModels(response.items || response || []);
    } catch (error) {
      console.error('Failed to load models:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortModels = () => {
    let filtered = [...models];

    // Filter by type
    if (selectedType !== 'all') {
      filtered = filtered.filter(m => m.model_type === selectedType);
    }

    // Filter by language
    if (selectedLanguage !== 'all') {
      filtered = filtered.filter(m =>
        m.languages.includes(selectedLanguage) ||
        m.primary_language === selectedLanguage
      );
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(m =>
        m.name.toLowerCase().includes(query) ||
        m.description?.toLowerCase().includes(query) ||
        m.architecture.toLowerCase().includes(query)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'downloads':
          return (b.download_count || 0) - (a.download_count || 0);
        case 'date':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

    setFilteredModels(filtered);
  };

  const handleDownload = async (model: Model) => {
    try {
      // Check authentication
      const user = localStorage.getItem('user');
      if (!user) {
        alert('Please sign in to download models');
        return;
      }

      // Get download URL
      const downloadUrl = await apiClient.getModelDownloadUrl(model.model_uuid);

      // Trigger download
      window.open(downloadUrl, '_blank');

      // Track download
      await apiClient.trackModelDownload(model.model_uuid);

      // Reload to update download count
      loadModels();
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download model. Please try again.');
    }
  };

  const toggleComparison = (modelId: string) => {
    const newSelection = new Set(selectedForComparison);
    if (newSelection.has(modelId)) {
      newSelection.delete(modelId);
    } else {
      if (newSelection.size >= 3) {
        alert('You can compare up to 3 models at a time');
        return;
      }
      newSelection.add(modelId);
    }
    setSelectedForComparison(newSelection);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    return `${(mb / 1024).toFixed(1)} GB`;
  };

  const getLanguages = () => {
    const languages = new Set<string>();
    models.forEach(m => {
      m.languages.forEach(lang => languages.add(lang));
    });
    return Array.from(languages).sort();
  };

  const ModelCard: React.FC<{ model: Model }> = ({ model }) => {
    const isSelected = selectedForComparison.has(model.model_uuid);

    return (
      <div className={`model-card ${isSelected ? 'selected' : ''}`}>
        {comparisonMode && (
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => toggleComparison(model.model_uuid)}
            className="comparison-checkbox"
          />
        )}

        <div className="model-header">
          <h3>{model.name}</h3>
          <span className={`model-type-badge ${model.model_type}`}>
            {model.model_type.toUpperCase()}
          </span>
        </div>

        <div className="model-info">
          <p className="model-description">
            {model.description || 'No description available'}
          </p>

          <div className="model-meta">
            <div className="meta-item">
              <span className="label">Architecture:</span>
              <span className="value">{model.architecture}</span>
            </div>

            <div className="meta-item">
              <span className="label">Languages:</span>
              <span className="value">
                {model.languages.join(', ')}
              </span>
            </div>

            <div className="meta-item">
              <span className="label">Version:</span>
              <span className="value">{model.version}</span>
            </div>

            <div className="meta-item">
              <span className="label">Size:</span>
              <span className="value">{formatFileSize(model.file_size)}</span>
            </div>
          </div>

          {/* Performance Metrics */}
          {model.performance_metrics && Object.keys(model.performance_metrics).length > 0 && (
            <div className="performance-metrics">
              <h4>Performance</h4>
              <div className="metrics-grid">
                {Object.entries(model.performance_metrics).map(([key, value]) => (
                  <div key={key} className="metric">
                    <span className="metric-label">{key}:</span>
                    <span className="metric-value">
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="model-stats">
            <span>📥 {model.download_count || 0} downloads</span>
            <span>📅 {new Date(model.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="model-actions">
          <button
            onClick={() => handleDownload(model)}
            className="btn btn-primary"
          >
            Download
          </button>
          <button
            onClick={() => window.location.href = `/models/${model.model_uuid}`}
            className="btn btn-secondary"
          >
            Details
          </button>
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="loading">Loading models...</div>;
  }

  return (
    <div className="model-browser">
      <div className="browser-header">
        <h1>Model Browser</h1>
        <p>Explore and download ML models for African languages</p>
      </div>

      {/* Filters and Controls */}
      <div className="browser-controls">
        <div className="filters">
          {/* Search */}
          <div className="search-box">
            <input
              type="text"
              placeholder="Search models..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as ModelType)}
          >
            <option value="all">All Types</option>
            <option value="asr">ASR (Speech Recognition)</option>
            <option value="tts">TTS (Text-to-Speech)</option>
            <option value="llm">LLM (Language Models)</option>
          </select>

          {/* Language Filter */}
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
          >
            <option value="all">All Languages</option>
            {getLanguages().map(lang => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
          >
            <option value="date">Newest First</option>
            <option value="name">Name (A-Z)</option>
            <option value="downloads">Most Downloaded</option>
          </select>
        </div>

        <div className="view-controls">
          {/* View Mode */}
          <div className="view-mode-toggle">
            <button
              className={viewMode === 'grid' ? 'active' : ''}
              onClick={() => setViewMode('grid')}
            >
              Grid
            </button>
            <button
              className={viewMode === 'list' ? 'active' : ''}
              onClick={() => setViewMode('list')}
            >
              List
            </button>
          </div>

          {/* Comparison Mode */}
          <button
            className={`btn ${comparisonMode ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setComparisonMode(!comparisonMode);
              if (comparisonMode) {
                setSelectedForComparison(new Set());
              }
            }}
          >
            {comparisonMode ? 'Exit Comparison' : 'Compare Models'}
          </button>

          {comparisonMode && selectedForComparison.size >= 2 && (
            <button
              className="btn btn-success"
              onClick={() => {
                const ids = Array.from(selectedForComparison).join(',');
                window.location.href = `/models/compare?ids=${ids}`;
              }}
            >
              Compare ({selectedForComparison.size})
            </button>
          )}
        </div>
      </div>

      {/* Results Count */}
      <div className="results-info">
        <p>
          Showing {filteredModels.length} of {models.length} models
        </p>
      </div>

      {/* Models Grid/List */}
      <div className={`models-container ${viewMode}`}>
        {filteredModels.length === 0 ? (
          <div className="no-results">
            <p>No models found matching your criteria</p>
            <button onClick={() => {
              setSelectedType('all');
              setSelectedLanguage('all');
              setSearchQuery('');
            }}>
              Clear Filters
            </button>
          </div>
        ) : (
          filteredModels.map(model => (
            <ModelCard key={model.model_uuid} model={model} />
          ))
        )}
      </div>
    </div>
  );
};

export default ModelBrowser;
