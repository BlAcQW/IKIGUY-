/**
 * Take Exercise Screen
 *
 * Allows students to take an exercise with:
 * - Question display (one at a time or all)
 * - MCQ option selection
 * - Timer display
 * - Progress indicator
 * - Submit with confirmation
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { exercisesApi } from '../lib/api';
import { ExerciseDetail, ExerciseQuestion } from '../types/exercise';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Clock,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';

interface Answer {
  question_id: string;
  answer: string;
  time_spent_seconds: number;
}

export default function TakeExercise() {
  const { exerciseId } = useParams<{ exerciseId: string }>();
  const navigate = useNavigate();

  const [exercise, setExercise] = useState<ExerciseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Exercise state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<string, Answer>>(new Map());
  const [startTime] = useState(Date.now());
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [timeElapsed, setTimeElapsed] = useState(0);

  // UI state
  const [viewMode, setViewMode] = useState<'single' | 'all'>('single');
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Load exercise
  useEffect(() => {
    if (exerciseId) {
      loadExercise();
    }
  }, [exerciseId]);

  // Timer
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  async function loadExercise() {
    try {
      setLoading(true);
      setError(null);
      const data = await exercisesApi.get(exerciseId!);
      setExercise(data);
    } catch (err: any) {
      console.error('Failed to load exercise:', err);
      setError(err.message || 'Failed to load exercise');
    } finally {
      setLoading(false);
    }
  }

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function handleAnswerChange(questionId: string, answer: string) {
    const timeSpent = Math.floor((Date.now() - questionStartTime) / 1000);
    setAnswers(
      new Map(answers.set(questionId, {
        question_id: questionId,
        answer,
        time_spent_seconds: timeSpent,
      }))
    );
  }

  function handleNextQuestion() {
    if (exercise && currentQuestionIndex < exercise.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setQuestionStartTime(Date.now());
    }
  }

  function handlePreviousQuestion() {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setQuestionStartTime(Date.now());
    }
  }

  function handleQuestionJump(index: number) {
    setCurrentQuestionIndex(index);
    setQuestionStartTime(Date.now());
  }

  async function handleSubmit() {
    if (!exercise) return;

    try {
      setSubmitting(true);
      const submissionData = {
        answers: Array.from(answers.values()),
        time_taken_seconds: timeElapsed,
      };

      const result = await exercisesApi.submit(exercise.id, submissionData);
      setShowSubmitDialog(false);

      // Navigate to results page
      navigate(`/exercises/results/${result.id}`);
    } catch (err: any) {
      console.error('Failed to submit exercise:', err);
      setError(err.message || 'Failed to submit exercise');
    } finally {
      setSubmitting(false);
    }
  }

  function isQuestionAnswered(questionId: string): boolean {
    return answers.has(questionId);
  }

  function getAnswerForQuestion(questionId: string): string {
    return answers.get(questionId)?.answer || '';
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading exercise...</p>
        </div>
      </div>
    );
  }

  if (error || !exercise) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <Card className="p-8 max-w-md bg-white shadow">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-center mb-2">
            Failed to Load Exercise
          </h2>
          <p className="text-gray-600 text-center mb-4">
            {error || 'Exercise not found'}
          </p>
          <button
            onClick={() => navigate('/exercises')}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Exercises
          </button>
        </Card>
      </div>
    );
  }

  const currentQuestion = exercise.questions[currentQuestionIndex];
  const answeredCount = answers.size;
  const totalQuestions = exercise.questions.length;
  const progress = (answeredCount / totalQuestions) * 100;

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
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{exercise.title}</h1>
                <p className="text-sm text-gray-600">{exercise.subject}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg border border-blue-200">
              <Clock size={20} className="text-blue-600" />
              <span className="text-lg font-semibold text-gray-900">{formatTime(timeElapsed)}</span>
              {exercise.time_limit_minutes && (
                <span className="text-sm text-gray-500">
                  / {exercise.time_limit_minutes} min
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress Bar */}
        <div className="mb-6 bg-white rounded-lg shadow p-4 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Progress: {answeredCount} of {totalQuestions} answered
            </span>
            <span className="text-sm font-semibold text-blue-600">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setViewMode('single')}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${
              viewMode === 'single'
                ? 'bg-blue-600 text-white'
                : 'border border-gray-300 hover:bg-gray-50'
            }`}
          >
            One at a Time
          </button>
          <button
            onClick={() => setViewMode('all')}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${
              viewMode === 'all'
                ? 'bg-blue-600 text-white'
                : 'border border-gray-300 hover:bg-gray-50'
            }`}
          >
            View All
          </button>
        </div>

        {/* Question Display - Single Mode */}
        {viewMode === 'single' && (
          <div>
            <QuestionCard
              question={currentQuestion}
              questionNumber={currentQuestionIndex + 1}
              answer={getAnswerForQuestion(currentQuestion.question_id)}
              onAnswerChange={(answer) =>
                handleAnswerChange(currentQuestion.question_id, answer)
              }
            />

            {/* Navigation */}
            <div className="flex items-center justify-between mt-6">
              <button
                onClick={handlePreviousQuestion}
                disabled={currentQuestionIndex === 0}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft size={20} />
                Previous
              </button>

              <div className="flex gap-2 flex-wrap justify-center">
                {exercise.questions.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuestionJump(idx)}
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                      idx === currentQuestionIndex
                        ? 'bg-blue-600 text-white shadow-md'
                        : isQuestionAnswered(exercise.questions[idx].question_id)
                        ? 'bg-green-50 text-green-700 border-2 border-green-200'
                        : 'bg-gray-100 text-gray-600 border-2 border-gray-200 hover:bg-gray-200'
                    }`}
                  >
                    {idx + 1}
                  </button>
                ))}
              </div>

              <button
                onClick={handleNextQuestion}
                disabled={currentQuestionIndex === exercise.questions.length - 1}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        )}

        {/* Question Display - All Mode */}
        {viewMode === 'all' && (
          <div className="space-y-6">
            {exercise.questions.map((question, idx) => (
              <QuestionCard
                key={question.question_id}
                question={question}
                questionNumber={idx + 1}
                answer={getAnswerForQuestion(question.question_id)}
                onAnswerChange={(answer) =>
                  handleAnswerChange(question.question_id, answer)
                }
              />
            ))}
          </div>
        )}

        {/* Submit Button */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={() => setShowSubmitDialog(true)}
            className="inline-flex items-center gap-2 px-6 py-3 text-base bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <CheckCircle size={20} />
            Submit Exercise
          </button>
        </div>

        {/* Submit Confirmation Dialog */}
        <Dialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Submit Exercise?</DialogTitle>
              <DialogDescription>
                Are you ready to submit your answers? You have answered{' '}
                {answeredCount} out of {totalQuestions} questions.
                {answeredCount < totalQuestions && (
                  <span className="block mt-2 text-yellow-600 font-medium">
                    Warning: {totalQuestions - answeredCount} questions are unanswered.
                  </span>
                )}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <button
                onClick={() => setShowSubmitDialog(false)}
                disabled={submitting}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Submit'}
              </button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}

// Question Card Component
interface QuestionCardProps {
  question: ExerciseQuestion;
  questionNumber: number;
  answer: string;
  onAnswerChange: (answer: string) => void;
}

function QuestionCard({
  question,
  questionNumber,
  answer,
  onAnswerChange,
}: QuestionCardProps) {
  return (
    <Card className="p-6 bg-white shadow border border-gray-200">
      <div className="mb-4">
        <div className="flex items-start gap-3">
          <Badge className="shrink-0 bg-blue-50 text-blue-700 border border-blue-200">
            Q{questionNumber}
          </Badge>
          <div className="flex-1">
            <p className="text-lg font-semibold text-gray-900">
              {question.question_text}
            </p>
            <div className="mt-2 flex gap-2">
              <Badge className="text-xs bg-gray-100 text-gray-700 border border-gray-200">
                {question.topic}
              </Badge>
              <Badge className="text-xs bg-purple-50 text-purple-700 border border-purple-200">
                {question.points} {question.points === 1 ? 'point' : 'points'}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Multiple Choice Options */}
      {question.question_type === 'multiple_choice' && question.options && (
        <div className="space-y-3">
          {question.options.map((option) => (
            <label
              key={option.label}
              className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                answer === option.label
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="radio"
                name={`question-${question.question_id}`}
                value={option.label}
                checked={answer === option.label}
                onChange={(e) => onAnswerChange(e.target.value)}
                className="mr-3 h-4 w-4"
              />
              <span className="font-medium mr-2">{option.label}.</span>
              <span>{option.text}</span>
            </label>
          ))}
        </div>
      )}

      {/* True/False Options */}
      {question.question_type === 'true_false' && (
        <div className="space-y-3">
          {['True', 'False'].map((option) => (
            <label
              key={option}
              className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                answer === option
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="radio"
                name={`question-${question.question_id}`}
                value={option}
                checked={answer === option}
                onChange={(e) => onAnswerChange(e.target.value)}
                className="mr-3 h-4 w-4"
              />
              <span>{option}</span>
            </label>
          ))}
        </div>
      )}

      {/* Short Answer / Essay */}
      {(question.question_type === 'short_answer' ||
        question.question_type === 'essay') && (
        <textarea
          value={answer}
          onChange={(e) => onAnswerChange(e.target.value)}
          placeholder="Type your answer here..."
          className={`w-full p-4 border-2 border-gray-200 rounded-lg focus:border-blue-600 focus:outline-none transition-colors ${
            question.question_type === 'essay' ? 'min-h-[200px]' : 'min-h-[100px]'
          }`}
        />
      )}
    </Card>
  );
}
