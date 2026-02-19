/**
 * Visitor Analytics Dashboard
 *
 * Displays journey funnel analytics including:
 * - Spiritual journey funnel
 * - Cell journey funnel
 * - Ministry journey funnel
 * - Conversion rates between stages
 * - Recent visitor trends
 *
 * URL: /visitors/analytics
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Users,
  Heart,
  Briefcase,
  ArrowLeft,
  Calendar,
  Loader,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { journeyApi, type JourneyAnalytics } from '../services/visitorApi';

type JourneyType = 'spiritual' | 'cell' | 'ministry';

export default function VisitorAnalytics() {
  const navigate = useNavigate();
  const [spiritualAnalytics, setSpiritualAnalytics] = useState<JourneyAnalytics | null>(null);
  const [cellAnalytics, setCellAnalytics] = useState<JourneyAnalytics | null>(null);
  const [ministryAnalytics, setMinistryAnalytics] = useState<JourneyAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeJourney, setActiveJourney] = useState<JourneyType>('spiritual');

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [spiritual, cell, ministry] = await Promise.all([
        journeyApi.getAnalytics({ journey_type: 'spiritual' }),
        journeyApi.getAnalytics({ journey_type: 'cell' }),
        journeyApi.getAnalytics({ journey_type: 'ministry' }),
      ]);

      setSpiritualAnalytics(spiritual);
      setCellAnalytics(cell);
      setMinistryAnalytics(ministry);
    } catch (err: any) {
      console.error('Failed to load analytics:', err);
      setError(err.response?.data?.detail || 'Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  };

  const getActiveAnalytics = () => {
    switch (activeJourney) {
      case 'spiritual':
        return spiritualAnalytics;
      case 'cell':
        return cellAnalytics;
      case 'ministry':
        return ministryAnalytics;
      default:
        return null;
    }
  };

  const getJourneyIcon = (type: JourneyType) => {
    switch (type) {
      case 'spiritual':
        return <Heart className="w-5 h-5" />;
      case 'cell':
        return <Users className="w-5 h-5" />;
      case 'ministry':
        return <Briefcase className="w-5 h-5" />;
    }
  };

  const getJourneyColor = (type: JourneyType) => {
    switch (type) {
      case 'spiritual':
        return 'purple';
      case 'cell':
        return 'green';
      case 'ministry':
        return 'blue';
    }
  };

  const analytics = getActiveAnalytics();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/visitors')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  <TrendingUp className="w-6 h-6 text-purple-600" />
                  Journey Analytics
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  Track member progression through discipleship journeys
                </p>
              </div>
            </div>
            <button
              onClick={loadAnalytics}
              disabled={isLoading}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
            >
              <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Journey Type Selector */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-2 mb-6 inline-flex gap-2">
          {(['spiritual', 'cell', 'ministry'] as JourneyType[]).map((type) => {
            const color = getJourneyColor(type);
            const isActive = activeJourney === type;
            return (
              <button
                key={type}
                onClick={() => setActiveJourney(type)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors capitalize ${
                  isActive
                    ? `bg-${color}-50 text-${color}-700 border border-${color}-200`
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {getJourneyIcon(type)}
                {type} Journey
              </button>
            );
          })}
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-900">Error Loading Analytics</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader className="w-8 h-8 text-purple-600 animate-spin mb-4" />
            <p className="text-gray-600">Loading analytics...</p>
          </div>
        )}

        {/* Analytics Content */}
        {!isLoading && analytics && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-500">Total Members</span>
                  <Users className="w-5 h-5 text-gray-400" />
                </div>
                <p className="text-3xl font-bold text-gray-900">{analytics.total_members}</p>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-500">Total Stages</span>
                  <TrendingUp className="w-5 h-5 text-gray-400" />
                </div>
                <p className="text-3xl font-bold text-gray-900">{analytics.funnel.length}</p>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-500">Date Range</span>
                  <Calendar className="w-5 h-5 text-gray-400" />
                </div>
                <p className="text-sm text-gray-900 font-medium">
                  {analytics.date_range.start ? new Date(analytics.date_range.start).toLocaleDateString() : 'All time'}
                  {' - '}
                  {analytics.date_range.end ? new Date(analytics.date_range.end).toLocaleDateString() : 'Now'}
                </p>
              </div>
            </div>

            {/* Journey Funnel */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6 capitalize">
                {activeJourney} Journey Funnel
              </h2>
              <div className="space-y-4">
                {analytics.funnel.map((stage, index) => {
                  const color = getJourneyColor(activeJourney);
                  const percentage = stage.percentage;
                  const isFirst = index === 0;
                  const dropoffFromPrevious =
                    index > 0 ? analytics.funnel[index - 1].percentage - percentage : 0;

                  return (
                    <div key={stage.stage_name} className="relative">
                      {/* Stage Info */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 text-gray-700 text-sm font-semibold">
                            {index + 1}
                          </span>
                          <div>
                            <h3 className="font-medium text-gray-900">{stage.stage_display_name}</h3>
                            <p className="text-xs text-gray-500">{stage.stage_name}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-semibold text-gray-900">{stage.count}</p>
                          <p className="text-xs text-gray-500">{percentage.toFixed(1)}%</p>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="relative w-full bg-gray-200 rounded-full h-6 overflow-hidden">
                        <div
                          className={`bg-${color}-600 h-6 rounded-full transition-all duration-500 flex items-center justify-end pr-3`}
                          style={{ width: `${percentage}%` }}
                        >
                          <span className="text-xs font-semibold text-white">
                            {percentage.toFixed(1)}%
                          </span>
                        </div>
                      </div>

                      {/* Drop-off Indicator */}
                      {!isFirst && dropoffFromPrevious > 0 && (
                        <div className="mt-1 flex items-center justify-end gap-1 text-xs text-orange-600">
                          <span className="font-medium">
                            -{dropoffFromPrevious.toFixed(1)}% drop-off
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Conversion Rates */}
            {analytics.conversion_rates && Object.keys(analytics.conversion_rates).length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Stage Conversion Rates</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(analytics.conversion_rates).map(([stageName, rate]) => (
                    <div
                      key={stageName}
                      className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                    >
                      <p className="text-sm text-gray-600 mb-1 capitalize">
                        {stageName.replace(/_/g, ' ')}
                      </p>
                      <p className="text-2xl font-bold text-gray-900">{rate.toFixed(1)}%</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty Funnel State */}
            {analytics.funnel.length === 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  No {activeJourney} journey data
                </h3>
                <p className="text-gray-600">
                  Members haven't been added to this journey yet.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
