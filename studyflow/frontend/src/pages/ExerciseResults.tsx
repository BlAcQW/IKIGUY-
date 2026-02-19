/**
 * Exercise Results Screen
 *
 * Shows detailed results after exercise submission:
 * - Score display with animation
 * - Performance summary
 * - Per-question review with correct/incorrect indicators
 * - Explanations for each question
 * - Retry and navigation buttons
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { exercisesApi } from '../lib/api';
import { SubmissionFeedback, QuestionFeedback } from '../types/exercise';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  CheckCircle,
  XCircle,
  TrendingUp,
  Trophy,
  Target,
  RotateCcw,
  ArrowLeft,
  BookOpen,
  Lightbulb,
  AlertCircle,
} from 'lucide-react';

const GRADE_COLORS: Record<string, string> = {
  A: 'text-green-600',
  B: 'text-blue-600',
  C: 'text-yellow-600',
  D: 'text-orange-600',
  F: 'text-red-600',
};

export default function ExerciseResults() {
  const { submissionId } = useParams<{ submissionId: string }>();
  const navigate = useNavigate();

  const [feedback, setFeedback] = useState<SubmissionFeedback | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAnimatedScore, setShowAnimatedScore] = useState(0);

  useEffect(() => {
    if (submissionId) {
      loadFeedback();
    }
  }, [submissionId]);

  // Animate score
  useEffect(() => {
    if (feedback) {
      let currentScore = 0;
      const targetScore = feedback.performance.percentage;
      const increment = targetScore / 50; // 50 steps

      const interval = setInterval(() => {
        currentScore += increment;
        if (currentScore >= targetScore) {
          currentScore = targetScore;
          clearInterval(interval);
        }
        setShowAnimatedScore(Math.round(currentScore));
      }, 20);

      return () => clearInterval(interval);
    }
  }, [feedback]);

  async function loadFeedback() {
    try {
      setLoading(true);
      setError(null);
      const data = await exercisesApi.getFeedback(submissionId!);
      setFeedback(data);
    } catch (err: any) {
      console.error('Failed to load feedback:', err);
      setError(err.message || 'Failed to load feedback');
    } finally {
      setLoading(false);
    }
  }

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  }

  function handleRetry() {
    if (feedback) {
      navigate(`/exercises/${feedback.exercise_id}/take`);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error || !feedback) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <Card className="p-8 max-w-md">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-center mb-2">
            Failed to Load Results
          </h2>
          <p className="text-gray-600 text-center mb-4">
            {error || 'Results not found'}
          </p>
          <button
            onClick={() => navigate('/exercises/history')}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to History
          </button>
        </Card>
      </div>
    );
  }

  const { performance } = feedback;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/exercises/history')}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                ← Back
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Exercise Results</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Score Card */}
        <Card className="p-8 mb-6 text-center bg-white shadow">
          <div className="mb-4">
            {performance.passed ? (
              <Trophy className="h-16 w-16 text-yellow-500 mx-auto" />
            ) : (
              <Target className="h-16 w-16 text-gray-400 mx-auto" />
            )}
          </div>

          <h2 className="text-3xl font-bold mb-2">
            {performance.passed ? 'Congratulations!' : 'Keep Practicing!'}
          </h2>

          <div className="mb-6">
            <div
              className={`text-6xl font-bold ${
                GRADE_COLORS[performance.grade]
              } mb-2`}
            >
              {showAnimatedScore}%
            </div>
            <div className="text-2xl font-semibold text-gray-700">
              Grade: {performance.grade}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 max-w-md mx-auto">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {performance.questions_correct}
              </div>
              <div className="text-sm text-gray-600">Correct</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {performance.questions_incorrect}
              </div>
              <div className="text-sm text-gray-600">Incorrect</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {formatTime(performance.time_taken_seconds)}
              </div>
              <div className="text-sm text-gray-600">Time</div>
            </div>
          </div>
        </Card>

        {/* Performance Summary */}
        <Card className="p-6 mb-6 bg-white shadow">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <TrendingUp size={24} className="text-blue-600" />
            Performance Summary
          </h2>

          <div className="space-y-4">
            {/* Score Breakdown */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Score
                </span>
                <span className="text-sm text-gray-600">
                  {performance.total_score} / {performance.max_score} points
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all"
                  style={{ width: `${performance.percentage}%` }}
                />
              </div>
            </div>

            {/* Strong Topics */}
            {performance.strong_topics.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle size={16} className="text-green-600" />
                  <span className="text-sm font-medium text-gray-700">
                    Strong Areas
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {performance.strong_topics.map((topic, idx) => (
                    <Badge
                      key={idx}
                      className="bg-green-50 text-green-700 border border-green-200"
                    >
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Weak Topics */}
            {performance.weak_topics.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle size={16} className="text-orange-600" />
                  <span className="text-sm font-medium text-gray-700">
                    Needs Improvement
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {performance.weak_topics.map((topic, idx) => (
                    <Badge
                      key={idx}
                      className="bg-orange-50 text-orange-700 border border-orange-200"
                    >
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {performance.recommendations.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb size={16} className="text-blue-600" />
                  <span className="text-sm font-medium text-gray-700">
                    Recommendations
                  </span>
                </div>
                <ul className="space-y-2">
                  {performance.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Card>

        {/* Question Review */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-900">
            <BookOpen size={24} className="text-blue-600" />
            Question Review
          </h2>

          <div className="space-y-4">
            {feedback.question_feedback.map((qf) => (
              <QuestionReviewCard key={qf.question_id} feedback={qf} />
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => navigate('/exercises/history')}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft size={20} />
            Back to History
          </button>
          <button
            onClick={handleRetry}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RotateCcw size={20} />
            Retry Exercise
          </button>
        </div>
      </main>
    </div>
  );
}

// Question Review Card Component
interface QuestionReviewCardProps {
  feedback: QuestionFeedback;
}

function QuestionReviewCard({ feedback }: QuestionReviewCardProps) {
  const [showExplanation, setShowExplanation] = useState(!feedback.is_correct);

  return (
    <Card className="p-6 bg-white shadow border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        {/* Status Icon */}
        <div className="shrink-0 mt-1">
          {feedback.is_correct ? (
            <div className="p-2 bg-green-50 rounded-full">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
          ) : (
            <div className="p-2 bg-red-50 rounded-full">
              <XCircle className="h-5 w-5 text-red-600" />
            </div>
          )}
        </div>

        <div className="flex-1">
          {/* Question Header */}
          <div className="mb-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <Badge className="bg-blue-50 text-blue-700 border border-blue-200">
                  Q{feedback.question_number}
                </Badge>
                <Badge className="bg-gray-100 text-gray-700 border border-gray-200 text-xs">
                  {feedback.topic}
                </Badge>
              </div>
              <div className="text-sm font-semibold text-gray-900">
                {feedback.points_earned} / {feedback.max_points} pts
              </div>
            </div>
            <p className="text-base font-medium text-gray-900">
              {feedback.question_text}
            </p>
          </div>

          {/* Student Answer */}
          <div className="mb-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm font-semibold text-gray-700 mb-2">
              Your Answer:
            </div>
            <div className="text-sm text-gray-900">{feedback.student_answer}</div>
          </div>

          {/* Correct Answer (if incorrect) */}
          {!feedback.is_correct && (
            <div className="mb-3 p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="text-sm font-semibold text-green-800 mb-2">
                Correct Answer:
              </div>
              <div className="text-sm text-green-900 font-medium">{feedback.correct_answer}</div>
            </div>
          )}

          {/* AI Feedback (if available) */}
          {feedback.ai_feedback && (
            <div className="mb-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-sm font-semibold text-blue-800 mb-2">
                Feedback:
              </div>
              <div className="text-sm text-blue-900">{feedback.ai_feedback}</div>
            </div>
          )}

          {/* Explanation Toggle */}
          <div>
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors mb-2"
            >
              {showExplanation ? 'Hide' : 'Show'} Explanation
            </button>

            {showExplanation && (
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-start gap-2 mb-2">
                  <Lightbulb size={16} className="text-blue-600 mt-0.5 shrink-0" />
                  <div className="text-sm font-semibold text-blue-800">
                    Explanation
                  </div>
                </div>
                <div className="text-sm text-gray-900 leading-relaxed">{feedback.explanation}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
