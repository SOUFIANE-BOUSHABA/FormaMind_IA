from __future__ import annotations

import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from app.schemas.soutenance import LearnerProfileSnapshot, ProjectContextSnapshot


class ProjectContextToolInput(BaseModel):
    topic: str = Field(default="overview", max_length=120)
    desired_detail_level: str = Field(default="concise", max_length=40)


class ProjectContextTool(BaseTool):
    name: str = "ProjectContextTool"
    description: str = (
        "Fournit un contexte projet FormaMind AI fiable depuis une allowlist "
        "documentaire preparee par l'application."
    )
    args_schema: type[BaseModel] = ProjectContextToolInput

    _snapshot: ProjectContextSnapshot = PrivateAttr()

    def __init__(self, *, snapshot: ProjectContextSnapshot) -> None:
        super().__init__()
        self._snapshot = snapshot

    @property
    def snapshot(self) -> ProjectContextSnapshot:
        return self._snapshot

    def _run(
        self,
        topic: str = "overview",
        desired_detail_level: str = "concise",
    ) -> str:
        payload = self._snapshot.model_dump()
        payload["requested_topic"] = topic
        payload["detail_level"] = desired_detail_level
        return json.dumps(payload, ensure_ascii=False, indent=2)


class LearnerProfileToolInput(BaseModel):
    focus_category: str = Field(default="global", max_length=80)
    include_previous_sessions: bool = True


class LearnerProfileTool(BaseTool):
    name: str = "LearnerProfileTool"
    description: str = (
        "Expose uniquement le profil pedagogique du learner authentifie: "
        "scores, lacunes, acquis et progression."
    )
    args_schema: type[BaseModel] = LearnerProfileToolInput

    _snapshot: LearnerProfileSnapshot = PrivateAttr()

    def __init__(self, *, snapshot: LearnerProfileSnapshot) -> None:
        super().__init__()
        self._snapshot = snapshot

    @property
    def snapshot(self) -> LearnerProfileSnapshot:
        return self._snapshot

    def _run(
        self,
        focus_category: str = "global",
        include_previous_sessions: bool = True,
    ) -> str:
        payload = self._snapshot.model_dump()
        payload["focus_category"] = focus_category
        if not include_previous_sessions:
            payload["previous_soutenance_scores"] = []
            payload["previous_soutenance_weaknesses"] = []
        return json.dumps(payload, ensure_ascii=False, indent=2)


class RubricCriterion(BaseModel):
    criterion: str
    label: str
    weight: int
    instructions: str


class SoutenanceRubricToolInput(BaseModel):
    purpose: str = Field(default="evaluation", max_length=80)


class SoutenanceRubricTool(BaseTool):
    name: str = "SoutenanceRubricTool"
    description: str = (
        "Retourne la grille de soutenance deterministe et calcule les scores "
        "ponderes sans LLM, reseau ou base de donnees."
    )
    args_schema: type[BaseModel] = SoutenanceRubricToolInput

    criteria: list[RubricCriterion] = [
        RubricCriterion(
            criterion="technical_accuracy",
            label="Exactitude technique",
            weight=30,
            instructions="Verifier la justesse des concepts et du vocabulaire.",
        ),
        RubricCriterion(
            criterion="clarity",
            label="Clarte",
            weight=15,
            instructions="Evaluer si la reponse est comprehensible et directe.",
        ),
        RubricCriterion(
            criterion="structure",
            label="Structure",
            weight=10,
            instructions="Evaluer l'organisation et la progression de la reponse.",
        ),
        RubricCriterion(
            criterion="architecture",
            label="Architecture",
            weight=20,
            instructions="Verifier la comprehension des composants et frontieres.",
        ),
        RubricCriterion(
            criterion="choice_justification",
            label="Justification des choix",
            weight=10,
            instructions="Evaluer la capacite a justifier les compromis.",
        ),
        RubricCriterion(
            criterion="security_limitations",
            label="Securite et limites",
            weight=10,
            instructions="Verifier la conscience des risques et limites.",
        ),
        RubricCriterion(
            criterion="communication",
            label="Communication",
            weight=5,
            instructions="Evaluer la posture de soutenance et la synthese.",
        ),
    ]

    def _run(self, purpose: str = "evaluation") -> str:
        return json.dumps(
            {
                "purpose": purpose,
                "score_range": "0-100 par critere",
                "criteria": [criterion.model_dump() for criterion in self.criteria],
                "total_weight": self.total_weight(),
            },
            ensure_ascii=False,
            indent=2,
        )

    def total_weight(self) -> int:
        return sum(criterion.weight for criterion in self.criteria)

    def weights(self) -> dict[str, int]:
        return {criterion.criterion: criterion.weight for criterion in self.criteria}

    def labels(self) -> dict[str, str]:
        return {criterion.criterion: criterion.label for criterion in self.criteria}

    def calculate_total(self, scores: dict[str, float]) -> float:
        missing = set(self.weights()) - set(scores)
        extra = set(scores) - set(self.weights())
        if missing or extra:
            raise ValueError("Rubric criteria mismatch.")

        total = 0.0
        for criterion, weight in self.weights().items():
            score = scores[criterion]
            if not 0 <= score <= 100:
                raise ValueError("Rubric score out of range.")
            total += score * (weight / 100)
        return round(total, 2)
