from __future__ import annotations

from math import ceil
from typing import Any

from app.models.assessment import AssessmentAttempt, Question, StudentAnswer
from app.models.user import User, utc_now
from app.repositories.attempt import AttemptRepository
from app.schemas.attempt import (
    AssessmentCoachFeedback,
    AssessmentCoachQuestionInput,
    AttemptAnswerSaveRequest,
    AttemptDetailResponse,
    AttemptHistoryItem,
    AttemptListResponse,
    AttemptQuestion,
    AttemptQuestionOption,
    AttemptResultsResponse,
    OpenAnswerEvaluation,
    OpenAnswerEvaluationInput,
    PublicAttemptAnswer,
    ResultQuestion,
    ResultQuestionOption,
    StartAttemptResponse,
)
from app.services.objective_grader import ObjectiveQuestionGrader
from app.services.scoring import (
    calculate_percentage,
    level_from_percentage,
    round_score,
)


class AttemptServiceError(Exception):
    message = "La gestion de la tentative a echoue."


class AttemptNotFoundError(AttemptServiceError):
    message = "Impossible de charger cette tentative."


class AssessmentStartError(AttemptServiceError):
    message = "Impossible de commencer cette evaluation."


class AttemptAlreadyEvaluatedError(AttemptServiceError):
    message = "Cette tentative est deja terminee."


class InvalidAnswerError(AttemptServiceError):
    message = "La reponse selectionnee est invalide."


class AttemptNotEvaluatedError(AttemptServiceError):
    message = "Les resultats ne sont pas encore disponibles."


class AttemptEvaluationError(AttemptServiceError):
    message = "Impossible d'evaluer les reponses ouvertes."


class AttemptService:
    def __init__(
        self,
        *,
        repository: AttemptRepository,
        assessment_agent: Any,
        objective_grader: ObjectiveQuestionGrader | None = None,
    ) -> None:
        self._repository = repository
        self._assessment_agent = assessment_agent
        self._objective_grader = objective_grader or ObjectiveQuestionGrader()

    def start_or_resume(
        self,
        *,
        current_user: User,
        assessment_id: int,
    ) -> StartAttemptResponse:
        assessment = self._repository.get_assessment_for_user(
            assessment_id=assessment_id,
            user_id=current_user.id,
        )
        if assessment is None:
            raise AssessmentStartError
        if not assessment.questions:
            raise AssessmentStartError

        attempt = self._repository.get_in_progress_attempt(
            assessment_id=assessment_id,
            user_id=current_user.id,
        )
        if attempt is None:
            attempt = AssessmentAttempt(
                assessment_id=assessment.id,
                user_id=current_user.id,
                status="in_progress",
            )
            self._repository.add_attempt(attempt)
            self._repository.commit()
            attempt = self._repository.get_attempt_for_user(
                attempt_id=attempt.id,
                user_id=current_user.id,
            )

        if attempt is None:
            raise AttemptNotFoundError

        return StartAttemptResponse(
            id=attempt.id,
            assessment_id=assessment.id,
            status=attempt.status,
            started_at=attempt.started_at.isoformat(),
            answered_count=self._answered_count(attempt.answers),
            total_questions=len(assessment.questions),
        )

    def get_attempt(
        self,
        *,
        current_user: User,
        attempt_id: int,
    ) -> AttemptDetailResponse:
        attempt = self._get_attempt(current_user=current_user, attempt_id=attempt_id)
        return self._to_detail(attempt)

    def save_answer(
        self,
        *,
        current_user: User,
        attempt_id: int,
        question_id: int,
        request: AttemptAnswerSaveRequest,
    ) -> PublicAttemptAnswer:
        attempt = self._get_attempt(current_user=current_user, attempt_id=attempt_id)
        if attempt.status != "in_progress":
            raise AttemptAlreadyEvaluatedError

        question = self._question_for_attempt(attempt, question_id)
        selected_option_id, text_answer = self._validate_answer(question, request)

        answer = self._repository.get_answer(
            attempt_id=attempt.id,
            question_id=question.id,
        )
        if answer is None:
            answer = StudentAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
            )
            self._repository.add_answer(answer)

        answer.selected_option_id = selected_option_id
        answer.text_answer = text_answer
        answer.is_flagged = request.is_flagged
        answer.evaluation_status = None
        answer.is_correct = None
        answer.points_awarded = None
        answer.feedback = None
        answer.missing_concepts = None
        self._repository.commit()

        return self._to_public_answer(answer)

    def submit_attempt(
        self,
        *,
        current_user: User,
        attempt_id: int,
    ) -> AttemptResultsResponse:
        attempt = self._get_attempt(current_user=current_user, attempt_id=attempt_id)
        if attempt.status == "evaluated":
            return self._to_results(attempt)
        if attempt.status != "in_progress":
            raise AttemptAlreadyEvaluatedError

        attempt.status = "evaluating"
        self._repository.commit()

        try:
            grades = self._evaluate_attempt(attempt)
        except Exception as exc:
            self._repository.rollback()
            attempt = self._get_attempt(
                current_user=current_user,
                attempt_id=attempt_id,
            )
            attempt.status = "in_progress"
            self._repository.commit()
            raise AttemptEvaluationError from exc

        attempt = self._get_attempt(current_user=current_user, attempt_id=attempt_id)
        now = utc_now()
        score = 0.0
        max_score = 0.0

        for question in attempt.assessment.questions:
            max_score += float(question.points)
            answer = self._answer_for_question(attempt, question.id)
            if answer is None:
                answer = StudentAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                )
                self._repository.add_answer(answer)

            grade = grades[question.id]
            answer.selected_option_id = grade.get("selected_option_id")
            answer.text_answer = grade.get("text_answer")
            answer.evaluation_status = grade["evaluation_status"]
            answer.is_correct = grade["evaluation_status"] == "correct"
            answer.points_awarded = grade["points_awarded"]
            answer.feedback = grade["feedback"]
            answer.missing_concepts = grade["missing_concepts"]
            score += float(grade["points_awarded"])

        percentage = calculate_percentage(score, max_score)
        attempt.score = round_score(score)
        attempt.max_score = round_score(max_score)
        attempt.percentage = percentage
        attempt.level = level_from_percentage(percentage)
        attempt.strong_topics, attempt.weak_topics = self._topic_analysis(attempt)
        attempt.submitted_at = now
        attempt.evaluated_at = now
        attempt.status = "evaluated"
        self._repository.commit()

        attempt = self._get_attempt(current_user=current_user, attempt_id=attempt_id)
        return self._to_results(attempt)

    def get_results(
        self,
        *,
        current_user: User,
        attempt_id: int,
    ) -> AttemptResultsResponse:
        attempt = self._get_attempt(current_user=current_user, attempt_id=attempt_id)
        if attempt.status != "evaluated":
            raise AttemptNotEvaluatedError
        return self._to_results(attempt)

    def list_attempts(
        self,
        *,
        current_user: User,
        assessment_id: int,
        page: int,
        page_size: int,
        status: str | None,
    ) -> AttemptListResponse:
        assessment = self._repository.get_assessment_for_user(
            assessment_id=assessment_id,
            user_id=current_user.id,
        )
        if assessment is None:
            raise AssessmentStartError

        offset = (page - 1) * page_size
        attempts, total = self._repository.list_for_assessment(
            assessment_id=assessment_id,
            user_id=current_user.id,
            limit=page_size,
            offset=offset,
            status=status,
        )
        return AttemptListResponse(
            items=[
                self._to_history_item(attempt, len(assessment.questions))
                for attempt in attempts
            ],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )

    def _evaluate_attempt(
        self,
        attempt: AssessmentAttempt,
    ) -> dict[int, dict[str, Any]]:
        grades: dict[int, dict[str, Any]] = {}
        open_inputs: list[OpenAnswerEvaluationInput] = []

        for question in attempt.assessment.questions:
            answer = self._answer_for_question(attempt, question.id)
            if question.type in {"multiple_choice", "true_false"}:
                if answer is None:
                    answer = StudentAnswer(
                        attempt_id=attempt.id,
                        question_id=question.id,
                    )
                grade = self._objective_grader.grade(question=question, answer=answer)
                grades[question.id] = {
                    "selected_option_id": answer.selected_option_id,
                    "text_answer": None,
                    "points_awarded": grade.points_awarded,
                    "evaluation_status": grade.evaluation_status,
                    "feedback": grade.feedback,
                    "missing_concepts": grade.missing_concepts,
                }
                continue

            if answer is None or not (answer.text_answer or "").strip():
                grades[question.id] = self._unanswered_open_grade(answer)
                continue

            open_inputs.append(
                OpenAnswerEvaluationInput(
                    question_id=question.id,
                    question_type=question.type,
                    question_text=question.text,
                    expected_answer=question.correct_answer,
                    rubric=question.explanation,
                    max_points=float(question.points),
                    learner_answer=answer.text_answer or "",
                    source_excerpt=question.source_excerpt,
                    topic=question.source_document.title
                    if question.source_document is not None
                    else None,
                )
            )

        for evaluation in self._evaluate_open_inputs(open_inputs):
            answer = self._answer_for_question(attempt, evaluation.question_id)
            grades[evaluation.question_id] = {
                "selected_option_id": None,
                "text_answer": answer.text_answer if answer is not None else None,
                "points_awarded": evaluation.points_awarded,
                "evaluation_status": evaluation.evaluation_status,
                "feedback": evaluation.feedback,
                "missing_concepts": evaluation.missing_concepts,
            }

        if set(grades) != {question.id for question in attempt.assessment.questions}:
            raise ValueError("Missing question grades.")

        return grades

    def _evaluate_open_inputs(
        self,
        inputs: list[OpenAnswerEvaluationInput],
    ) -> list[OpenAnswerEvaluation]:
        if not inputs:
            return []
        return self._assessment_agent.evaluate_open_answers(inputs)

    def _unanswered_open_grade(self, answer: StudentAnswer | None) -> dict[str, Any]:
        return {
            "selected_option_id": None,
            "text_answer": answer.text_answer if answer is not None else None,
            "points_awarded": 0.0,
            "evaluation_status": "unanswered",
            "feedback": "Aucune reponse fournie.",
            "missing_concepts": [],
        }

    def _validate_answer(
        self,
        question: Question,
        request: AttemptAnswerSaveRequest,
    ) -> tuple[int | None, str | None]:
        if question.type in {"multiple_choice", "true_false"}:
            if request.selected_option_id is None:
                return None, None
            option_ids = {option.id for option in question.options}
            if request.selected_option_id not in option_ids:
                raise InvalidAnswerError
            return request.selected_option_id, None

        if request.selected_option_id is not None:
            raise InvalidAnswerError
        return None, request.text_answer

    def _question_for_attempt(
        self,
        attempt: AssessmentAttempt,
        question_id: int,
    ) -> Question:
        question = next(
            (item for item in attempt.assessment.questions if item.id == question_id),
            None,
        )
        if question is None:
            raise InvalidAnswerError
        return question

    def _get_attempt(self, *, current_user: User, attempt_id: int) -> AssessmentAttempt:
        attempt = self._repository.get_attempt_for_user(
            attempt_id=attempt_id,
            user_id=current_user.id,
        )
        if attempt is None:
            raise AttemptNotFoundError
        return attempt

    def _answer_for_question(
        self,
        attempt: AssessmentAttempt,
        question_id: int,
    ) -> StudentAnswer | None:
        return next(
            (answer for answer in attempt.answers if answer.question_id == question_id),
            None,
        )

    def _answered_count(self, answers: list[StudentAnswer]) -> int:
        return sum(
            1
            for answer in answers
            if answer.selected_option_id is not None or bool(answer.text_answer)
        )

    def _topic_analysis(
        self,
        attempt: AssessmentAttempt,
    ) -> tuple[list[str], list[str]]:
        by_topic: dict[str, list[float]] = {}
        for question in attempt.assessment.questions:
            answer = self._answer_for_question(attempt, question.id)
            if answer is None or answer.points_awarded is None:
                continue
            topic = (
                question.source_document.title
                if question.source_document is not None
                else None
            )
            if not topic:
                continue
            by_topic.setdefault(topic, []).append(
                float(answer.points_awarded) / max(float(question.points), 1.0),
            )

        strong = [
            topic
            for topic, values in by_topic.items()
            if values and sum(values) / len(values) >= 0.75
        ]
        weak = [
            topic
            for topic, values in by_topic.items()
            if values and sum(values) / len(values) < 0.55
        ]
        return strong[:5], weak[:5]

    def _to_detail(self, attempt: AssessmentAttempt) -> AttemptDetailResponse:
        answers = [self._to_public_answer(answer) for answer in attempt.answers]
        return AttemptDetailResponse(
            id=attempt.id,
            assessment_id=attempt.assessment_id,
            assessment_title=attempt.assessment.title,
            difficulty=attempt.assessment.difficulty,
            status=attempt.status,
            started_at=attempt.started_at.isoformat(),
            submitted_at=self._optional_iso(attempt.submitted_at),
            evaluated_at=self._optional_iso(attempt.evaluated_at),
            answered_count=self._answered_count(attempt.answers),
            flagged_count=sum(1 for answer in attempt.answers if answer.is_flagged),
            total_questions=len(attempt.assessment.questions),
            questions=[
                AttemptQuestion(
                    id=question.id,
                    type=question.type,
                    text=question.text,
                    points=question.points,
                    order_index=question.order_index,
                    options=[
                        AttemptQuestionOption(
                            id=option.id,
                            text=option.text,
                            order_index=option.order_index,
                        )
                        for option in question.options
                    ],
                )
                for question in attempt.assessment.questions
            ],
            answers=answers,
        )

    def _to_public_answer(self, answer: StudentAnswer) -> PublicAttemptAnswer:
        return PublicAttemptAnswer(
            question_id=answer.question_id,
            selected_option_id=answer.selected_option_id,
            text_answer=answer.text_answer,
            is_flagged=answer.is_flagged,
            evaluation_status=answer.evaluation_status,
            is_correct=answer.is_correct,
            points_awarded=self._optional_float(answer.points_awarded),
            feedback=answer.feedback,
            missing_concepts=answer.missing_concepts or [],
        )

    def _to_history_item(
        self,
        attempt: AssessmentAttempt,
        total_questions: int,
    ) -> AttemptHistoryItem:
        return AttemptHistoryItem(
            id=attempt.id,
            assessment_id=attempt.assessment_id,
            status=attempt.status,
            score=self._optional_float(attempt.score),
            max_score=self._optional_float(attempt.max_score),
            percentage=self._optional_float(attempt.percentage),
            level=attempt.level,
            started_at=attempt.started_at.isoformat(),
            submitted_at=self._optional_iso(attempt.submitted_at),
            evaluated_at=self._optional_iso(attempt.evaluated_at),
            answered_count=self._answered_count(attempt.answers),
            total_questions=total_questions,
        )

    def _to_results(self, attempt: AssessmentAttempt) -> AttemptResultsResponse:
        if (
            attempt.score is None
            or attempt.max_score is None
            or attempt.percentage is None
            or attempt.level is None
            or attempt.submitted_at is None
            or attempt.evaluated_at is None
        ):
            raise AttemptNotEvaluatedError

        return AttemptResultsResponse(
            id=attempt.id,
            assessment_id=attempt.assessment_id,
            assessment_title=attempt.assessment.title,
            difficulty=attempt.assessment.difficulty,
            status="evaluated",
            score=float(attempt.score),
            max_score=float(attempt.max_score),
            percentage=float(attempt.percentage),
            level=attempt.level,
            strong_topics=attempt.strong_topics or [],
            weak_topics=attempt.weak_topics or [],
            started_at=attempt.started_at.isoformat(),
            submitted_at=attempt.submitted_at.isoformat(),
            evaluated_at=attempt.evaluated_at.isoformat(),
            coach_feedback=self._coach_feedback(attempt),
            questions=[
                self._to_result_question(attempt, question)
                for question in attempt.assessment.questions
            ],
        )

    def _coach_feedback(
        self,
        attempt: AssessmentAttempt,
    ) -> AssessmentCoachFeedback | None:
        questions: list[AssessmentCoachQuestionInput] = []
        for question in attempt.assessment.questions:
            answer = self._answer_for_question(attempt, question.id)
            if answer is None or answer.evaluation_status is None:
                continue
            questions.append(
                AssessmentCoachQuestionInput(
                    question_id=question.id,
                    question_text=question.text,
                    expected_answer=question.correct_answer,
                    explanation=question.explanation,
                    points=float(question.points),
                    points_awarded=float(answer.points_awarded or 0),
                    evaluation_status=answer.evaluation_status,
                    feedback=answer.feedback,
                    missing_concepts=answer.missing_concepts or [],
                    source_document_id=question.source_document_id,
                    source_document_title=question.source_document.title,
                    source_page_number=question.source_page_number,
                    source_excerpt=question.source_excerpt,
                )
            )

        if not hasattr(self._assessment_agent, "analyze_attempt"):
            return None

        return self._assessment_agent.analyze_attempt(
            score_percent=float(attempt.percentage or 0),
            questions=questions,
        )

    def _to_result_question(
        self,
        attempt: AssessmentAttempt,
        question: Question,
    ) -> ResultQuestion:
        answer = self._answer_for_question(attempt, question.id)
        if answer is None:
            raise AttemptNotEvaluatedError
        return ResultQuestion(
            id=question.id,
            type=question.type,
            text=question.text,
            points=question.points,
            order_index=question.order_index,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            source_document_id=question.source_document_id,
            source_document_title=question.source_document.title,
            source_page_number=question.source_page_number,
            source_excerpt=question.source_excerpt,
            options=[
                ResultQuestionOption(
                    id=option.id,
                    text=option.text,
                    order_index=option.order_index,
                    is_correct=option.is_correct,
                )
                for option in question.options
            ],
            learner_answer=self._to_public_answer(answer),
        )

    def _optional_iso(self, value: Any) -> str | None:
        return value.isoformat() if value is not None else None

    def _optional_float(self, value: Any) -> float | None:
        return float(value) if value is not None else None
