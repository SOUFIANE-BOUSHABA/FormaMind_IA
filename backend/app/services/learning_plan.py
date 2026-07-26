from __future__ import annotations

from datetime import date
from math import ceil
from typing import Any

from app.agents.learning_coach_agent import (
    LearningCoachAgent,
    LearningCoachConfigurationError,
    LearningCoachOutputError,
)
from app.models.assessment import AssessmentAttempt, Question, StudentAnswer
from app.models.learning_plan import (
    LearningActivity,
    LearningActivitySource,
    LearningModule,
    LearningPlan,
)
from app.models.user import User, utc_now
from app.repositories.learning_plan import LearningPlanRepository
from app.schemas.learning_plan import (
    AssessmentEvidenceItem,
    AssessmentLearningSnapshot,
    GenerateLearningPlanRequest,
    LearningActivityRead,
    LearningModuleRead,
    LearningPlanListItem,
    LearningPlanListResponse,
    LearningPlanRead,
    LearningPlanSource,
    UpdateLearningActivityStatusRequest,
)
from app.schemas.rag import RetrievedChunk
from app.tools.assessment_results_tool import AssessmentResultsTool
from app.tools.learning_content_tool import LearningContentTool
from app.tools.study_schedule_tool import ScheduleActivityInput, StudyScheduleTool


class LearningPlanServiceError(Exception):
    message = "La gestion du plan d'apprentissage a echoue."


class LearningPlanAttemptNotFoundError(LearningPlanServiceError):
    message = "Cette tentative evaluee est introuvable."


class LearningPlanAlreadyExistsError(LearningPlanServiceError):
    message = "Un plan actif existe deja pour cette tentative."


class LearningPlanGenerationConfigurationError(LearningPlanServiceError):
    message = "Le Learning Coach Agent n'est pas configure."


class LearningPlanGenerationInvalidOutputError(LearningPlanServiceError):
    message = "Le Learning Coach Agent n'a pas produit un plan valide."


class LearningPlanNotFoundError(LearningPlanServiceError):
    message = "Impossible de charger ce plan d'apprentissage."


class LearningActivityNotFoundError(LearningPlanServiceError):
    message = "Impossible de charger cette activite."


class LearningActivityTransitionError(LearningPlanServiceError):
    message = "Cette transition de statut n'est pas autorisee."


class LearningPlanService:
    def __init__(
        self,
        *,
        repository: LearningPlanRepository,
        learning_coach_agent: LearningCoachAgent,
        retriever_tool: Any,
    ) -> None:
        self._repository = repository
        self._learning_coach_agent = learning_coach_agent
        self._retriever_tool = retriever_tool

    def generate_plan(
        self,
        *,
        current_user: User,
        request: GenerateLearningPlanRequest,
    ) -> LearningPlanRead:
        attempt = self._repository.get_attempt_for_generation(
            attempt_id=request.attempt_id,
            user_id=current_user.id,
        )
        if attempt is None or attempt.status != "evaluated":
            raise LearningPlanAttemptNotFoundError

        existing_plan = self._repository.get_active_for_attempt(
            attempt_id=attempt.id,
            user_id=current_user.id,
        )
        if existing_plan is not None:
            loaded_plan = self._repository.get_for_user(
                plan_id=existing_plan.id,
                user_id=current_user.id,
            )
            if loaded_plan is None:
                raise LearningPlanNotFoundError
            return self._to_read(loaded_plan)

        snapshot = self._snapshot_for_attempt(attempt)
        if not snapshot.evidence:
            raise LearningPlanGenerationInvalidOutputError

        content_tool = LearningContentTool(
            user_id=current_user.id,
            document_ids=snapshot.document_ids,
            retriever_tool=self._retriever_tool,
        )
        assessment_tool = AssessmentResultsTool(snapshot=snapshot)
        schedule_tool = StudyScheduleTool()

        try:
            draft = self._learning_coach_agent.generate_plan(
                request=request,
                assessment_results_tool=assessment_tool,
                learning_content_tool=content_tool,
                study_schedule_tool=schedule_tool,
            )
        except LearningCoachConfigurationError as exc:
            raise LearningPlanGenerationConfigurationError from exc
        except LearningCoachOutputError as exc:
            raise LearningPlanGenerationInvalidOutputError from exc

        try:
            plan = self._persist_plan(
                user=current_user,
                attempt=attempt,
                request=request,
                draft=draft,
                source_map=content_tool.source_map,
                schedule_tool=schedule_tool,
            )
            self._repository.commit()
        except Exception as exc:
            self._repository.rollback()
            if isinstance(exc, LearningPlanServiceError):
                raise
            raise LearningPlanGenerationInvalidOutputError from exc

        loaded = self._repository.get_for_user(plan_id=plan.id, user_id=current_user.id)
        if loaded is None:
            raise LearningPlanNotFoundError
        return self._to_read(loaded)

    def list_plans(
        self,
        *,
        current_user: User,
        page: int,
        page_size: int,
        status: str | None,
    ) -> LearningPlanListResponse:
        offset = (page - 1) * page_size
        plans, total = self._repository.list_for_user(
            user_id=current_user.id,
            limit=page_size,
            offset=offset,
            status=status,
        )
        return LearningPlanListResponse(
            items=[self._to_list_item(plan) for plan in plans],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )

    def get_plan(self, *, current_user: User, plan_id: int) -> LearningPlanRead:
        plan = self._repository.get_for_user(plan_id=plan_id, user_id=current_user.id)
        if plan is None:
            raise LearningPlanNotFoundError
        return self._to_read(plan)

    def delete_plan(self, *, current_user: User, plan_id: int) -> None:
        plan = self._repository.get_for_user(plan_id=plan_id, user_id=current_user.id)
        if plan is None:
            raise LearningPlanNotFoundError
        self._repository.delete(plan)
        self._repository.commit()

    def update_activity_status(
        self,
        *,
        current_user: User,
        plan_id: int,
        activity_id: int,
        request: UpdateLearningActivityStatusRequest,
    ) -> LearningPlanRead:
        plan = self._repository.get_for_user(plan_id=plan_id, user_id=current_user.id)
        if plan is None:
            raise LearningPlanNotFoundError

        activity = self._activity_for_plan(plan, activity_id)
        if activity is None:
            raise LearningActivityNotFoundError

        self._apply_transition(activity=activity, next_status=request.status)
        self._recalculate_progress(plan)
        self._repository.commit()

        loaded = self._repository.get_for_user(plan_id=plan.id, user_id=current_user.id)
        if loaded is None:
            raise LearningPlanNotFoundError
        return self._to_read(loaded)

    def _persist_plan(
        self,
        *,
        user: User,
        attempt: AssessmentAttempt,
        request: GenerateLearningPlanRequest,
        draft: Any,
        source_map: dict[str, RetrievedChunk],
        schedule_tool: StudyScheduleTool,
    ) -> LearningPlan:
        activity_inputs: list[ScheduleActivityInput] = []
        for module_index, module in enumerate(draft.modules):
            for activity_index, activity in enumerate(module.activities):
                activity_inputs.append(
                    ScheduleActivityInput(
                        temp_id=f"{module_index}:{activity_index}",
                        duration_minutes=activity.duration_minutes,
                    )
                )

        schedule = schedule_tool.build_schedule(
            activities=activity_inputs,
            daily_minutes=request.daily_minutes,
            start_date=request.start_date,
            intensity=request.intensity,
        )
        activity_dates: dict[str, str] = schedule["activities"]  # type: ignore[assignment]

        plan = LearningPlan(
            user_id=user.id,
            attempt_id=attempt.id,
            title=draft.title[:180],
            status="active",
            intensity=request.intensity,
            daily_minutes=request.daily_minutes,
            start_date=request.start_date,
            target_end_date=date.fromisoformat(str(schedule["target_end_date"])),
            progress_percentage=0,
            generated_summary=draft.generated_summary,
        )
        self._repository.add(plan)

        for module_index, module_draft in enumerate(draft.modules):
            module = LearningModule(
                plan=plan,
                title=module_draft.title,
                objective=module_draft.objective,
                topic=module_draft.topic,
                priority=module_draft.priority,
                order_index=module_index,
                estimated_minutes=sum(
                    activity.duration_minutes for activity in module_draft.activities
                ),
            )
            plan.modules.append(module)

            for activity_index, activity_draft in enumerate(module_draft.activities):
                activity_key = f"{module_index}:{activity_index}"
                activity = LearningActivity(
                    module=module,
                    title=activity_draft.title,
                    instructions=activity_draft.instructions,
                    type=activity_draft.type,
                    status="pending",
                    order_index=activity_index,
                    scheduled_date=date.fromisoformat(activity_dates[activity_key]),
                    duration_minutes=activity_draft.duration_minutes,
                )
                module.activities.append(activity)

                for source_ref in activity_draft.source_refs:
                    chunk = source_map.get(source_ref)
                    if chunk is None:
                        raise LearningPlanGenerationInvalidOutputError
                    activity.sources.append(
                        LearningActivitySource(
                            activity=activity,
                            document_id=chunk.document_id,
                            page_number=chunk.page_number,
                            excerpt=self._truncate(chunk.text, 520),
                        )
                    )

        self._repository.flush()
        return plan

    def _snapshot_for_attempt(
        self,
        attempt: AssessmentAttempt,
    ) -> AssessmentLearningSnapshot:
        document_ids = [
            item.document_id
            for item in attempt.assessment.documents
            if item.document is not None
        ]
        evidence: list[AssessmentEvidenceItem] = []
        for question in attempt.assessment.questions:
            answer = self._answer_for_question(attempt, question.id)
            if answer is None or answer.evaluation_status is None:
                continue
            evidence.append(
                AssessmentEvidenceItem(
                    question_id=question.id,
                    question_text=question.text,
                    expected_answer=question.correct_answer,
                    learner_answer=self._learner_answer(question, answer),
                    evaluation_status=answer.evaluation_status,
                    points=float(question.points),
                    points_awarded=float(answer.points_awarded or 0),
                    feedback=answer.feedback,
                    missing_concepts=answer.missing_concepts or [],
                    source_document_id=question.source_document_id,
                    source_document_title=question.source_document.title,
                    source_page_number=question.source_page_number,
                    source_excerpt=question.source_excerpt,
                )
            )

        return AssessmentLearningSnapshot(
            attempt_id=attempt.id,
            assessment_title=attempt.assessment.title,
            score_percent=float(attempt.percentage or 0),
            level=attempt.level or "A renforcer",
            strong_topics=attempt.strong_topics or [],
            weak_topics=attempt.weak_topics or [],
            document_ids=sorted(set(document_ids)),
            evidence=evidence,
        )

    def _learner_answer(self, question: Question, answer: StudentAnswer) -> str | None:
        if answer.text_answer:
            return answer.text_answer
        if answer.selected_option is not None:
            return answer.selected_option.text
        return None

    def _answer_for_question(
        self,
        attempt: AssessmentAttempt,
        question_id: int,
    ) -> StudentAnswer | None:
        return next(
            (answer for answer in attempt.answers if answer.question_id == question_id),
            None,
        )

    def _activity_for_plan(
        self,
        plan: LearningPlan,
        activity_id: int,
    ) -> LearningActivity | None:
        for module in plan.modules:
            for activity in module.activities:
                if activity.id == activity_id:
                    return activity
        return None

    def _apply_transition(
        self,
        *,
        activity: LearningActivity,
        next_status: str,
    ) -> None:
        allowed = {
            "pending": {"in_progress"},
            "in_progress": {"completed", "pending"},
            "completed": {"in_progress"},
        }
        if next_status == activity.status:
            return
        if next_status not in allowed.get(activity.status, set()):
            raise LearningActivityTransitionError

        now = utc_now()
        activity.status = next_status
        if next_status == "in_progress" and activity.started_at is None:
            activity.started_at = now
            activity.completed_at = None
        elif next_status == "completed":
            if activity.started_at is None:
                activity.started_at = now
            activity.completed_at = now
        elif next_status == "pending":
            activity.completed_at = None

    def _recalculate_progress(self, plan: LearningPlan) -> None:
        activities = [
            activity for module in plan.modules for activity in module.activities
        ]
        if not activities:
            plan.progress_percentage = 0
            plan.status = "active"
            return

        completed_count = sum(
            1 for activity in activities if activity.status == "completed"
        )
        plan.progress_percentage = round((completed_count / len(activities)) * 100)
        plan.status = "completed" if plan.progress_percentage == 100 else "active"

    def _to_list_item(self, plan: LearningPlan) -> LearningPlanListItem:
        next_activity = self._next_activity(plan)
        return LearningPlanListItem(
            id=plan.id,
            attempt_id=plan.attempt_id,
            assessment_title=plan.attempt.assessment.title,
            title=plan.title,
            status=plan.status,
            intensity=plan.intensity,
            daily_minutes=plan.daily_minutes,
            start_date=plan.start_date.isoformat(),
            target_end_date=plan.target_end_date.isoformat(),
            progress_percentage=plan.progress_percentage,
            next_activity_title=next_activity.title if next_activity else None,
            next_activity_date=(
                next_activity.scheduled_date.isoformat() if next_activity else None
            ),
            created_at=plan.created_at.isoformat(),
        )

    def _to_read(self, plan: LearningPlan) -> LearningPlanRead:
        return LearningPlanRead(
            id=plan.id,
            attempt_id=plan.attempt_id,
            assessment_title=plan.attempt.assessment.title,
            title=plan.title,
            status=plan.status,
            intensity=plan.intensity,
            daily_minutes=plan.daily_minutes,
            start_date=plan.start_date.isoformat(),
            target_end_date=plan.target_end_date.isoformat(),
            progress_percentage=plan.progress_percentage,
            generated_summary=plan.generated_summary,
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat(),
            modules=[
                LearningModuleRead(
                    id=module.id,
                    title=module.title,
                    objective=module.objective,
                    topic=module.topic,
                    priority=module.priority,
                    order_index=module.order_index,
                    estimated_minutes=module.estimated_minutes,
                    activities=[
                        LearningActivityRead(
                            id=activity.id,
                            title=activity.title,
                            instructions=activity.instructions,
                            type=activity.type,
                            status=activity.status,
                            order_index=activity.order_index,
                            scheduled_date=activity.scheduled_date.isoformat(),
                            duration_minutes=activity.duration_minutes,
                            started_at=self._optional_iso(activity.started_at),
                            completed_at=self._optional_iso(activity.completed_at),
                            sources=[
                                LearningPlanSource(
                                    document_id=source.document_id,
                                    document_title=source.document.title,
                                    page_number=source.page_number,
                                    excerpt=source.excerpt,
                                )
                                for source in activity.sources
                            ],
                        )
                        for activity in module.activities
                    ],
                )
                for module in plan.modules
            ],
        )

    def _next_activity(self, plan: LearningPlan) -> LearningActivity | None:
        activities = [
            activity
            for module in plan.modules
            for activity in module.activities
            if activity.status != "completed"
        ]
        return min(
            activities,
            key=lambda activity: (
                activity.scheduled_date,
                activity.module.order_index,
                activity.order_index,
            ),
            default=None,
        )

    def _optional_iso(self, value: Any) -> str | None:
        return value.isoformat() if value is not None else None

    def _truncate(self, text: str, max_length: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= max_length:
            return normalized
        return f"{normalized[: max_length - 1].rstrip()}..."
