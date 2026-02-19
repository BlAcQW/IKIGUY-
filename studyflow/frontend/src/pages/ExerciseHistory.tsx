/**
 * Exercise History Screen
 *
 * Shows past exercise submissions with:
 * - List of completed exercises
 * - Scores and submission dates
 * - Ability to view results again
 * - Search filtering
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { exercisesApi } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import {
  Clock,
  Calendar,
  TrendingUp,
  Eye,
  CheckCircle,
  XCircle,
  Trophy,
  Target,
  BookOpen,
  Star,
  Search,
} from 'lucide-react';

// Mock data - in production this would come from API
interface SubmissionHistory {
  id: string;
  exercise_id: string;
  exercise_title: string;
  subject: string;
  difficulty: string;
  score: number;
  max_score: number;
  percentage: number;
  grade: string;
  passed: boolean;
  questions_correct: number;
  questions_total: number;
  time_taken_seconds: number;
  submitted_at: string;
}

// Soft pastel colors for grade badges
const GRADE_COLORS: Record<string, string> = {
  A: 'bg-green-50 text-green-700 border border-green-200',
  B: 'bg-blue-50 text-blue-700 border border-blue-200',
  C: 'bg-yellow-50 text-yellow-700 border border-yellow-200',
  D: 'bg-orange-50 text-orange-700 border border-orange-200',
  F: 'bg-red-50 text-red-700 border border-red-200',
};

// Very soft pastel background colors for submission cards
const GRADE_CARD_COLORS: Record<string, string> = {
  A: 'bg-green-50/30',
  B: 'bg-blue-50/30',
  C: 'bg-yellow-50/30',
  D: 'bg-orange-50/30',
  F: 'bg-red-50/30',
};

export default function ExerciseHistory() {
  const navigate = useNavigate();
  const [submissions, setSubmissions] = useState<SubmissionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      setLoading(true);
      const data = await exercisesApi.getMySubmissions({ limit: 100 });
      setSubmissions(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load history:', err);
      setSubmissions([]);
    } finally {
      setLoading(false);
    }
  }

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  }

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  }

  function handleViewResults(submissionId: string) {
    navigate(`/exercises/results/${submissionId}`);
  }

  function handleRetry(exerciseId: string) {
    navigate(`/exercises/${exerciseId}/take`);
  }

  // Filter submissions by search query only
  const filteredSubmissions = submissions.filter((submission) => {
    if (!searchQuery) return true;

    const searchLower = searchQuery.toLowerCase();
    return (
      submission.exercise_title.toLowerCase().includes(searchLower) ||
      submission.subject.toLowerCase().includes(searchLower) ||
      submission.difficulty.toLowerCase().includes(searchLower)
    );
  });

  // Calculate stats
  const totalAttempts = filteredSubmissions.length;
  const passedAttempts = filteredSubmissions.filter((s) => s.passed).length;
  const averageScore =
    totalAttempts > 0
      ? filteredSubmissions.reduce((sum, s) => sum + s.percentage, 0) / totalAttempts
      : 0;
  const totalQuestions = filteredSubmissions.reduce((sum, s) => sum + s.questions_total, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/exercises')}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                ← Back
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Exercise History</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Attempts</p>
                <p className="text-2xl font-bold text-gray-900">{totalAttempts}</p>
              </div>
              <div className="p-2 bg-blue-50 rounded-lg">
                <Trophy className="text-blue-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Passed</p>
                <p className="text-2xl font-bold text-gray-900">{passedAttempts}</p>
              </div>
              <div className="p-2 bg-green-50 rounded-lg">
                <CheckCircle className="text-green-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Average Score</p>
                <p className="text-2xl font-bold text-gray-900">{Math.round(averageScore)}%</p>
              </div>
              <div className="p-2 bg-yellow-50 rounded-lg">
                <Star className="text-yellow-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Questions</p>
                <p className="text-2xl font-bold text-gray-900">{totalQuestions}</p>
              </div>
              <div className="p-2 bg-purple-50 rounded-lg">
                <BookOpen className="text-purple-600" size={24} />
              </div>
            </div>
          </div>
        </div>

        {/* Filter - Search Only */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <Input
              type="text"
              placeholder="Search submissions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-10"
            />
          </div>
        </div>

        {/* Submissions List */}
        {filteredSubmissions.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Trophy className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No submissions found
            </h3>
            <p className="text-gray-600 mb-4">
              {searchQuery
                ? 'Try adjusting your search query'
                : 'Take your first exercise to see your history here'}
            </p>
            {!searchQuery && (
              <button
                onClick={() => navigate('/exercises')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Browse Exercises
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredSubmissions.map((submission) => (
              <div
                key={submission.id}
                className={`rounded-lg shadow hover:shadow-lg transition-all border border-gray-200 overflow-hidden ${GRADE_CARD_COLORS[submission.grade]}`}
              >
                {/* Card Header */}
                <div className="bg-white/50 backdrop-blur-sm px-6 pt-6 pb-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Title */}
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">
                        {submission.exercise_title}
                      </h3>

                      {/* Grade and Pass/Fail Badges */}
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold ${GRADE_COLORS[submission.grade]}`}>
                          <Trophy size={16} />
                          <span>Grade {submission.grade}</span>
                          <span className="text-sm font-normal">({submission.percentage}%)</span>
                        </div>
                        {submission.passed ? (
                          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-50 text-green-700 border border-green-200 font-medium">
                            <CheckCircle size={16} />
                            <span>Passed</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-50 text-red-700 border border-red-200 font-medium">
                            <XCircle size={16} />
                            <span>Failed</span>
                          </div>
                        )}
                      </div>

                      {/* Subject and Difficulty */}
                      <div className="flex gap-2">
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                          {submission.subject}
                        </span>
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs capitalize">
                          {submission.difficulty}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card Body */}
                <div className="bg-white px-6 pb-6 pt-4">
                  {/* Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 pb-4 border-b border-gray-100">
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar size={16} className="mr-2 text-blue-600" />
                      <span>{formatDate(submission.submitted_at)}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Clock size={16} className="mr-2 text-purple-600" />
                      <span>{formatTime(submission.time_taken_seconds)}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Target size={16} className="mr-2 text-green-600" />
                      <span>
                        <strong>{submission.percentage}%</strong> ({submission.score}/{submission.max_score} pts)
                      </span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <BookOpen size={16} className="mr-2 text-orange-600" />
                      <span>
                        {submission.questions_correct}/{submission.questions_total} correct
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleViewResults(submission.id)}
                      className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <Eye size={16} />
                      View Results
                    </button>
                    <button
                      onClick={() => handleRetry(submission.exercise_id)}
                      className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Retry Exercise
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
