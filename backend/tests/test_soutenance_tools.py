from __future__ import annotations

import json

from app.schemas.soutenance import LearnerProfileSnapshot, ProjectContextSnapshot
from app.tools.soutenance_tools import (
    LearnerProfileTool,
    ProjectContextTool,
    SoutenanceRubricTool,
)


def test_project_context_tool_exposes_only_snapshot_data() -> None:
    snapshot = ProjectContextSnapshot(
        project_objective="Plateforme educative multi-agents.",
        backend_stack=["FastAPI", "CrewAI"],
        frontend_stack=["React"],
        database="SQLite",
        implemented_features=["RAG"],
        endpoints=["/api/v1/assistant/ask"],
        security_boundaries=["Ownership par user_id"],
        known_limits=["Pas de micro"],
    )
    tool = ProjectContextTool(snapshot=snapshot)

    payload = json.loads(tool._run())

    assert payload["database"] == "SQLite"
    assert "secret" not in json.dumps(payload).lower()
    assert "path" not in json.dumps(payload).lower()


def test_learner_profile_tool_can_hide_previous_soutenance_sessions() -> None:
    snapshot = LearnerProfileSnapshot(
        learner_name="Learner",
        global_score=62,
        current_level="Preparation partielle",
        recent_assessment_scores=[60, 64],
        weak_topics=["architecture"],
        strong_topics=["RAG"],
        missing_concepts=["securite"],
        learning_plan_progress=[50],
        previous_soutenance_scores=[70],
        previous_soutenance_weaknesses=["communication"],
    )
    tool = LearnerProfileTool(snapshot=snapshot)

    payload = json.loads(tool._run(include_previous_sessions=False))

    assert payload["previous_soutenance_scores"] == []
    assert payload["previous_soutenance_weaknesses"] == []


def test_soutenance_rubric_tool_weights_total_100_and_scores() -> None:
    tool = SoutenanceRubricTool()
    weights = tool.weights()

    total = tool.calculate_total({criterion: 80 for criterion in weights})

    assert sum(weights.values()) == 100
    assert total == 80
