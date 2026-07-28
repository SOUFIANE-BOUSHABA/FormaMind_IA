from __future__ import annotations

import json
from math import ceil
from pathlib import Path
from typing import Any

from app.agents.soutenance_coach_agent import (
    SoutenanceCoachAgent,
    SoutenanceCoachConfigurationError,
    SoutenanceCoachOutputError,
)
from app.core.config import Settings
from app.models.assessment import AssessmentAttempt
from app.models.soutenance import (
    SoutenanceAnswer,
    SoutenanceQuestion,
    SoutenanceRubricScore,
    SoutenanceSession,
)
from app.models.user import User, utc_now
from app.repositories.soutenance import SoutenanceRepository
from app.schemas.soutenance import (
    CATEGORY_LABELS,
    RUBRIC_CRITERIA,
    CreateSoutenanceSessionRequest,
    LearnerProfileSnapshot,
    ProjectContextSnapshot,
    PublicSoutenanceQuestion,
    SoutenanceAnswerEvaluationDraft,
    SoutenanceAnswerFeedback,
    SoutenanceCategoryScore,
    SoutenanceCurrentQuestionResponse,
    SoutenanceQuestionResult,
    SoutenanceResultsResponse,
    SoutenanceRubricCriterionRead,
    SoutenanceSessionDraft,
    SoutenanceSessionListItem,
    SoutenanceSessionListResponse,
    SoutenanceSessionRead,
    SubmitSoutenanceAnswerRequest,
    SubmitSoutenanceAnswerResponse,
)
from app.tools.soutenance_tools import (
    LearnerProfileTool,
    ProjectContextTool,
    SoutenanceRubricTool,
)


class SoutenanceServiceError(Exception):
    message = "La gestion de la simulation de soutenance a echoue."


class SoutenanceSessionNotFoundError(SoutenanceServiceError):
    message = "Simulation introuvable."


class SoutenanceSessionCompletedError(SoutenanceServiceError):
    message = "Cette simulation est deja terminee."


class SoutenanceCreationError(SoutenanceServiceError):
    message = "Impossible de creer cette simulation."


class SoutenanceConfigurationError(SoutenanceServiceError):
    message = "Le service d'intelligence artificielle est temporairement indisponible."


class SoutenanceEvaluationError(SoutenanceServiceError):
    message = "Impossible d'evaluer votre reponse."


class WrongCurrentQuestionError(SoutenanceServiceError):
    message = "Cette question n'est pas la question actuelle."


class DuplicateSoutenanceAnswerError(SoutenanceServiceError):
    message = "Une reponse a deja ete enregistree pour cette question."


class SoutenanceResultsUnavailableError(SoutenanceServiceError):
    message = "Impossible de charger les resultats."


class SoutenanceCompletionError(SoutenanceServiceError):
    message = "Toutes les questions doivent etre completees."


class SoutenanceSessionService:
    def __init__(
        self,
        *,
        repository: SoutenanceRepository,
        soutenance_coach_agent: SoutenanceCoachAgent,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._soutenance_coach_agent = soutenance_coach_agent
        self._settings = settings
        self._rubric_tool = SoutenanceRubricTool()

    def create_session(
        self,
        *,
        current_user: User,
        request: CreateSoutenanceSessionRequest,
    ) -> SoutenanceSessionRead:
        if request.question_count > self._settings.soutenance_max_questions:
            raise SoutenanceCreationError

        project_tool, learner_tool, rubric_tool = self._tools_for_user(current_user)
        try:
            draft = self._soutenance_coach_agent.generate_questions(
                request=request,
                project_context_tool=project_tool,
                learner_profile_tool=learner_tool,
                rubric_tool=rubric_tool,
            )
            draft = self._validate_session_draft(request=request, draft=draft)
            session = self._persist_session(
                user=current_user,
                request=request,
                draft=draft,
            )
            self._repository.commit()
        except SoutenanceCoachConfigurationError as exc:
            self._repository.rollback()
            raise SoutenanceConfigurationError from exc
        except (SoutenanceCoachOutputError, SoutenanceServiceError) as exc:
            self._repository.rollback()
            raise SoutenanceCreationError from exc
        except Exception as exc:
            self._repository.rollback()
            raise SoutenanceCreationError from exc

        loaded = self._repository.get_for_user(
            session_id=session.id,
            user_id=current_user.id,
        )
        if loaded is None:
            raise SoutenanceSessionNotFoundError
        return self._to_session_read(loaded)

    def list_sessions(
        self,
        *,
        current_user: User,
        page: int,
        page_size: int,
        status: str | None,
    ) -> SoutenanceSessionListResponse:
        sessions, total = self._repository.list_for_user(
            user_id=current_user.id,
            limit=page_size,
            offset=(page - 1) * page_size,
            status=status,
        )
        return SoutenanceSessionListResponse(
            items=[self._to_list_item(session) for session in sessions],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )

    def get_session(
        self,
        *,
        current_user: User,
        session_id: int,
    ) -> SoutenanceSessionRead:
        session = self._get_session(current_user=current_user, session_id=session_id)
        return self._to_session_read(session)

    def get_current_question(
        self,
        *,
        current_user: User,
        session_id: int,
    ) -> SoutenanceCurrentQuestionResponse:
        session = self._get_session(current_user=current_user, session_id=session_id)
        return SoutenanceCurrentQuestionResponse(
            session_id=session.id,
            status=session.status,
            mode=session.mode,
            question_index=session.current_question_index,
            total_questions=session.question_count,
            progress_percentage=self._progress(session),
            question=self._public_question(self._current_question(session)),
        )

    def submit_answer(
        self,
        *,
        current_user: User,
        session_id: int,
        request: SubmitSoutenanceAnswerRequest,
    ) -> SubmitSoutenanceAnswerResponse:
        session = self._get_session(current_user=current_user, session_id=session_id)
        if session.status == "completed":
            raise SoutenanceSessionCompletedError

        question = self._current_question(session)
        if question is None or question.id != request.question_id:
            raise WrongCurrentQuestionError
        if question.answer is not None or question.answer_status == "answered":
            raise DuplicateSoutenanceAnswerError

        project_tool, learner_tool, rubric_tool = self._tools_for_user(current_user)
        try:
            draft = self._soutenance_coach_agent.evaluate_answer(
                question=self._public_question(question),
                expected_concepts=self._load_list(question.expected_concepts),
                evaluation_focus=question.evaluation_focus,
                answer_text=request.answer,
                project_context_tool=project_tool,
                learner_profile_tool=learner_tool,
                rubric_tool=rubric_tool,
            )
            draft = self._validate_evaluation_draft(
                question=question,
                draft=draft,
                rubric_tool=rubric_tool,
            )
            answer = self._persist_answer(
                question=question,
                answer_text=request.answer,
                draft=draft,
                rubric_tool=rubric_tool,
            )
            question.answer_status = "answered"
            session.current_question_index += 1
            if session.current_question_index >= session.question_count:
                self._complete_session(session)
            self._repository.commit()
        except (SoutenanceCoachConfigurationError, SoutenanceCoachOutputError) as exc:
            self._repository.rollback()
            raise SoutenanceEvaluationError from exc
        except Exception as exc:
            self._repository.rollback()
            if isinstance(exc, SoutenanceServiceError):
                raise
            raise SoutenanceEvaluationError from exc

        loaded = self._repository.get_for_user(
            session_id=session.id,
            user_id=current_user.id,
        )
        if loaded is None:
            raise SoutenanceSessionNotFoundError
        next_question = self._current_question(loaded)
        return SubmitSoutenanceAnswerResponse(
            session_id=loaded.id,
            question_id=question.id,
            mode=loaded.mode,
            status=loaded.status,
            feedback=self._answer_feedback(answer)
            if loaded.mode == "training"
            else None,
            next_question=self._public_question(next_question),
            progress_percentage=self._progress(loaded),
            message=(
                "Reponse enregistree. Feedback disponible en fin de simulation."
                if loaded.mode == "jury"
                else "Reponse evaluee."
            ),
        )

    def complete_session(
        self,
        *,
        current_user: User,
        session_id: int,
    ) -> SoutenanceResultsResponse:
        session = self._get_session(current_user=current_user, session_id=session_id)
        if session.status != "completed":
            if self._answered_count(session) != session.question_count:
                raise SoutenanceCompletionError
            self._complete_session(session)
            self._repository.commit()

        return self.get_results(current_user=current_user, session_id=session_id)

    def get_results(
        self,
        *,
        current_user: User,
        session_id: int,
    ) -> SoutenanceResultsResponse:
        session = self._get_session(current_user=current_user, session_id=session_id)
        if session.status != "completed" or session.final_score is None:
            raise SoutenanceResultsUnavailableError
        return self._to_results(session)

    def delete_session(self, *, current_user: User, session_id: int) -> None:
        session = self._get_session(current_user=current_user, session_id=session_id)
        self._repository.delete(session)
        self._repository.commit()

    def _tools_for_user(
        self,
        user: User,
    ) -> tuple[ProjectContextTool, LearnerProfileTool, SoutenanceRubricTool]:
        return (
            ProjectContextTool(snapshot=self._project_context_snapshot()),
            LearnerProfileTool(snapshot=self._learner_profile_snapshot(user)),
            SoutenanceRubricTool(),
        )

    def _project_context_snapshot(self) -> ProjectContextSnapshot:
        self._read_allowed_docs()
        return ProjectContextSnapshot(
            project_objective=(
                "FormaMind AI est une plateforme educative multi-agents pour "
                "transformer des supports PDF en assistant, evaluations, plans "
                "d'apprentissage et simulations de soutenance."
            ),
            backend_stack=[
                "FastAPI",
                "SQLAlchemy",
                "Alembic",
                "SQLite",
                "JWT",
                "CrewAI",
                "Gemini",
                "LlamaIndex",
                "ChromaDB",
            ],
            frontend_stack=[
                "React",
                "TypeScript",
                "Vite",
                "Tailwind CSS",
                "TanStack Query",
                "React Hook Form",
                "Zod",
            ],
            database="SQLite en developpement avec migrations Alembic.",
            implemented_features=[
                "Authentification JWT",
                "Documents PDF",
                "RAG avec embeddings et ChromaDB",
                "Knowledge Agent",
                "Assessment Agent",
                "Learning Coach Agent",
                "Plans d'apprentissage persistants",
            ],
            endpoints=[
                "/api/v1/auth/*",
                "/api/v1/documents",
                "/api/v1/assistant/ask",
                "/api/v1/assessments",
                "/api/v1/attempts",
                "/api/v1/learning-plans",
                "/api/v1/soutenance-sessions",
            ],
            security_boundaries=[
                "Authentification obligatoire",
                "Ownership par user_id",
                "Routes fines sans logique metier",
                "Services responsables des transactions",
                "Agents sans acces direct DB ou HTTP",
                "Tools limites a des snapshots fiables",
            ],
            known_limits=[
                "Pas de micro, webcam, speech-to-text ou temps reel",
                "Pas de Redis, Celery ou WebSockets",
                "SQLite pour le developpement",
            ],
        )

    def _learner_profile_snapshot(self, user: User) -> LearnerProfileSnapshot:
        attempts = self._repository.learner_attempts(user_id=user.id)
        learning_plans = self._repository.learner_learning_plans(user_id=user.id)
        previous_sessions = self._repository.completed_sessions(user_id=user.id)
        percentages = [
            float(attempt.percentage)
            for attempt in attempts
            if attempt.percentage is not None
        ]
        global_score = (
            round(sum(percentages) / len(percentages), 2) if percentages else 0
        )
        return LearnerProfileSnapshot(
            learner_name=user.full_name,
            global_score=global_score,
            current_level=self._readiness_level(global_score),
            recent_assessment_scores=percentages,
            weak_topics=self._unique_flatten(
                attempt.weak_topics or [] for attempt in attempts
            ),
            strong_topics=self._unique_flatten(
                attempt.strong_topics or [] for attempt in attempts
            ),
            missing_concepts=self._missing_concepts_from_attempts(attempts),
            learning_plan_progress=[
                plan.progress_percentage for plan in learning_plans
            ],
            previous_soutenance_scores=[
                float(session.final_score)
                for session in previous_sessions
                if session.final_score is not None
            ],
            previous_soutenance_weaknesses=self._unique_flatten(
                self._load_list(session.weaknesses) for session in previous_sessions
            ),
        )

    def _read_allowed_docs(self) -> None:
        root = Path(__file__).resolve().parents[3]
        allowed_paths = [
            root / "README.md",
            root / "DESIGN_REFERENCE.md",
            root / "docs" / "architecture.md",
            root / "docs" / "feature-07-learning-coach-visual-spec.md",
        ]
        for path in allowed_paths:
            if path.exists():
                path.read_text(encoding="utf-8", errors="ignore")

    def _validate_session_draft(
        self,
        *,
        request: CreateSoutenanceSessionRequest,
        draft: SoutenanceSessionDraft,
    ) -> SoutenanceSessionDraft:
        if len(draft.questions) != request.question_count:
            raise SoutenanceCreationError

        local_ids: set[str] = set()
        texts: set[str] = set()
        allowed_categories = set(request.question_categories)
        normalized_questions = []
        for index, question in enumerate(draft.questions):
            if question.local_id in local_ids:
                raise SoutenanceCreationError
            if question.text.strip().lower() in texts:
                raise SoutenanceCreationError
            if question.category not in allowed_categories:
                raise SoutenanceCreationError
            local_ids.add(question.local_id)
            texts.add(question.text.strip().lower())
            normalized_questions.append(
                question.model_copy(update={"order_index": index})
            )

        return draft.model_copy(update={"questions": normalized_questions})

    def _persist_session(
        self,
        *,
        user: User,
        request: CreateSoutenanceSessionRequest,
        draft: SoutenanceSessionDraft,
    ) -> SoutenanceSession:
        session = SoutenanceSession(
            user_id=user.id,
            title=draft.title,
            introduction=draft.introduction,
            mode=request.mode,
            difficulty=request.difficulty,
            status="in_progress",
            question_count=request.question_count,
            current_question_index=0,
        )
        self._repository.add(session)
        for question_draft in draft.questions:
            session.questions.append(
                SoutenanceQuestion(
                    local_id=question_draft.local_id,
                    text=question_draft.text,
                    category=question_draft.category,
                    difficulty=question_draft.difficulty,
                    expected_concepts=self._dump_list(question_draft.expected_concepts),
                    evaluation_focus=question_draft.evaluation_focus,
                    follow_up_hint=question_draft.follow_up_hint,
                    order_index=question_draft.order_index,
                    answer_status="waiting",
                )
            )
        self._repository.flush()
        return session

    def _validate_evaluation_draft(
        self,
        *,
        question: SoutenanceQuestion,
        draft: SoutenanceAnswerEvaluationDraft,
        rubric_tool: SoutenanceRubricTool,
    ) -> SoutenanceAnswerEvaluationDraft:
        if draft.question_id != question.id:
            raise SoutenanceEvaluationError
        criteria = [score.criterion for score in draft.rubric_scores]
        if criteria != RUBRIC_CRITERIA:
            raise SoutenanceEvaluationError
        rubric_tool.calculate_total(
            {score.criterion: score.score for score in draft.rubric_scores}
        )
        return draft

    def _persist_answer(
        self,
        *,
        question: SoutenanceQuestion,
        answer_text: str,
        draft: SoutenanceAnswerEvaluationDraft,
        rubric_tool: SoutenanceRubricTool,
    ) -> SoutenanceAnswer:
        weights = rubric_tool.weights()
        total = rubric_tool.calculate_total(
            {score.criterion: score.score for score in draft.rubric_scores}
        )
        answer = SoutenanceAnswer(
            question=question,
            text=answer_text,
            total_score=total,
            feedback=draft.feedback,
            strengths=self._dump_list(draft.strengths),
            missing_concepts=self._dump_list(draft.missing_concepts),
            improved_answer=draft.improved_answer,
            recommendation=draft.recommendation,
        )
        for score in draft.rubric_scores:
            answer.rubric_scores.append(
                SoutenanceRubricScore(
                    criterion=score.criterion,
                    score=score.score,
                    weight=weights[score.criterion],
                    comment=score.comment,
                )
            )
        question.answer = answer
        self._repository.add_answer(answer)
        return answer

    def _complete_session(self, session: SoutenanceSession) -> None:
        answers = [
            question.answer
            for question in session.questions
            if question.answer is not None
        ]
        if len(answers) != session.question_count:
            raise SoutenanceCompletionError
        final_score = round(
            sum(float(answer.total_score) for answer in answers) / len(answers),
            2,
        )
        session.status = "completed"
        session.final_score = final_score
        session.readiness_level = self._readiness_level(final_score)
        session.strengths = self._dump_list(
            self._unique_flatten(
                self._load_list(answer.strengths) for answer in answers
            )
        )
        session.missing_concepts = self._dump_list(
            self._unique_flatten(
                self._load_list(answer.missing_concepts) for answer in answers
            )
        )
        session.weaknesses = self._dump_list(
            self._weak_categories(session, threshold=60)
        )
        session.recommendations = self._dump_list(
            self._unique_flatten([answer.recommendation] for answer in answers)[:6]
        )
        session.completed_at = utc_now()

    def _get_session(self, *, current_user: User, session_id: int) -> SoutenanceSession:
        session = self._repository.get_for_user(
            session_id=session_id,
            user_id=current_user.id,
        )
        if session is None:
            raise SoutenanceSessionNotFoundError
        return session

    def _to_session_read(self, session: SoutenanceSession) -> SoutenanceSessionRead:
        return SoutenanceSessionRead(
            id=session.id,
            title=session.title,
            introduction=session.introduction,
            mode=session.mode,
            difficulty=session.difficulty,
            status=session.status,
            question_count=session.question_count,
            answered_count=self._answered_count(session),
            current_question_index=session.current_question_index,
            progress_percentage=self._progress(session),
            final_score=self._optional_float(session.final_score),
            readiness_level=session.readiness_level,
            created_at=session.created_at.isoformat(),
            completed_at=self._optional_iso(session.completed_at),
            questions=[
                self._public_question(question) for question in session.questions
            ],
        )

    def _to_list_item(self, session: SoutenanceSession) -> SoutenanceSessionListItem:
        return SoutenanceSessionListItem(
            id=session.id,
            title=session.title,
            mode=session.mode,
            difficulty=session.difficulty,
            status=session.status,
            question_count=session.question_count,
            answered_count=self._answered_count(session),
            progress_percentage=self._progress(session),
            final_score=self._optional_float(session.final_score),
            readiness_level=session.readiness_level,
            created_at=session.created_at.isoformat(),
            completed_at=self._optional_iso(session.completed_at),
        )

    def _to_results(self, session: SoutenanceSession) -> SoutenanceResultsResponse:
        if session.completed_at is None or session.final_score is None:
            raise SoutenanceResultsUnavailableError
        return SoutenanceResultsResponse(
            id=session.id,
            title=session.title,
            mode=session.mode,
            difficulty=session.difficulty,
            final_score=float(session.final_score),
            readiness_level=session.readiness_level or "A renforcer",
            strengths=self._load_list(session.strengths),
            weaknesses=self._load_list(session.weaknesses),
            missing_concepts=self._load_list(session.missing_concepts),
            recommendations=self._load_list(session.recommendations),
            category_scores=self._category_scores(session),
            questions=[
                SoutenanceQuestionResult(
                    question=self._public_question(question),
                    answer_text=question.answer.text,
                    feedback=self._answer_feedback(question.answer),
                )
                for question in session.questions
                if question.answer is not None
            ],
            completed_at=session.completed_at.isoformat(),
        )

    def _public_question(
        self,
        question: SoutenanceQuestion | None,
    ) -> PublicSoutenanceQuestion | None:
        if question is None:
            return None
        return PublicSoutenanceQuestion(
            id=question.id,
            text=question.text,
            category=question.category,
            category_label=CATEGORY_LABELS[question.category],
            difficulty=question.difficulty,
            order_index=question.order_index,
            answer_status=question.answer_status,
        )

    def _answer_feedback(self, answer: SoutenanceAnswer) -> SoutenanceAnswerFeedback:
        rubric_labels = self._rubric_tool.labels()
        return SoutenanceAnswerFeedback(
            total_score=float(answer.total_score),
            feedback=answer.feedback,
            strengths=self._load_list(answer.strengths),
            missing_concepts=self._load_list(answer.missing_concepts),
            improved_answer=answer.improved_answer,
            recommendation=answer.recommendation,
            rubric_scores=[
                SoutenanceRubricCriterionRead(
                    criterion=score.criterion,
                    label=rubric_labels[score.criterion],
                    weight=score.weight,
                    score=float(score.score),
                    comment=score.comment,
                )
                for score in answer.rubric_scores
            ],
        )

    def _current_question(
        self,
        session: SoutenanceSession,
    ) -> SoutenanceQuestion | None:
        if session.status == "completed":
            return None
        return next(
            (
                question
                for question in session.questions
                if question.order_index == session.current_question_index
            ),
            None,
        )

    def _answered_count(self, session: SoutenanceSession) -> int:
        return sum(1 for question in session.questions if question.answer is not None)

    def _progress(self, session: SoutenanceSession) -> int:
        if session.question_count == 0:
            return 0
        return round((self._answered_count(session) / session.question_count) * 100)

    def _category_scores(
        self,
        session: SoutenanceSession,
    ) -> list[SoutenanceCategoryScore]:
        by_category: dict[str, list[float]] = {}
        for question in session.questions:
            if question.answer is None:
                continue
            by_category.setdefault(question.category, []).append(
                float(question.answer.total_score)
            )
        return [
            SoutenanceCategoryScore(
                category=category,
                category_label=CATEGORY_LABELS[category],
                score=round(sum(scores) / len(scores), 2),
                answered_count=len(scores),
            )
            for category, scores in by_category.items()
        ]

    def _weak_categories(
        self,
        session: SoutenanceSession,
        *,
        threshold: int,
    ) -> list[str]:
        return [
            score.category_label
            for score in self._category_scores(session)
            if score.score < threshold
        ]

    def _missing_concepts_from_attempts(
        self,
        attempts: list[AssessmentAttempt],
    ) -> list[str]:
        values: list[str] = []
        for attempt in attempts:
            for answer in attempt.answers:
                values.extend(answer.missing_concepts or [])
        return self._unique_flatten([values])

    def _readiness_level(self, score: float) -> str:
        if score >= 85:
            return "Pret pour la soutenance"
        if score >= 70:
            return "Bonne preparation"
        if score >= 55:
            return "Preparation partielle"
        return "A renforcer"

    def _dump_list(self, values: list[str]) -> str:
        return json.dumps(values, ensure_ascii=False)

    def _load_list(self, value: str | None) -> list[str]:
        if not value:
            return []
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return []
        if not isinstance(loaded, list):
            return []
        return [str(item) for item in loaded if str(item).strip()]

    def _unique_flatten(self, groups: Any) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for group in groups:
            for value in group:
                cleaned = " ".join(str(value).split())
                if not cleaned or cleaned.lower() in seen:
                    continue
                seen.add(cleaned.lower())
                result.append(cleaned)
        return result[:10]

    def _optional_float(self, value: Any) -> float | None:
        return float(value) if value is not None else None

    def _optional_iso(self, value: Any) -> str | None:
        return value.isoformat() if value is not None else None
