from __future__ import annotations

import json
from datetime import date

from app.schemas.learning_plan import AssessmentLearningSnapshot
from app.schemas.rag import RetrievedChunk
from app.tools.assessment_results_tool import AssessmentResultsTool
from app.tools.learning_content_tool import LearningContentTool
from app.tools.study_schedule_tool import ScheduleActivityInput, StudyScheduleTool


class FakeRetrieverTool:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def search(
        self,
        *,
        user_id: int,
        document_ids: list[int],
        question: str,
    ) -> list[RetrievedChunk]:
        self.calls.append(
            {"document_ids": document_ids, "question": question, "user_id": user_id}
        )
        return [
            RetrievedChunk(
                vector_id="document-10-page-2-chunk-0",
                user_id=user_id,
                document_id=10,
                document_title="Cours CNN",
                page_number=2,
                chunk_index=0,
                text="La convolution detecte des motifs dans une image.",
                relevance_score=0.93,
            )
        ]


def test_learning_content_tool_scopes_retrieval_and_stores_source_refs() -> None:
    retriever = FakeRetrieverTool()
    tool = LearningContentTool(
        user_id=7,
        document_ids=[10],
        retriever_tool=retriever,
    )

    payload = json.loads(
        tool._run(
            topic="convolution",
            missing_concepts=["filtres"],
            target_difficulty="intermediate",
            desired_learning_objective="reprendre les bases",
        )
    )

    assert retriever.calls[0]["user_id"] == 7
    assert retriever.calls[0]["document_ids"] == [10]
    assert "filtres" in str(retriever.calls[0]["question"])
    assert payload["sources"][0]["source_ref"] == "CONTENT_SOURCE_1"
    assert "CONTENT_SOURCE_1" in tool.source_map


def test_study_schedule_respects_daily_minutes() -> None:
    schedule = StudyScheduleTool().build_schedule(
        activities=[
            ScheduleActivityInput(temp_id="a", duration_minutes=30),
            ScheduleActivityInput(temp_id="b", duration_minutes=25),
            ScheduleActivityInput(temp_id="c", duration_minutes=20),
        ],
        daily_minutes=45,
        start_date=date(2026, 7, 23),
        intensity="balanced",
    )

    assert schedule["activities"] == {
        "a": "2026-07-23",
        "b": "2026-07-24",
        "c": "2026-07-24",
    }
    assert schedule["target_end_date"] == "2026-07-24"


def test_assessment_results_tool_handles_empty_evidence() -> None:
    tool = AssessmentResultsTool(
        snapshot=AssessmentLearningSnapshot(
            attempt_id=1,
            assessment_title="Quiz",
            score_percent=0,
            level="A renforcer",
            document_ids=[],
            evidence=[],
        )
    )

    payload = json.loads(tool._run(analysis_focus="lacunes"))

    assert payload["attempt_id"] == 1
    assert payload["priority_questions"] == []
