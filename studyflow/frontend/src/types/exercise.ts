/**
 * Exercise type definitions
 */

export type DifficultyLevel = 'beginner' | 'easy' | 'medium' | 'hard' | 'expert';
export type QuestionType = 'multiple_choice' | 'short_answer' | 'essay' | 'true_false';
export type ExerciseStatus = 'draft' | 'ready' | 'archived';

export interface MCQOption {
  label: string;
  text: string;
  is_correct: boolean;
}

export interface ExerciseQuestion {
  question_id: string;
  question_type: QuestionType;
  question_text: string;
  options?: MCQOption[];
  correct_answer: string;
  acceptable_answers: string[];
  explanation: string;
  topic: string;
  difficulty: DifficultyLevel;
  points: number;
  hints?: string[];
}

export interface Exercise {
  id: string;
  title: string;
  description?: string;
  subject: string;
  topics: string[];
  difficulty: DifficultyLevel;
  total_points: number;
  num_questions: number;
  time_limit_minutes?: number;
  passing_score_percentage: number;
  created_by: string;
  created_at: string;
  status: ExerciseStatus;
}

export interface ExerciseDetail extends Exercise {
  questions: ExerciseQuestion[];
}

export interface StudentAnswer {
  question_id: string;
  answer: string;
  is_correct?: boolean;
  points_earned?: number;
  time_spent_seconds?: number;
}

export interface SubmissionResponse {
  id: string;
  exercise_id: string;
  student_id: string;
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  questions_correct: number;
  questions_total: number;
  time_taken_seconds: number;
  recommended_next_difficulty?: DifficultyLevel;
  weak_topics: string[];
  submitted_at: string;
}

export interface QuestionFeedback {
  question_id: string;
  question_number: number;
  question_text: string;
  question_type: QuestionType;
  student_answer: string;
  is_correct: boolean;
  points_earned: number;
  max_points: number;
  correct_answer: string;
  explanation: string;
  ai_feedback?: string;
  alternative_correct_answers: string[];
  topic: string;
  hints_if_incorrect: string[];
}

export interface PerformanceSummary {
  total_score: number;
  max_score: number;
  percentage: number;
  grade: string;
  passed: boolean;
  questions_total: number;
  questions_correct: number;
  questions_incorrect: number;
  strong_topics: string[];
  weak_topics: string[];
  accuracy_by_topic: Record<string, number>;
  time_taken_seconds: number;
  average_time_per_question: number;
  recommended_next_difficulty?: DifficultyLevel;
  recommendations: string[];
  focus_areas: string[];
}

export interface SubmissionFeedback {
  submission_id: string;
  exercise_id: string;
  student_id: string;
  question_feedback: QuestionFeedback[];
  performance: PerformanceSummary;
  submitted_at: string;
}
