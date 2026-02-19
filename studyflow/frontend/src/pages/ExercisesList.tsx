/**
 * Exercise List Screen - Enhanced Modern Design
 *
 * Shows available exercises with filtering by subject/topic/difficulty.
 * Displays completed vs available badges and scores with modern UI.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { exercisesApi } from '../lib/api';
import { Exercise, DifficultyLevel } from '../types/exercise';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import {
  BookOpen,
  Clock,
  Target,
  TrendingUp,
  Search,
  Plus,
  Award,
  Zap,
  Brain,
  Star,
  ArrowRight,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';

// Soft pastel colors for difficulty badges
const DIFFICULTY_COLORS: Record<DifficultyLevel, string> = {
  beginner: 'bg-green-50 text-green-700 border border-green-200',
  easy: 'bg-blue-50 text-blue-700 border border-blue-200',
  medium: 'bg-yellow-50 text-yellow-700 border border-yellow-200',
  hard: 'bg-orange-50 text-orange-700 border border-orange-200',
  expert: 'bg-red-50 text-red-700 border border-red-200',
};

// Very soft pastel background colors for exercise cards
const DIFFICULTY_CARD_COLORS: Record<DifficultyLevel, string> = {
  beginner: 'bg-green-50/30',
  easy: 'bg-blue-50/30',
  medium: 'bg-yellow-50/30',
  hard: 'bg-orange-50/30',
  expert: 'bg-red-50/30',
};

const DIFFICULTY_LABELS: Record<DifficultyLevel, string> = {
  beginner: 'Beginner',
  easy: 'Easy',
  medium: 'Medium',
  hard: 'Hard',
  expert: 'Expert',
};

export default function ExercisesList() {
  const navigate = useNavigate();
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadExercises();
  }, []);

  async function loadExercises() {
    try {
      setLoading(true);
      setError(null);

      const data = await exercisesApi.list({ limit: 100 });
      setExercises(data);
    } catch (err: any) {
      console.error('Failed to load exercises:', err);
      setError(err.message || 'Failed to load exercises');
    } finally {
      setLoading(false);
    }
  }

  // Filter exercises by search query only
  const filteredExercises = exercises.filter((exercise) => {
    if (!searchQuery) return true;

    const searchLower = searchQuery.toLowerCase();
    return (
      exercise.title.toLowerCase().includes(searchLower) ||
      exercise.subject.toLowerCase().includes(searchLower) ||
      exercise.topics.some((topic) => topic.toLowerCase().includes(searchLower))
    );
  });

  function handleStartExercise(exerciseId: string) {
    navigate(`/exercises/${exerciseId}/take`);
  }

  function handleCreateExercise() {
    navigate('/materials');
  }

  // Calculate stats
  const totalExercises = exercises.length;
  const totalQuestions = exercises.reduce((sum, ex) => sum + ex.num_questions, 0);
  const totalPoints = exercises.reduce((sum, ex) => sum + ex.total_points, 0);
  const avgDifficulty = exercises.length > 0
    ? exercises.filter(ex => ex.difficulty === 'medium' || ex.difficulty === 'hard').length / exercises.length * 100
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading exercises...</p>
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
                onClick={() => navigate('/materials')}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                ← Back
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Practice Exercises</h1>
            </div>
            <button
              onClick={handleCreateExercise}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus size={20} />
              Upload Materials
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards - Simplified */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Exercises</p>
                <p className="text-2xl font-bold text-gray-900">{totalExercises}</p>
              </div>
              <div className="p-2 bg-blue-50 rounded-lg">
                <BookOpen className="text-blue-600" size={24} />
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
                <Target className="text-purple-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Points</p>
                <p className="text-2xl font-bold text-gray-900">{totalPoints}</p>
              </div>
              <div className="p-2 bg-yellow-50 rounded-lg">
                <Star className="text-yellow-600" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Challenge Level</p>
                <p className="text-2xl font-bold text-gray-900">{Math.round(avgDifficulty)}%</p>
              </div>
              <div className="p-2 bg-green-50 rounded-lg">
                <Zap className="text-green-600" size={24} />
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
            <button
              onClick={loadExercises}
              className="mt-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Filter - Search Only */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <Input
              type="text"
              placeholder="Search exercises..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-10"
            />
          </div>
        </div>

        {/* Exercise Cards */}
        {filteredExercises.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="max-w-md mx-auto">
              <BookOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No exercises found
              </h3>
              <p className="text-gray-600 mb-4">
                {searchQuery
                  ? 'Try adjusting your search query'
                  : 'Create your first exercise to get started'}
              </p>
              {!searchQuery && (
                <button
                  onClick={handleCreateExercise}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Upload Materials
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredExercises.map((exercise) => (
              <div
                key={exercise.id}
                className={`rounded-lg shadow hover:shadow-lg transition-all cursor-pointer border border-gray-200 overflow-hidden ${DIFFICULTY_CARD_COLORS[exercise.difficulty]}`}
                onClick={() => handleStartExercise(exercise.id)}
              >
                {/* Card Header with Difficulty Badge */}
                <div className="bg-white/50 backdrop-blur-sm px-6 pt-6 pb-4">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 flex-1 line-clamp-2 pr-2">
                      {exercise.title}
                    </h3>
                    <Badge className={DIFFICULTY_COLORS[exercise.difficulty]}>
                      {DIFFICULTY_LABELS[exercise.difficulty]}
                    </Badge>
                  </div>

                  {/* Subject */}
                  <p className="text-sm text-gray-600 font-medium">{exercise.subject}</p>
                </div>

                {/* Card Body */}
                <div className="bg-white px-6 pb-6 pt-4">
                  {/* Topics */}
                  {exercise.topics && exercise.topics.length > 0 && (
                    <div className="mb-4 flex flex-wrap gap-2">
                      {exercise.topics.slice(0, 3).map((topic, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                        >
                          {topic}
                        </span>
                      ))}
                      {exercise.topics.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                          +{exercise.topics.length - 3} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Stats */}
                  <div className="space-y-2 mb-4 pt-4 border-t border-gray-100">
                    <div className="flex items-center text-sm text-gray-600">
                      <BookOpen size={16} className="mr-2 text-blue-600" />
                      <span>{exercise.num_questions} questions</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Target size={16} className="mr-2 text-purple-600" />
                      <span>{exercise.total_points} points</span>
                    </div>
                    {exercise.time_limit_minutes && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Clock size={16} className="mr-2 text-gray-600" />
                        <span>{exercise.time_limit_minutes} minutes</span>
                      </div>
                    )}
                  </div>

                  {/* Action Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartExercise(exercise.id);
                    }}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Start Exercise
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* View History Button */}
        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/exercises/history')}
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <TrendingUp size={20} />
            View Exercise History
          </button>
        </div>
      </main>
    </div>
  );
}
