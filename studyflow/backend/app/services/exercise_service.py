"""
Exercise generation service for StudyFlow.

Generates exercises from study materials using RAG, implements adaptive
difficulty, and manages submissions and performance tracking.
"""

import os
import sys
import json
import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from bson import ObjectId

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.integration.rag import RAGService, RAGConfig

from app.models.exercise import (
    Exercise,
    ExerciseQuestion,
    ExerciseSubmission,
    StudentPerformance,
    DifficultyLevel,
    QuestionType,
    ExerciseStatus,
    MCQOption,
    StudentAnswer,
    ExerciseGenerateRequest,
    ExerciseCreate,
    QuestionFeedback,
    PerformanceSummary,
    SubmissionFeedbackResponse,
    SubmissionResponse,
)
from app.models.material import StudyMaterial
from app.core.database import (
    mongodb,
    COLLECTION_MATERIALS,
)
from app.config import settings

logger = logging.getLogger(__name__)

# MongoDB collections
COLLECTION_EXERCISES = "exercises"
COLLECTION_SUBMISSIONS = "exercise_submissions"
COLLECTION_PERFORMANCE = "student_performance"


class ExerciseService:
    """
    Service for exercise generation and management.

    Uses RAG to generate contextual exercises from study materials
    with adaptive difficulty.
    """

    _rag_service: Optional[RAGService] = None

    @classmethod
    def get_rag_service(cls) -> RAGService:
        """
        Get or create RAG service instance.

        Returns:
            RAGService instance
        """
        if cls._rag_service is None:
            config = RAGConfig(
                postgres_host=settings.POSTGRES_HOST,
                postgres_port=settings.POSTGRES_PORT,
                postgres_user=settings.POSTGRES_USER,
                postgres_password=settings.POSTGRES_PASSWORD,
                postgres_db=settings.POSTGRES_DB,
                ai_provider=settings.AI_PROVIDER,
                api_key=settings.GEMINI_API_KEY,
                llm_model=settings.GEMINI_MODEL,
                embedding_model=settings.GEMINI_EMBEDDING_MODEL
            )
            cls._rag_service = RAGService(config)
            logger.info("✓ RAG Service initialized for exercise generation")

        return cls._rag_service

    @staticmethod
    async def get_material(material_id: str) -> Optional[StudyMaterial]:
        """
        Get material by ID.

        Args:
            material_id: Material ID

        Returns:
            Material or None
        """
        try:
            collection = mongodb.get_collection(COLLECTION_MATERIALS)
            material_doc = await collection.find_one({"_id": ObjectId(material_id)})

            if material_doc:
                material_doc["id"] = str(material_doc.pop("_id"))

                # Fix legacy data
                if "file_name" not in material_doc and "title" in material_doc:
                    material_doc["file_name"] = material_doc["title"]
                if material_doc.get("status") == "processed":
                    material_doc["status"] = "completed"

                return StudyMaterial(**material_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting material: {e}")
            return None

    @staticmethod
    def _build_generation_prompt(
        material_content: str,
        topic: Optional[str],
        difficulty: DifficultyLevel,
        num_questions: int,
        question_types: List[QuestionType]
    ) -> str:
        """
        Build prompt for exercise generation.

        Args:
            material_content: Study material content
            topic: Specific topic focus
            difficulty: Difficulty level
            num_questions: Number of questions
            question_types: Types of questions

        Returns:
            Formatted prompt
        """
        types_str = ", ".join([qt.value for qt in question_types])

        prompt = f"""Generate {num_questions} {difficulty.value} difficulty educational questions based on the following study material.

Question types to generate: {types_str}

Study Material:
{material_content[:4000]}  # Limit context size

"""
        if topic:
            prompt += f"\nFocus on topic: {topic}\n"

        prompt += """
Requirements:
1. Each question must test understanding, not just memorization
2. For multiple choice: provide 4 options (A, B, C, D) with ONE correct answer
3. For true/false: provide a clear statement
4. For short answer: expect 1-3 sentence responses
5. Include detailed explanations for all correct answers
6. Ensure questions are at {{difficulty}} level

Return your response as a JSON array with this exact structure:
[
  {{
    "question_type": "multiple_choice" | "short_answer" | "essay" | "true_false",
    "question_text": "The actual question",
    "options": [  // Only for multiple_choice and true_false
      {{"label": "A", "text": "Option text", "is_correct": false}},
      {{"label": "B", "text": "Option text", "is_correct": true}},
      ...
    ],
    "correct_answer": "B" or "The answer text",
    "acceptable_answers": ["Alternative answer 1", "Alternative answer 2"],  // Optional
    "explanation": "Detailed explanation of why this is correct",
    "topic": "Specific topic this question covers",
    "points": 1
  }}
]

Generate exactly {{num_questions}} questions now:
""".format(difficulty=difficulty.value, num_questions=num_questions)

        return prompt

    @staticmethod
    def _parse_generated_questions(
        ai_response: str,
        difficulty: DifficultyLevel,
        source_material_id: str
    ) -> List[ExerciseQuestion]:
        """
        Parse AI response into structured questions.

        Args:
            ai_response: Raw AI response
            difficulty: Difficulty level
            source_material_id: Source material ID

        Returns:
            List of ExerciseQuestion objects

        Raises:
            ValueError: If parsing fails
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[[\s\S]*\]', ai_response)
            if not json_match:
                raise ValueError("No JSON array found in response")

            questions_data = json.loads(json_match.group())

            questions = []
            for idx, q_data in enumerate(questions_data):
                # Parse options for MCQ/True-False
                options = None
                if q_data.get("options"):
                    options = [
                        MCQOption(
                            label=opt["label"],
                            text=opt["text"],
                            is_correct=opt.get("is_correct", False)
                        )
                        for opt in q_data["options"]
                    ]

                # Create question
                question = ExerciseQuestion(
                    question_type=QuestionType(q_data["question_type"]),
                    question_text=q_data["question_text"],
                    options=options,
                    correct_answer=q_data["correct_answer"],
                    acceptable_answers=q_data.get("acceptable_answers", []),
                    explanation=q_data["explanation"],
                    topic=q_data.get("topic", "General"),
                    difficulty=difficulty,
                    points=q_data.get("points", 1),
                    source_material_id=source_material_id
                )
                questions.append(question)

            return questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response: {ai_response[:500]}")
            raise ValueError(f"Failed to parse AI response as JSON: {e}")
        except Exception as e:
            logger.error(f"Error parsing questions: {e}")
            raise ValueError(f"Failed to parse questions: {e}")

    @classmethod
    async def generate_exercise(
        cls,
        request: ExerciseGenerateRequest,
        organization_id: str,
        created_by: str,
        school_id: Optional[str] = None
    ) -> Exercise:
        """
        Generate exercise from study material using RAG.

        Args:
            request: Generation request
            organization_id: Organization ID
            created_by: User ID creating exercise
            school_id: School ID (optional)

        Returns:
            Generated exercise

        Raises:
            ValueError: If generation fails
        """
        # Get material
        material = await cls.get_material(request.material_id)
        if not material:
            raise ValueError(f"Material {request.material_id} not found")

        # Get RAG service
        rag = cls.get_rag_service()

        # Query RAG for relevant content
        context_query = f"Provide study content about {request.topic}" if request.topic else f"Summarize the key concepts in: {material.title}"

        # Use query_knowledge_base instead of query
        rag_result = await rag.query_knowledge_base(
            collection_name=material.embedding_collection,
            query=context_query
        )

        if not rag_result.success:
            raise ValueError(f"Failed to retrieve content from RAG: {rag_result.error_message}")

        # Use the RAG response as material content
        material_content = rag_result.response

        # Build generation prompt
        prompt = cls._build_generation_prompt(
            material_content,
            request.topic,
            request.difficulty,
            request.num_questions,
            request.question_types
        )

        # Generate questions using AI
        try:
            # Use the LLM directly for generation since RAG doesn't have generate()
            import asyncio
            response_text = await asyncio.to_thread(
                lambda: rag.llm.invoke(prompt).content
            )
            tokens_used = len(prompt.split()) + len(response_text.split())  # Approximate
            cost = tokens_used * 0.000001  # Approximate cost

        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            raise ValueError(f"Failed to generate exercise: {e}")

        # Parse questions
        try:
            questions = cls._parse_generated_questions(
                response_text,
                request.difficulty,
                request.material_id
            )
        except Exception as e:
            logger.error(f"Question parsing failed: {e}")
            raise ValueError(f"Failed to parse questions: {e}")

        if not questions:
            raise ValueError("No questions were generated")

        # Calculate total points
        total_points = sum(q.points for q in questions)

        # Create exercise
        exercise = Exercise(
            organization_id=organization_id,
            school_id=school_id,
            title=f"{material.title} - {request.difficulty.value.capitalize()} Exercise",
            description=f"Auto-generated exercise from {material.title}",
            subject=material.subject,
            topics=[request.topic] if request.topic else material.topics,
            questions=questions,
            total_points=total_points,
            difficulty=request.difficulty,
            generated_from_material_id=request.material_id,
            generation_prompt=prompt,
            generation_cost=cost,
            tokens_used=tokens_used,
            time_limit_minutes=request.time_limit_minutes,
            created_by=created_by,
            status=ExerciseStatus.READY
        )

        # Save to database
        collection = mongodb.get_collection(COLLECTION_EXERCISES)
        exercise_dict = exercise.model_dump(by_alias=True, exclude={"id"})
        result = await collection.insert_one(exercise_dict)
        exercise.id = str(result.inserted_id)

        logger.info(f"Generated exercise {exercise.id} with {len(questions)} questions")

        return exercise

    @staticmethod
    async def create_exercise(
        exercise_data: ExerciseCreate,
        organization_id: str,
        created_by: str,
        school_id: Optional[str] = None
    ) -> Exercise:
        """
        Manually create an exercise.

        Args:
            exercise_data: Exercise creation data
            organization_id: Organization ID
            created_by: User ID
            school_id: School ID (optional)

        Returns:
            Created exercise
        """
        total_points = sum(q.points for q in exercise_data.questions)

        exercise = Exercise(
            organization_id=organization_id,
            school_id=school_id,
            title=exercise_data.title,
            description=exercise_data.description,
            subject=exercise_data.subject,
            topics=exercise_data.topics,
            questions=exercise_data.questions,
            total_points=total_points,
            difficulty=exercise_data.difficulty,
            time_limit_minutes=exercise_data.time_limit_minutes,
            passing_score_percentage=exercise_data.passing_score_percentage,
            created_by=created_by,
            status=ExerciseStatus.READY
        )

        collection = mongodb.get_collection(COLLECTION_EXERCISES)
        exercise_dict = exercise.model_dump(by_alias=True, exclude={"id"})
        result = await collection.insert_one(exercise_dict)
        exercise.id = str(result.inserted_id)

        logger.info(f"Created manual exercise {exercise.id}")

        return exercise

    @staticmethod
    async def get_exercise(
        exercise_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[Exercise]:
        """
        Get exercise by ID.

        Args:
            exercise_id: Exercise ID
            organization_id: Organization ID for access control (None for universal admin)

        Returns:
            Exercise or None
        """
        try:
            query = {"_id": ObjectId(exercise_id)}
            if organization_id is not None:
                query["organization_id"] = organization_id

            collection = mongodb.get_collection(COLLECTION_EXERCISES)
            exercise_doc = await collection.find_one(query)

            if exercise_doc:
                exercise_doc["id"] = str(exercise_doc.pop("_id"))
                return Exercise(**exercise_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting exercise: {e}")
            return None

    @staticmethod
    async def list_exercises(
        organization_id: Optional[str] = None,
        subject: Optional[str] = None,
        difficulty: Optional[DifficultyLevel] = None,
        created_by: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Exercise]:
        """
        List exercises with filtering.

        Args:
            organization_id: Filter by organization (None for universal admin)
            subject: Filter by subject
            difficulty: Filter by difficulty
            created_by: Filter by creator
            limit: Max results
            skip: Skip count

        Returns:
            List of exercises
        """
        query = {}
        if organization_id is not None:
            query["organization_id"] = organization_id
        if subject:
            query["subject"] = subject
        if difficulty:
            query["difficulty"] = difficulty.value
        if created_by:
            query["created_by"] = created_by

        collection = mongodb.get_collection(COLLECTION_EXERCISES)
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

        exercises = []
        async for exercise_doc in cursor:
            exercise_doc["id"] = str(exercise_doc.pop("_id"))
            exercises.append(Exercise(**exercise_doc))

        return exercises

    @staticmethod
    async def submit_exercise(
        exercise_id: str,
        student_id: str,
        answers: List[StudentAnswer],
        time_taken_seconds: int,
        organization_id: str
    ) -> ExerciseSubmission:
        """
        Submit exercise and calculate score.

        Args:
            exercise_id: Exercise ID
            student_id: Student ID
            answers: Student answers
            time_taken_seconds: Time taken
            organization_id: Organization ID

        Returns:
            Exercise submission with score

        Raises:
            ValueError: If exercise not found
        """
        # Get exercise
        exercise = await ExerciseService.get_exercise(exercise_id)
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")

        # Score answers
        questions_correct = 0
        total_score = 0.0
        max_score = exercise.total_points

        # Create answer lookup
        answer_map = {ans.question_id: ans for ans in answers}

        # Score each question
        for question in exercise.questions:
            student_ans = answer_map.get(question.question_id)
            if not student_ans:
                continue

            # Check if correct based on question type
            is_correct = False
            points_earned = 0.0

            if question.question_type == QuestionType.MULTIPLE_CHOICE:
                # Auto-grade MCQs
                is_correct = student_ans.answer.strip().upper() == question.correct_answer.strip().upper()
                points_earned = question.points if is_correct else 0
            elif question.question_type in [QuestionType.SHORT_ANSWER, QuestionType.ESSAY]:
                # Use AI grading for text answers
                is_correct, points_earned, ai_feedback = await ExerciseService.grade_short_answer_with_ai(
                    question=question,
                    student_answer=student_ans.answer,
                    use_rubric=True
                )
                # Store AI feedback in answer metadata (if we want to access it later)
                if not hasattr(student_ans, 'metadata'):
                    student_ans.metadata = {}
                student_ans.metadata = {"ai_feedback": ai_feedback}
            else:
                # TRUE_FALSE - treat like MCQ
                is_correct = student_ans.answer.strip().upper() == question.correct_answer.strip().upper()
                points_earned = question.points if is_correct else 0

            student_ans.is_correct = is_correct
            student_ans.points_earned = points_earned
            total_score += points_earned
            if is_correct:
                questions_correct += 1

        # Calculate percentage
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= exercise.passing_score_percentage

        # Analyze weak/strong topics
        topic_performance: Dict[str, List[bool]] = {}
        for question in exercise.questions:
            student_ans = answer_map.get(question.question_id)
            if student_ans and student_ans.is_correct is not None:
                if question.topic not in topic_performance:
                    topic_performance[question.topic] = []
                topic_performance[question.topic].append(student_ans.is_correct)

        weak_topics = [
            topic for topic, results in topic_performance.items()
            if sum(results) / len(results) < 0.6  # Less than 60% correct
        ]
        strong_topics = [
            topic for topic, results in topic_performance.items()
            if sum(results) / len(results) >= 0.8  # 80% or more correct
        ]

        # Determine next difficulty
        recommended_next_difficulty = await ExerciseService._calculate_next_difficulty(
            student_id,
            exercise.subject,
            percentage,
            exercise.difficulty
        )

        # Create submission
        submission = ExerciseSubmission(
            exercise_id=exercise_id,
            student_id=student_id,
            organization_id=organization_id,
            answers=answers,
            score=total_score,
            max_score=max_score,
            percentage=percentage,
            passed=passed,
            time_taken_seconds=time_taken_seconds,
            questions_correct=questions_correct,
            questions_total=len(exercise.questions),
            difficulty_level=exercise.difficulty,
            recommended_next_difficulty=recommended_next_difficulty,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
            started_at=datetime.utcnow()  # Simplified, should track actual start
        )

        # Save submission
        collection = mongodb.get_collection(COLLECTION_SUBMISSIONS)
        submission_dict = submission.model_dump(by_alias=True, exclude={"id"})
        result = await collection.insert_one(submission_dict)
        submission.id = str(result.inserted_id)

        # Update performance tracking
        await ExerciseService._update_performance(
            student_id,
            exercise.subject,
            exercise.topics,
            percentage,
            exercise.difficulty,
            topic_performance
        )

        logger.info(f"Submission {submission.id}: {questions_correct}/{len(exercise.questions)} correct, {percentage:.1f}%")

        return submission

    @staticmethod
    async def _calculate_next_difficulty(
        student_id: str,
        subject: str,
        score_percentage: float,
        current_difficulty: DifficultyLevel
    ) -> DifficultyLevel:
        """
        Calculate recommended next difficulty based on performance.

        Logic:
        - Score >= 80%: Increase difficulty
        - Score < 60%: Decrease difficulty
        - Otherwise: Keep same

        Args:
            student_id: Student ID
            subject: Subject
            score_percentage: Score percentage
            current_difficulty: Current difficulty

        Returns:
            Recommended difficulty level
        """
        difficulty_order = [
            DifficultyLevel.BEGINNER,
            DifficultyLevel.EASY,
            DifficultyLevel.MEDIUM,
            DifficultyLevel.HARD,
            DifficultyLevel.EXPERT
        ]

        current_idx = difficulty_order.index(current_difficulty)

        # Increase difficulty if score >= 80%
        if score_percentage >= 80 and current_idx < len(difficulty_order) - 1:
            return difficulty_order[current_idx + 1]

        # Decrease difficulty if score < 60%
        if score_percentage < 60 and current_idx > 0:
            return difficulty_order[current_idx - 1]

        # Otherwise keep same
        return current_difficulty

    @staticmethod
    async def _update_performance(
        student_id: str,
        subject: str,
        topics: List[str],
        score_percentage: float,
        difficulty: DifficultyLevel,
        topic_performance: Dict[str, List[bool]]
    ):
        """
        Update student performance tracking.

        Args:
            student_id: Student ID
            subject: Subject
            topics: Topics covered
            score_percentage: Score percentage
            difficulty: Difficulty level
            topic_performance: Per-topic performance
        """
        collection = mongodb.get_collection(COLLECTION_PERFORMANCE)

        # Get or create performance record
        perf_doc = await collection.find_one({"student_id": student_id, "subject": subject})

        if perf_doc:
            # Update existing
            perf = StudentPerformance(**perf_doc)

            # Update metrics
            perf.total_exercises += 1
            perf.recent_scores.append(score_percentage)
            if len(perf.recent_scores) > 5:
                perf.recent_scores = perf.recent_scores[-5:]
            perf.average_recent_score = sum(perf.recent_scores) / len(perf.recent_scores)

            # Update difficulty tracking
            if difficulty.value not in perf.exercises_by_difficulty:
                perf.exercises_by_difficulty[difficulty.value] = 0
            perf.exercises_by_difficulty[difficulty.value] += 1

            # Update topic scores
            for topic, results in topic_performance.items():
                avg_score = sum(results) / len(results) * 100
                if topic in perf.topic_scores:
                    # Moving average
                    perf.topic_scores[topic] = (perf.topic_scores[topic] + avg_score) / 2
                else:
                    perf.topic_scores[topic] = avg_score

            # Identify weak and mastered topics
            perf.weak_topics = [t for t, s in perf.topic_scores.items() if s < 60]
            perf.mastered_topics = [t for t, s in perf.topic_scores.items() if s >= 85]

            perf.last_exercise_at = datetime.utcnow()
            perf.updated_at = datetime.utcnow()

            await collection.update_one(
                {"_id": perf_doc["_id"]},
                {"$set": perf.model_dump(exclude={"id"})}
            )

        else:
            # Create new
            perf = StudentPerformance(
                student_id=student_id,
                subject=subject,
                total_exercises=1,
                recent_scores=[score_percentage],
                average_recent_score=score_percentage,
                current_difficulty=difficulty,
                exercises_by_difficulty={difficulty.value: 1},
                topic_scores={
                    topic: sum(results) / len(results) * 100
                    for topic, results in topic_performance.items()
                },
                weak_topics=[t for t, results in topic_performance.items() if sum(results) / len(results) < 0.6],
                mastered_topics=[t for t, results in topic_performance.items() if sum(results) / len(results) >= 0.85],
                last_exercise_at=datetime.utcnow()
            )

            await collection.insert_one(perf.model_dump(exclude={"id"}))

    @classmethod
    async def grade_short_answer_with_ai(
        cls,
        question: ExerciseQuestion,
        student_answer: str,
        use_rubric: bool = True
    ) -> Tuple[bool, float, str]:
        """
        Grade short answer using AI with rubric-based evaluation.

        Args:
            question: The question being graded
            student_answer: Student's answer
            use_rubric: Use AI rubric-based grading

        Returns:
            Tuple of (is_correct, points_earned, feedback)
        """
        if not use_rubric:
            # Fallback to simple matching
            student_text = student_answer.strip().lower()
            correct_answers = [question.correct_answer.lower()] + [
                a.lower() for a in question.acceptable_answers
            ]
            is_correct = any(
                student_text in ans or ans in student_text
                for ans in correct_answers
            )
            points = question.points if is_correct else 0
            feedback = "Correct!" if is_correct else f"Expected: {question.correct_answer}"
            return is_correct, points, feedback

        # AI-powered grading
        try:
            rag = cls.get_rag_service()

            grading_prompt = f"""Grade the following student answer using a rubric.

Question: {question.question_text}
Topic: {question.topic}
Difficulty: {question.difficulty.value}

Correct Answer: {question.correct_answer}
Acceptable Alternatives: {', '.join(question.acceptable_answers) if question.acceptable_answers else 'None'}

Student's Answer: {student_answer}

Grading Rubric:
- Full Credit ({question.points} points): Answer is correct and demonstrates understanding
- Partial Credit ({question.points * 0.5} points): Answer shows some understanding but is incomplete or partially incorrect
- No Credit (0 points): Answer is incorrect or irrelevant

Provide your response as JSON:
{{
    "is_correct": true/false,
    "points_earned": <float>,
    "feedback": "Specific feedback explaining the grade",
    "key_concepts_identified": ["concept1", "concept2"]
}}
"""

            # Use LLM directly
            import asyncio
            response_text = await asyncio.to_thread(
                lambda: rag.llm.invoke(grading_prompt).content
            )

            # Parse AI response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                grading_data = json.loads(json_match.group())
                is_correct = grading_data.get("is_correct", False)
                points_earned = float(grading_data.get("points_earned", 0))
                feedback = grading_data.get("feedback", "")

                # Ensure points don't exceed max
                points_earned = min(points_earned, question.points)

                return is_correct, points_earned, feedback

            # Fallback if parsing fails
            logger.warning("AI grading response parsing failed, using fallback")
            return False, 0, "Could not grade answer automatically"

        except Exception as e:
            logger.error(f"AI grading failed: {e}")
            # Fallback to simple matching
            return await cls.grade_short_answer_with_ai(
                question=question,
                student_answer=student_answer,
                use_rubric=False
            )

    @staticmethod
    def _calculate_grade(percentage: float) -> str:
        """
        Calculate letter grade from percentage.

        Args:
            percentage: Score percentage

        Returns:
            Letter grade (A, B, C, D, F)
        """
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"

    @staticmethod
    def _generate_recommendations(
        percentage: float,
        weak_topics: List[str],
        strong_topics: List[str],
        difficulty: DifficultyLevel,
        recommended_next_difficulty: Optional[DifficultyLevel]
    ) -> List[str]:
        """
        Generate actionable recommendations for student.

        Args:
            percentage: Score percentage
            weak_topics: Topics needing improvement
            strong_topics: Topics mastered
            difficulty: Current difficulty
            recommended_next_difficulty: Recommended next difficulty

        Returns:
            List of recommendations
        """
        recommendations = []

        # Performance-based recommendations
        if percentage >= 90:
            recommendations.append("Excellent work! You've mastered this material.")
            if recommended_next_difficulty and recommended_next_difficulty != difficulty:
                recommendations.append(f"Try {recommended_next_difficulty.value} exercises to challenge yourself further.")
        elif percentage >= 80:
            recommendations.append("Great job! You have a strong understanding of this material.")
            if strong_topics:
                recommendations.append(f"You excel at: {', '.join(strong_topics[:3])}")
        elif percentage >= 70:
            recommendations.append("Good effort! You're on the right track.")
            recommendations.append("Review the explanations for questions you missed.")
        elif percentage >= 60:
            recommendations.append("You're making progress but need more practice.")
            recommendations.append("Review the material and try again.")
        else:
            recommendations.append("This material needs more study.")
            recommendations.append("Consider reviewing the study materials before retrying.")

        # Topic-specific recommendations
        if weak_topics:
            recommendations.append(f"Focus on improving: {', '.join(weak_topics[:3])}")
            recommendations.append("Use the explanations provided to understand these topics better.")

        # Study tips
        if percentage < 80:
            recommendations.append("Take notes while reviewing the explanations.")
            recommendations.append("Try creating flashcards for key concepts.")

        return recommendations

    @classmethod
    async def get_submission_feedback(
        cls,
        submission_id: str
    ) -> Optional[SubmissionFeedbackResponse]:
        """
        Get detailed feedback for a submission.

        Args:
            submission_id: Submission ID

        Returns:
            Detailed feedback or None
        """
        # Get submission
        collection = mongodb.get_collection(COLLECTION_SUBMISSIONS)
        submission_doc = await collection.find_one({"_id": ObjectId(submission_id)})

        if not submission_doc:
            return None

        submission_doc["id"] = str(submission_doc.pop("_id"))
        submission = ExerciseSubmission(**submission_doc)

        # Get exercise
        exercise = await cls.get_exercise(submission.exercise_id)
        if not exercise:
            return None

        # Build per-question feedback
        question_feedback_list = []
        answer_map = {ans.question_id: ans for ans in submission.answers}

        for idx, question in enumerate(exercise.questions):
            student_ans = answer_map.get(question.question_id)

            if student_ans:
                # Generate feedback for this question
                feedback = QuestionFeedback(
                    question_id=question.question_id,
                    question_number=idx + 1,
                    question_text=question.question_text,
                    question_type=question.question_type,
                    student_answer=student_ans.answer,
                    is_correct=student_ans.is_correct or False,
                    points_earned=student_ans.points_earned,
                    max_points=question.points,
                    correct_answer=question.correct_answer,
                    explanation=question.explanation,
                    alternative_correct_answers=question.acceptable_answers,
                    topic=question.topic,
                    hints_if_incorrect=question.hints if not student_ans.is_correct else []
                )
                question_feedback_list.append(feedback)

        # Calculate topic accuracy
        topic_performance: Dict[str, List[bool]] = {}
        for feedback in question_feedback_list:
            if feedback.topic not in topic_performance:
                topic_performance[feedback.topic] = []
            topic_performance[feedback.topic].append(feedback.is_correct)

        accuracy_by_topic = {
            topic: (sum(results) / len(results) * 100)
            for topic, results in topic_performance.items()
        }

        # Generate recommendations
        recommendations = cls._generate_recommendations(
            submission.percentage,
            submission.weak_topics,
            submission.strong_topics,
            submission.difficulty_level,
            submission.recommended_next_difficulty
        )

        # Focus areas
        focus_areas = []
        if submission.weak_topics:
            focus_areas.append(f"Review: {', '.join(submission.weak_topics[:3])}")
        if submission.percentage < 70:
            focus_areas.append("Review study materials thoroughly")
        if submission.percentage >= 80:
            focus_areas.append("You're ready for more advanced material")

        # Build performance summary
        performance = PerformanceSummary(
            total_score=submission.score,
            max_score=submission.max_score,
            percentage=submission.percentage,
            grade=cls._calculate_grade(submission.percentage),
            passed=submission.passed,
            questions_total=submission.questions_total,
            questions_correct=submission.questions_correct,
            questions_incorrect=submission.questions_total - submission.questions_correct,
            strong_topics=submission.strong_topics,
            weak_topics=submission.weak_topics,
            accuracy_by_topic=accuracy_by_topic,
            time_taken_seconds=submission.time_taken_seconds,
            average_time_per_question=submission.time_taken_seconds / submission.questions_total if submission.questions_total > 0 else 0,
            recommended_next_difficulty=submission.recommended_next_difficulty,
            recommendations=recommendations,
            focus_areas=focus_areas
        )

        return SubmissionFeedbackResponse(
            submission_id=submission.id,
            exercise_id=submission.exercise_id,
            student_id=submission.student_id,
            question_feedback=question_feedback_list,
            performance=performance,
            submitted_at=submission.submitted_at
        )

    @staticmethod
    async def get_performance(student_id: str, subject: str) -> Optional[StudentPerformance]:
        """
        Get student performance for a subject.

        Args:
            student_id: Student ID
            subject: Subject

        Returns:
            Performance data or None
        """
        collection = mongodb.get_collection(COLLECTION_PERFORMANCE)
        perf_doc = await collection.find_one({"student_id": student_id, "subject": subject})

        if perf_doc:
            return StudentPerformance(**perf_doc)
        return None

    @staticmethod
    async def get_user_submissions(
        user_id: str,
        limit: int = 100,
        skip: int = 0
    ) -> List[SubmissionResponse]:
        """
        Get all submissions for a user.

        Args:
            user_id: User ID
            limit: Maximum number of submissions to return
            skip: Number of submissions to skip for pagination

        Returns:
            List of submission responses with exercise details
        """
        submissions_collection = mongodb.get_collection(COLLECTION_SUBMISSIONS)
        exercises_collection = mongodb.get_collection(COLLECTION_EXERCISES)

        # Get submissions sorted by most recent first
        cursor = submissions_collection.find(
            {"student_id": user_id}
        ).sort("submitted_at", -1).skip(skip).limit(limit)

        submissions_list = await cursor.to_list(length=limit)

        # Build response with exercise details
        result = []
        for sub_doc in submissions_list:
            # Build submission response matching SubmissionResponse model
            submission_response = SubmissionResponse(
                id=str(sub_doc["_id"]),
                exercise_id=sub_doc["exercise_id"],
                student_id=sub_doc["student_id"],
                score=sub_doc["score"],
                max_score=sub_doc["max_score"],
                percentage=sub_doc["percentage"],
                passed=sub_doc["passed"],
                questions_correct=sub_doc["questions_correct"],
                questions_total=sub_doc["questions_total"],
                time_taken_seconds=sub_doc["time_taken_seconds"],
                recommended_next_difficulty=sub_doc.get("recommended_next_difficulty"),
                weak_topics=sub_doc.get("weak_topics", []),
                submitted_at=sub_doc["submitted_at"]
            )

            result.append(submission_response)

        return result
