/**
 * Language Resource Hub Component
 *
 * Comprehensive language page displaying all resources in one view:
 * - Datasets, models, notebooks for a specific language
 * - Resource gap indicators
 * - "Start Training" wizard
 * - Resource filtering and search
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../lib/api';

interface LanguageResource {
  datasets: {
    speech: number;
    text: number;
    total: number;
  };
  models: {
    asr: number;
    tts: number;
    llm: number;
    total: number;
  };
  notebooks: number;
  papers: number;
  contributors: number;
}

interface ResourceGap {
  category: string;
  current: number;
  target: number;
  percentage: number;
  status: 'critical' | 'low' | 'moderate' | 'good' | 'excellent';
}

interface Language {
  code: string;
  name: string;
  native_name: string;
  speaker_count?: number;
  data_tier: string;
  voice_support_level: string;
}

export const LanguageResourceHub: React.FC<{ languageCode: string }> = ({ languageCode }) => {
  const [language, setLanguage] = useState<Language | null>(null);
  const [resources, setResources] = useState<LanguageResource | null>(null);
  const [gaps, setGaps] = useState<ResourceGap[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  // Wizard
  const [showTrainingWizard, setShowTrainingWizard] = useState(false);

  useEffect(() => {
    loadLanguageData();
  }, [languageCode]);

  const loadLanguageData = async () => {
    try {
      setLoading(true);

      // Load language info
      const langData = await apiClient.getLanguage(languageCode);
      setLanguage(langData);

      // Load resource counts
      const resourceData = await loadResourceCounts();
      setResources(resourceData);

      // Calculate gaps
      const calculatedGaps = calculateResourceGaps(resourceData);
      setGaps(calculatedGaps);

    } catch (error) {
      console.error('Failed to load language data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadResourceCounts = async (): Promise<LanguageResource> => {
    // Load counts for each resource type
    const [datasets, models, notebooks, papers] = await Promise.all([
      apiClient.getDatasets({ language_code: languageCode }),
      apiClient.getModels({ language: languageCode }),
      apiClient.getNotebooks({ language_code: languageCode }),
      apiClient.getResourceLinks({ language_code: languageCode, type: 'paper' })
    ]);

    return {
      datasets: {
        speech: datasets.filter((d: any) => d.type === 'speech').length,
        text: datasets.filter((d: any) => d.type === 'text').length,
        total: datasets.length
      },
      models: {
        asr: models.filter((m: any) => m.model_type === 'asr').length,
        tts: models.filter((m: any) => m.model_type === 'tts').length,
        llm: models.filter((m: any) => m.model_type === 'llm').length,
        total: models.length
      },
      notebooks: notebooks.length,
      papers: papers.length,
      contributors: 0 // TODO: Load from API
    };
  };

  const calculateResourceGaps = (data: LanguageResource): ResourceGap[] => {
    const calculateGap = (current: number, target: number, category: string): ResourceGap => {
      const percentage = target > 0 ? (current / target) * 100 : 0;

      let status: ResourceGap['status'];
      if (percentage >= 80) status = 'excellent';
      else if (percentage >= 60) status = 'good';
      else if (percentage >= 40) status = 'moderate';
      else if (percentage >= 20) status = 'low';
      else status = 'critical';

      return { category, current, target, percentage, status };
    };

    return [
      calculateGap(data.datasets.speech, 10, 'Speech Datasets'),
      calculateGap(data.datasets.text, 5, 'Text Datasets'),
      calculateGap(data.models.asr, 3, 'ASR Models'),
      calculateGap(data.models.tts, 2, 'TTS Models'),
      calculateGap(data.models.llm, 1, 'LLM Models'),
      calculateGap(data.notebooks, 5, 'Training Notebooks'),
      calculateGap(data.papers, 3, 'Research Papers'),
    ];
  };

  const getStatusColor = (status: ResourceGap['status']) => {
    const colors = {
      critical: '#dc3545',
      low: '#fd7e14',
      moderate: '#ffc107',
      good: '#28a745',
      excellent: '#20c997'
    };
    return colors[status];
  };

  const getStatusIcon = (status: ResourceGap['status']) => {
    const icons = {
      critical: '🔴',
      low: '🟠',
      moderate: '🟡',
      good: '🟢',
      excellent: '✨'
    };
    return icons[status];
  };

  if (loading) {
    return <div className="loading">Loading language resources...</div>;
  }

  if (!language || !resources) {
    return <div className="error">Language not found</div>;
  }

  return (
    <div className="language-resource-hub">
      {/* Header */}
      <div className="hub-header">
        <h1>{language.name} ({language.native_name})</h1>
        <div className="language-meta">
          <span className="tier-badge">{language.data_tier}</span>
          <span className="voice-badge">{language.voice_support_level}</span>
          {language.speaker_count && (
            <span className="speakers">
              {(language.speaker_count / 1000000).toFixed(1)}M speakers
            </span>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="quick-stats">
        <div className="stat-card">
          <div className="stat-value">{resources.datasets.total}</div>
          <div className="stat-label">Datasets</div>
          <div className="stat-breakdown">
            {resources.datasets.speech} speech • {resources.datasets.text} text
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{resources.models.total}</div>
          <div className="stat-label">Models</div>
          <div className="stat-breakdown">
            {resources.models.asr} ASR • {resources.models.tts} TTS • {resources.models.llm} LLM
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{resources.notebooks}</div>
          <div className="stat-label">Notebooks</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{resources.papers}</div>
          <div className="stat-label">Papers</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{resources.contributors}</div>
          <div className="stat-label">Contributors</div>
        </div>
      </div>

      {/* Resource Gap Indicators */}
      <div className="resource-gaps">
        <h2>Resource Coverage</h2>
        <p className="section-description">
          Progress towards comprehensive language support
        </p>

        <div className="gaps-grid">
          {gaps.map(gap => (
            <div key={gap.category} className="gap-card">
              <div className="gap-header">
                <span className="gap-icon">{getStatusIcon(gap.status)}</span>
                <span className="gap-category">{gap.category}</span>
              </div>

              <div className="gap-progress">
                <div className="progress-bar-container">
                  <div
                    className="progress-bar"
                    style={{
                      width: `${Math.min(gap.percentage, 100)}%`,
                      backgroundColor: getStatusColor(gap.status)
                    }}
                  />
                </div>
                <div className="progress-text">
                  {gap.current} / {gap.target} ({gap.percentage.toFixed(0)}%)
                </div>
              </div>

              {gap.status === 'critical' || gap.status === 'low' ? (
                <div className="gap-action">
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => window.location.href = `/contribute?language=${languageCode}&type=${gap.category}`}
                  >
                    Contribute
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </div>

      {/* Start Training Wizard */}
      <div className="training-wizard-cta">
        <h2>Ready to Train a Model?</h2>
        <p>
          Get started with our guided training wizard that helps you:
        </p>
        <ul>
          <li>✓ Select the right datasets for your task</li>
          <li>✓ Choose appropriate model architecture</li>
          <li>✓ Configure training parameters</li>
          <li>✓ Launch training pipeline</li>
        </ul>
        <button
          className="btn btn-lg btn-success"
          onClick={() => setShowTrainingWizard(true)}
        >
          🚀 Start Training Wizard
        </button>
      </div>

      {/* Resource Categories */}
      <div className="resource-categories">
        <div className="category-tabs">
          <button
            className={selectedCategory === 'all' ? 'active' : ''}
            onClick={() => setSelectedCategory('all')}
          >
            All Resources
          </button>
          <button
            className={selectedCategory === 'datasets' ? 'active' : ''}
            onClick={() => setSelectedCategory('datasets')}
          >
            Datasets ({resources.datasets.total})
          </button>
          <button
            className={selectedCategory === 'models' ? 'active' : ''}
            onClick={() => setSelectedCategory('models')}
          >
            Models ({resources.models.total})
          </button>
          <button
            className={selectedCategory === 'notebooks' ? 'active' : ''}
            onClick={() => setSelectedCategory('notebooks')}
          >
            Notebooks ({resources.notebooks})
          </button>
          <button
            className={selectedCategory === 'papers' ? 'active' : ''}
            onClick={() => setSelectedCategory('papers')}
          >
            Papers ({resources.papers})
          </button>
        </div>

        {/* Resource Filters */}
        {selectedCategory !== 'all' && (
          <div className="resource-filters">
            {selectedCategory === 'datasets' && (
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
              >
                <option value="all">All Types</option>
                <option value="speech">Speech</option>
                <option value="text">Text</option>
              </select>
            )}

            {selectedCategory === 'models' && (
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
              >
                <option value="all">All Types</option>
                <option value="asr">ASR</option>
                <option value="tts">TTS</option>
                <option value="llm">LLM</option>
              </select>
            )}
          </div>
        )}

        {/* Resource List */}
        <div className="resource-list">
          {/* TODO: Load and display actual resources based on filters */}
          <div className="placeholder">
            Resources for {language.name} will be displayed here.
            Selected category: {selectedCategory}, type: {selectedType}
          </div>
        </div>
      </div>

      {/* Contribution CTA */}
      <div className="contribution-cta">
        <h3>Help Grow {language.name} Resources</h3>
        <p>
          Your contributions make a difference. Share datasets, models, or notebooks
          to help advance {language.name} language technology.
        </p>
        <button
          className="btn btn-primary"
          onClick={() => window.location.href = `/contribute?language=${languageCode}`}
        >
          Contribute Resources
        </button>
      </div>

      {/* Training Wizard Modal */}
      {showTrainingWizard && (
        <div className="modal-overlay" onClick={() => setShowTrainingWizard(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Training Wizard</h2>
              <button
                className="modal-close"
                onClick={() => setShowTrainingWizard(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <p>Training wizard coming soon!</p>
              <p>This will guide you through:</p>
              <ol>
                <li>Task selection (ASR, TTS, or LLM)</li>
                <li>Dataset selection</li>
                <li>Model architecture choice</li>
                <li>Hyperparameter configuration</li>
                <li>Pipeline launch</li>
              </ol>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LanguageResourceHub;
