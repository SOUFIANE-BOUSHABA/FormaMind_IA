from __future__ import annotations

import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from app.schemas.learning_plan import AssessmentEvidenceItem, AssessmentLearningSnapshot


class AssessmentResultsToolInput(BaseModel):
    analysis_focus: str = Field(
        min_length=1,
        max_length=160,
        description="Focus d'analyse: lacunes, acquis, priorites ou progression.",
    )
    include_strong_topics: bool = Field(
        default=True,
        description="Inclure aussi les points acquis pour equilibrer le plan.",
    )


class AssessmentResultsTool(BaseTool):
    name: str = "AssessmentResultsTool"
    description: str = (
        "Analyse les resultats d'une tentative evaluee: score, questions "
        "reussies, questions manquees, feedback et concepts manquants."
    )
    args_schema: type[BaseModel] = AssessmentResultsToolInput

    _snapshot: AssessmentLearningSnapshot = PrivateAttr()

    def __init__(self, *, snapshot: AssessmentLearningSnapshot) -> None:
        super().__init__()
        self._snapshot = snapshot

    @property
    def snapshot(self) -> AssessmentLearningSnapshot:
        return self._snapshot

    def _run(self, analysis_focus: str, include_strong_topics: bool = True) -> str:
        weak_evidence = [
            item
            for item in self._snapshot.evidence
            if item.evaluation_status in {"partial", "incorrect", "unanswered"}
        ]
        strong_evidence = [
            item
            for item in self._snapshot.evidence
            if item.evaluation_status == "correct"
        ]
        payload = {
            "analysis_focus": analysis_focus,
            "attempt_id": self._snapshot.attempt_id,
            "assessment_title": self._snapshot.assessment_title,
            "score_percent": self._snapshot.score_percent,
            "level": self._snapshot.level,
            "weak_topics": self._snapshot.weak_topics,
            "strong_topics": self._snapshot.strong_topics
            if include_strong_topics
            else [],
            "priority_questions": [
                self._format_evidence(item) for item in weak_evidence[:8]
            ],
            "mastered_questions": [
                self._format_evidence(item) for item in strong_evidence[:5]
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _format_evidence(self, item: AssessmentEvidenceItem) -> dict[str, object]:
        return {
            "question_id": item.question_id,
            "question_text": item.question_text,
            "evaluation_status": item.evaluation_status,
            "points_awarded": item.points_awarded,
            "points": item.points,
            "feedback": item.feedback,
            "missing_concepts": item.missing_concepts,
            "source_document_id": item.source_document_id,
            "source_document_title": item.source_document_title,
            "source_page_number": item.source_page_number,
            "source_excerpt": item.source_excerpt,
        }
