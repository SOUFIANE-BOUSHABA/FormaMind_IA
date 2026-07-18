from __future__ import annotations

from app.models.user import User
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
    def get_summary(self, user: User) -> DashboardSummary:
        learner_name = user.full_name.strip() or "Rabie"

        return DashboardSummary(
            learner_name=learner_name,
            learner_title="Apprenant en Intelligence Artificielle",
            greeting=f"Bonjour {learner_name},",
            subtitle=(
                "L'intelligence artificielle évolue rapidement. Voici vos "
                "prochaines étapes pour rester à la pointe."
            ),
            metrics=[
                DashboardMetric(
                    label="Score global",
                    value="85",
                    description="/100",
                    icon="verified",
                    tone="primary",
                    trend="+4 pts cette semaine",
                ),
                DashboardMetric(
                    label="Niveau actuel",
                    value="Avancé",
                    description="Expert Lvl 12 • Top 5%",
                    icon="award",
                    tone="secondary",
                ),
                DashboardMetric(
                    label="Documents",
                    value="142",
                    description="Analysés par l'IA",
                    icon="book",
                    tone="accent",
                ),
                DashboardMetric(
                    label="Évaluations",
                    value="28",
                    description="Terminées ce mois",
                    icon="checklist",
                    tone="error",
                ),
                DashboardMetric(
                    label="Apprentissage",
                    value="42h",
                    description="Temps total investi",
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
            skills=[
                SkillMetric(label="Deep L.", value=85),
                SkillMetric(label="CNN", value=70),
                SkillMetric(label="NLP", value=92, highlighted=True),
                SkillMetric(label="LLM", value=98, highlighted=True),
                SkillMetric(label="Prompt", value=65),
                SkillMetric(label="RAG", value=40),
                SkillMetric(label="Agents", value=30),
            ],
            agents=[
                AgentActivity(
                    name="Knowledge Agent",
                    status="online",
                    description='Extraction de données : "Global AI Trends 2024.pdf"',
                    tone="accent",
                ),
                AgentActivity(
                    name="Learning Coach",
                    status="active",
                    description=(
                        "Optimisation en cours : adaptation du niveau de difficulté..."
                    ),
                    tone="primary",
                ),
                AgentActivity(
                    name="Assessment Agent",
                    status="waiting",
                    description="Génération du quiz final en attente.",
                    tone="secondary",
                ),
            ],
            recommendation=Recommendation(
                eyebrow="Architecture RAG",
                title="Intégration LangChain & VectorDB",
                duration="45 min",
                badge="Certification",
                description=(
                    "Augmentez la pertinence de vos LLM en maîtrisant le flux "
                    "d'indexation et de récupération."
                ),
                action_label="Commencer le module",
            ),
            focus_areas=[
                FocusArea(
                    label="Fine-tuning de modèles", severity="critical", progress=33
                ),
                FocusArea(
                    label="Éthique & Biais IA", severity="important", progress=40
                ),
            ],
            recent_activity=[
                ActivityEntry(
                    title="Quiz NLP terminé",
                    description="Score : 92/100. Badge obtenu.",
                    timestamp="2h",
                    tone="primary",
                ),
                ActivityEntry(
                    title="Analyse documentaire",
                    description='"AI Policy.pdf" indexé avec succès.',
                    timestamp="Hier",
                    tone="secondary",
                ),
                ActivityEntry(
                    title="Simulation validée",
                    description="Optimisation PyTorch effectuée.",
                    timestamp="Cette semaine",
                    tone="accent",
                ),
            ],
        )
