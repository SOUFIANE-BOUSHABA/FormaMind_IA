from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.assessment import Assessment, AssessmentAttempt, Question
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.schemas.dashboard import (
    ActivityEntry,
    AgentActivity,
    DashboardMetric,
    DashboardSummary,
    FocusArea,
    Recommendation,
    SkillMetric,
)


class DashboardService:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        db: Session | None = None,
    ) -> None:
        self.document_repository = document_repository
        self.db = db

    def get_summary(self, user: User) -> DashboardSummary:
        learner_name = user.full_name.strip() or "Rabie"
        document_count = (
            self.document_repository.count_owned(user_id=user.id)
            if self.document_repository is not None
            else 0
        )
        attempts = self._evaluated_attempts(user.id)
        completed_count = len(attempts)
        percentages = [
            float(attempt.percentage)
            for attempt in attempts
            if attempt.percentage is not None
        ]
        global_score = round(sum(percentages) / len(percentages)) if percentages else 0
        learning_minutes = self._learning_minutes(attempts)

        return DashboardSummary(
            learner_name=learner_name,
            learner_title="Apprenant en Intelligence Artificielle",
            greeting=f"Bonjour {learner_name},",
            subtitle=(
                "L'intelligence artificielle evolue rapidement. Voici vos "
                "prochaines etapes pour rester a la pointe."
            ),
            metrics=[
                DashboardMetric(
                    label="Score global",
                    value=str(global_score),
                    description="/100",
                    icon="verified",
                    tone="primary",
                    trend="Base sur vos evaluations terminees"
                    if completed_count
                    else None,
                ),
                DashboardMetric(
                    label="Niveau actuel",
                    value=self._level_from_score(global_score),
                    description="Calcule depuis vos scores reels",
                    icon="award",
                    tone="secondary",
                ),
                DashboardMetric(
                    label="Documents",
                    value=str(document_count),
                    description="PDF import\u00e9s",
                    icon="book",
                    tone="accent",
                ),
                DashboardMetric(
                    label="Evaluations",
                    value=str(completed_count),
                    description="Tentatives evaluees",
                    icon="checklist",
                    tone="error",
                ),
                DashboardMetric(
                    label="Apprentissage",
                    value=f"{learning_minutes}m",
                    description="Temps estime sur les quiz",
                    icon="timer",
                    tone="primary",
                ),
                DashboardMetric(
                    label="Objectif hebdo",
                    value="75%",
                    description="Progression active",
                    icon="target",
                    tone="primary",
                    progress=75,
                ),
            ],
            skills=self._skills_from_attempts(attempts),
            agents=[
                AgentActivity(
                    name="Knowledge Agent",
                    status="online",
                    description="Documents analyses et disponibles pour le RAG.",
                    tone="accent",
                ),
                AgentActivity(
                    name="Learning Coach",
                    status="waiting",
                    description="Plan d'apprentissage prevu dans une feature dediee.",
                    tone="primary",
                ),
                AgentActivity(
                    name="Assessment Agent",
                    status="active" if completed_count else "waiting",
                    description=f"{completed_count} evaluation(s) corrigee(s).",
                    tone="secondary",
                ),
            ],
            recommendation=Recommendation(
                eyebrow="Revision ciblee",
                title="Reprendre les notions faibles",
                duration="30 min",
                badge="Remediation",
                description=(
                    "Utilisez vos resultats d'evaluation pour retravailler les "
                    "questions incorrectes et les sources associees."
                ),
                action_label="Voir mes evaluations",
            )
            if completed_count
            else None,
            focus_areas=self._focus_areas_from_attempts(attempts),
            recent_activity=self._recent_activity(attempts),
        )

    def _evaluated_attempts(self, user_id: int) -> list[AssessmentAttempt]:
        if self.db is None:
            return []

        statement = (
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.user_id == user_id,
                AssessmentAttempt.status == "evaluated",
            )
            .order_by(AssessmentAttempt.evaluated_at.desc())
            .options(
                joinedload(AssessmentAttempt.assessment).options(
                    selectinload(Assessment.questions).joinedload(
                        Question.source_document
                    )
                ),
                selectinload(AssessmentAttempt.answers),
            )
        )
        return list(self.db.scalars(statement).unique().all())

    def _learning_minutes(self, attempts: list[AssessmentAttempt]) -> int:
        total_seconds = 0
        for attempt in attempts:
            end = attempt.submitted_at or attempt.evaluated_at
            if end is None:
                continue
            total_seconds += max(int((end - attempt.started_at).total_seconds()), 60)
        return max(round(total_seconds / 60), 0)

    def _level_from_score(self, score: int) -> str:
        if score >= 90:
            return "Expert"
        if score >= 75:
            return "Avance"
        if score >= 55:
            return "Intermediaire"
        if score >= 35:
            return "Debutant"
        return "A renforcer"

    def _skills_from_attempts(
        self,
        attempts: list[AssessmentAttempt],
    ) -> list[SkillMetric]:
        topic_scores: dict[str, list[float]] = {}
        for attempt in attempts:
            for question in attempt.assessment.questions:
                answer = next(
                    (
                        item
                        for item in attempt.answers
                        if item.question_id == question.id
                        and item.points_awarded is not None
                    ),
                    None,
                )
                if answer is None or question.source_document is None:
                    continue
                ratio = float(answer.points_awarded) / max(float(question.points), 1.0)
                topic_scores.setdefault(question.source_document.title, []).append(
                    ratio * 100
                )

        return [
            SkillMetric(
                label=topic[:12],
                value=round(sum(values) / len(values)),
                highlighted=sum(values) / len(values) >= 80,
            )
            for topic, values in list(topic_scores.items())[:8]
            if values
        ]

    def _focus_areas_from_attempts(
        self,
        attempts: list[AssessmentAttempt],
    ) -> list[FocusArea]:
        labels: list[str] = []
        for attempt in attempts:
            labels.extend(attempt.weak_topics or [])

        focus: list[FocusArea] = []
        for label in dict.fromkeys(labels):
            focus.append(
                FocusArea(
                    label=label,
                    severity="critical" if not focus else "important",
                    progress=35 if not focus else 45,
                )
            )
        return focus[:3]

    def _recent_activity(
        self,
        attempts: list[AssessmentAttempt],
    ) -> list[ActivityEntry]:
        activities: list[ActivityEntry] = []
        for attempt in attempts[:5]:
            if attempt.percentage is None:
                continue
            activities.append(
                ActivityEntry(
                    title=f"Evaluation terminee: {attempt.assessment.title}",
                    description=f"Score : {float(attempt.percentage):.0f}/100.",
                    timestamp=self._relative_time(attempt.evaluated_at),
                    tone="primary",
                )
            )
        return activities

    def _relative_time(self, value: datetime | None) -> str:
        if value is None:
            return "Recemment"

        delta = datetime.now(value.tzinfo) - value
        if delta.days >= 7:
            return "Cette semaine"
        if delta.days >= 1:
            return "Hier"
        hours = max(delta.seconds // 3600, 1)
        return f"{hours}h"
