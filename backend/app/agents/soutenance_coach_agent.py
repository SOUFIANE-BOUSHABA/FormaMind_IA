from __future__ import annotations

import json
import logging
import re

from crewai import LLM, Agent, Crew, Task
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.soutenance import (
    CATEGORY_LABELS,
    CreateSoutenanceSessionRequest,
    PublicSoutenanceQuestion,
    SoutenanceAnswerEvaluationDraft,
    SoutenanceQuestionDraft,
    SoutenanceSessionDraft,
)
from app.tools.soutenance_tools import (
    LearnerProfileTool,
    ProjectContextTool,
    SoutenanceRubricTool,
)

logger = logging.getLogger(__name__)


class SoutenanceCoachAgentError(Exception):
    message = "Le Soutenance Coach Agent a echoue."


class SoutenanceCoachConfigurationError(SoutenanceCoachAgentError):
    message = "Le Soutenance Coach Agent n'est pas configure."


class SoutenanceCoachOutputError(SoutenanceCoachAgentError):
    message = "Le Soutenance Coach Agent n'a pas produit une sortie valide."


class SoutenanceCoachAgent:
    role = "Membre de jury et coach de soutenance technique"
    goal = (
        "Simuler une soutenance realiste, poser des questions adaptees au projet "
        "et au niveau de l'apprenant, puis evaluer la qualite technique et "
        "pedagogique de ses reponses."
    )
    backstory = (
        "Expert en intelligence artificielle, architecture logicielle, "
        "developpement full-stack, securite, tests et pedagogie. Il possede "
        "l'experience d'un membre de jury capable de challenger les choix du "
        "candidat tout en fournissant des conseils constructifs."
    )

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_questions(
        self,
        *,
        request: CreateSoutenanceSessionRequest,
        project_context_tool: ProjectContextTool,
        learner_profile_tool: LearnerProfileTool,
        rubric_tool: SoutenanceRubricTool,
    ) -> SoutenanceSessionDraft:
        self._ensure_configured()
        self._prime_question_tools(
            project_context_tool=project_context_tool,
            learner_profile_tool=learner_profile_tool,
            rubric_tool=rubric_tool,
        )

        try:
            result = self._run_question_crew(
                request=request,
                project_context_tool=project_context_tool,
                learner_profile_tool=learner_profile_tool,
                rubric_tool=rubric_tool,
            )
            return self._parse_session_draft(result)
        except SoutenanceCoachOutputError:
            return self._fallback_session_draft(request=request)
        except Exception:
            logger.exception("CrewAI soutenance question generation failed.")
            return self._fallback_session_draft(request=request)

    def evaluate_answer(
        self,
        *,
        question: PublicSoutenanceQuestion,
        expected_concepts: list[str],
        evaluation_focus: str,
        answer_text: str,
        project_context_tool: ProjectContextTool,
        learner_profile_tool: LearnerProfileTool,
        rubric_tool: SoutenanceRubricTool,
    ) -> SoutenanceAnswerEvaluationDraft:
        self._ensure_configured()

        try:
            result = self._run_evaluation_crew(
                question=question,
                expected_concepts=expected_concepts,
                evaluation_focus=evaluation_focus,
                answer_text=answer_text,
                project_context_tool=project_context_tool,
                learner_profile_tool=learner_profile_tool,
                rubric_tool=rubric_tool,
            )
            return self._parse_evaluation_draft(result)
        except SoutenanceCoachOutputError:
            return self._fallback_evaluation(
                question=question,
                expected_concepts=expected_concepts,
                answer_text=answer_text,
                rubric_tool=rubric_tool,
            )
        except Exception:
            logger.exception("CrewAI soutenance answer evaluation failed.")
            return self._fallback_evaluation(
                question=question,
                expected_concepts=expected_concepts,
                answer_text=answer_text,
                rubric_tool=rubric_tool,
            )

    def _ensure_configured(self) -> None:
        if not self._settings.gemini_api_key:
            raise SoutenanceCoachConfigurationError

    def _run_question_crew(
        self,
        *,
        request: CreateSoutenanceSessionRequest,
        project_context_tool: ProjectContextTool,
        learner_profile_tool: LearnerProfileTool,
        rubric_tool: SoutenanceRubricTool,
    ) -> object:
        agent = Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=[project_context_tool, learner_profile_tool, rubric_tool],
            llm=self._build_llm(),
            verbose=False,
            allow_delegation=False,
        )
        task = Task(
            description=self._question_task_description(request),
            expected_output=(
                "Un JSON valide correspondant a SoutenanceSessionDraft avec "
                "exactement le nombre de questions demande."
            ),
            agent=agent,
            output_pydantic=SoutenanceSessionDraft,
        )
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        return crew.kickoff()

    def _run_evaluation_crew(
        self,
        *,
        question: PublicSoutenanceQuestion,
        expected_concepts: list[str],
        evaluation_focus: str,
        answer_text: str,
        project_context_tool: ProjectContextTool,
        learner_profile_tool: LearnerProfileTool,
        rubric_tool: SoutenanceRubricTool,
    ) -> object:
        agent = Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=[project_context_tool, learner_profile_tool, rubric_tool],
            llm=self._build_llm(),
            verbose=False,
            allow_delegation=False,
        )
        task = Task(
            description=self._evaluation_task_description(
                question=question,
                expected_concepts=expected_concepts,
                evaluation_focus=evaluation_focus,
                answer_text=answer_text,
            ),
            expected_output=(
                "Un JSON valide correspondant a SoutenanceAnswerEvaluationDraft."
            ),
            agent=agent,
            output_pydantic=SoutenanceAnswerEvaluationDraft,
        )
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        return crew.kickoff()

    def _build_llm(self) -> LLM:
        return LLM(
            model=self._gemini_model_name(self._settings.gemini_model),
            api_key=self._settings.gemini_api_key,
            temperature=self._settings.soutenance_agent_temperature,
        )

    def _gemini_model_name(self, model: str) -> str:
        if model.startswith("gemini/"):
            return model
        if model.startswith("models/"):
            return f"gemini/{model.removeprefix('models/')}"
        return f"gemini/{model}"

    def _prime_question_tools(
        self,
        *,
        project_context_tool: ProjectContextTool,
        learner_profile_tool: LearnerProfileTool,
        rubric_tool: SoutenanceRubricTool,
    ) -> None:
        project_context_tool._run(topic="architecture", desired_detail_level="concise")
        learner_profile_tool._run(focus_category="global")
        rubric_tool._run(purpose="generation_et_evaluation")

    def _parse_session_draft(self, result: object) -> SoutenanceSessionDraft:
        output = self._extract_pydantic(result, SoutenanceSessionDraft)
        if isinstance(output, SoutenanceSessionDraft):
            return output

        raw = self._extract_raw(result)
        if raw is None:
            raise SoutenanceCoachOutputError

        try:
            return SoutenanceSessionDraft.model_validate_json(raw)
        except ValidationError as exc:
            raise SoutenanceCoachOutputError from exc
        except ValueError:
            return SoutenanceSessionDraft.model_validate(self._json_payload(raw))

    def _parse_evaluation_draft(
        self,
        result: object,
    ) -> SoutenanceAnswerEvaluationDraft:
        output = self._extract_pydantic(result, SoutenanceAnswerEvaluationDraft)
        if isinstance(output, SoutenanceAnswerEvaluationDraft):
            return output

        raw = self._extract_raw(result)
        if raw is None:
            raise SoutenanceCoachOutputError

        try:
            return SoutenanceAnswerEvaluationDraft.model_validate_json(raw)
        except ValidationError as exc:
            raise SoutenanceCoachOutputError from exc
        except ValueError:
            return SoutenanceAnswerEvaluationDraft.model_validate(
                self._json_payload(raw)
            )

    def _extract_pydantic(self, result: object, model: type[object]) -> object | None:
        pydantic_output = getattr(result, "pydantic", None)
        if isinstance(pydantic_output, model):
            return pydantic_output

        for task_output in getattr(result, "tasks_output", []) or []:
            pydantic_output = getattr(task_output, "pydantic", None)
            if isinstance(pydantic_output, model):
                return pydantic_output
        return None

    def _extract_raw(self, result: object) -> str | None:
        json_dict = getattr(result, "json_dict", None)
        if isinstance(json_dict, dict):
            return json.dumps(json_dict)

        raw = getattr(result, "raw", None)
        if isinstance(raw, str):
            return self._strip_json_fence(raw)
        return None

    def _json_payload(self, text: str) -> dict[str, object]:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match is None:
            raise SoutenanceCoachOutputError
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise SoutenanceCoachOutputError from exc
        if not isinstance(payload, dict):
            raise SoutenanceCoachOutputError
        return payload

    def _fallback_session_draft(
        self,
        *,
        request: CreateSoutenanceSessionRequest,
    ) -> SoutenanceSessionDraft:
        categories = self._distributed_categories(
            categories=list(request.question_categories),
            question_count=request.question_count,
        )
        questions: list[SoutenanceQuestionDraft] = []
        for index, category in enumerate(categories):
            label = CATEGORY_LABELS[category]
            questions.append(
                SoutenanceQuestionDraft(
                    local_id=f"Q{index + 1}",
                    text=self._fallback_question_text(
                        category=category,
                        label=label,
                        difficulty=request.difficulty,
                    ),
                    category=category,
                    difficulty=self._question_difficulty(
                        requested=request.difficulty,
                        index=index,
                    ),
                    expected_concepts=self._expected_concepts(category),
                    evaluation_focus=self._evaluation_focus(category),
                    follow_up_hint=(
                        "Demander un exemple concret relie a FormaMind AI si la "
                        "reponse reste trop generale."
                    ),
                    order_index=index,
                )
            )

        return SoutenanceSessionDraft(
            title=request.title or "Simulation de soutenance FormaMind AI",
            introduction=(
                "Vous allez repondre a une serie de questions de jury sur "
                "l'architecture, les agents IA, la securite et les choix du projet."
            ),
            questions=questions,
        )

    def _fallback_evaluation(
        self,
        *,
        question: PublicSoutenanceQuestion,
        expected_concepts: list[str],
        answer_text: str,
        rubric_tool: SoutenanceRubricTool,
    ) -> SoutenanceAnswerEvaluationDraft:
        lowered_answer = answer_text.lower()
        covered = [
            concept
            for concept in expected_concepts
            if concept.lower().split()[0] in lowered_answer
        ]
        coverage = len(covered) / max(len(expected_concepts), 1)
        base_score = 45 + (coverage * 35)
        if len(answer_text.split()) >= 45:
            base_score += 10
        base_score = min(round(base_score, 2), 92)

        rubric_scores = []
        for criterion in rubric_tool.criteria:
            adjustment = 0
            if criterion.criterion == "technical_accuracy":
                adjustment = 4 if coverage >= 0.5 else -8
            if criterion.criterion == "structure" and len(answer_text.split()) < 30:
                adjustment = -6
            score = max(min(base_score + adjustment, 100), 0)
            rubric_scores.append(
                {
                    "criterion": criterion.criterion,
                    "score": round(score, 2),
                    "comment": f"Evaluation deterministe: {criterion.label}.",
                }
            )

        missing = [
            concept for concept in expected_concepts if concept not in covered
        ] or ["Donner davantage d'exemples relies au projet."]
        return SoutenanceAnswerEvaluationDraft(
            question_id=question.id,
            rubric_scores=rubric_scores,
            feedback=(
                "Votre reponse couvre une partie des attentes. Renforcez la "
                "precision technique et reliez davantage vos arguments au projet."
            ),
            strengths=["Reponse exploitable et orientee soutenance."],
            missing_concepts=missing[:5],
            improved_answer=(
                "Une reponse plus solide cite le composant concerne, explique "
                "son role, justifie le choix technique, puis mentionne une limite "
                "ou un test de validation."
            ),
            recommendation=(
                "Preparez une reponse structuree en trois temps: contexte, choix, "
                "limites et verification."
            ),
        )

    def _distributed_categories(
        self,
        *,
        categories: list[str],
        question_count: int,
    ) -> list[str]:
        return [categories[index % len(categories)] for index in range(question_count)]

    def _question_difficulty(self, *, requested: str, index: int) -> str:
        if requested != "adaptive":
            return requested
        sequence = ["intermediate", "intermediate", "advanced"]
        return sequence[index % len(sequence)]

    def _fallback_question_text(
        self,
        *,
        category: str,
        label: str,
        difficulty: str,
    ) -> str:
        prompts = {
            "ai_concepts": (
                "Expliquez comment FormaMind AI utilise le RAG et les agents IA "
                "pour produire des reponses ou activites sourcees."
            ),
            "architecture": (
                "Presentez l'architecture backend/frontend de FormaMind AI et "
                "la responsabilite des services applicatifs."
            ),
            "deployment": (
                "Comment prepareriez-vous FormaMind AI pour un deploiement "
                "plus robuste sans changer les frontieres metier ?"
            ),
            "jury_challenge": (
                "Un membre du jury affirme que vos agents ne sont que des appels "
                "LLM. Comment defendriez-vous leur comportement agentique ?"
            ),
            "limitations": (
                "Quelles limites techniques et pedagogiques reconnaissez-vous "
                "dans l'etat actuel de FormaMind AI ?"
            ),
            "project_choices": (
                "Justifiez vos choix de FastAPI, React, SQLAlchemy, ChromaDB, "
                "LlamaIndex et CrewAI dans ce projet."
            ),
            "security": (
                "Quelles protections empechent un agent ou un utilisateur de "
                "lire des donnees qui ne lui appartiennent pas ?"
            ),
            "technical": (
                "Decrivez le cycle technique complet depuis l'import PDF jusqu'a "
                "une reponse sourcee de l'assistant."
            ),
            "testing": (
                "Expliquez votre strategie de tests pour verifier les agents "
                "sans appeler Gemini en environnement de test."
            ),
        }
        suffix = " Adaptez votre reponse au niveau demande."
        if difficulty == "advanced":
            suffix = " Ajoutez les compromis et les risques."
        return prompts.get(category, f"Expliquez la categorie {label}.") + suffix

    def _expected_concepts(self, category: str) -> list[str]:
        mapping = {
            "ai_concepts": ["RAG", "CrewAI", "Gemini", "sources"],
            "architecture": ["FastAPI", "services", "repositories", "React"],
            "deployment": ["configuration", "environnements", "migration"],
            "jury_challenge": ["decisions", "tools", "validation", "memoire"],
            "limitations": ["limites", "risques", "scope", "ameliorations"],
            "project_choices": ["choix", "compromis", "stack", "justification"],
            "security": ["authentification", "ownership", "allowlist", "secrets"],
            "technical": ["PDF", "chunks", "embeddings", "Chroma"],
            "testing": ["pytest", "fakes", "ruff", "typecheck"],
        }
        return mapping.get(category, ["FormaMind AI", "architecture"])

    def _evaluation_focus(self, category: str) -> str:
        return (
            "Verifier que la reponse est exacte, structuree, reliee au projet "
            f"et couvre les concepts attendus pour {CATEGORY_LABELS[category]}."
        )

    def _question_task_description(
        self,
        request: CreateSoutenanceSessionRequest,
    ) -> str:
        categories = ", ".join(request.question_categories)
        return f"""
Genere une simulation de soutenance FormaMind AI en francais.

Tu dois utiliser ProjectContextTool, LearnerProfileTool et SoutenanceRubricTool.
Configuration:
- Mode: {request.mode}
- Difficulte: {request.difficulty}
- Nombre exact de questions: {request.question_count}
- Categories autorisees: {categories}

Contraintes:
- Questions uniques et reliees au projet FormaMind AI reel.
- Aucune question sur micro, webcam, speech-to-text ou feature non implementee.
- expected_concepts doit rester interne et fonde sur le projet.
- follow_up_hint est interne et ne doit pas reveler de correction.
- Retourne uniquement le schema SoutenanceSessionDraft.
""".strip()

    def _evaluation_task_description(
        self,
        *,
        question: PublicSoutenanceQuestion,
        expected_concepts: list[str],
        evaluation_focus: str,
        answer_text: str,
    ) -> str:
        return f"""
Evalue cette reponse de soutenance FormaMind AI en francais.

Question id: {question.id}
Question: {question.text}
Categorie: {question.category}
Concepts attendus: {", ".join(expected_concepts)}
Focus: {evaluation_focus}
Reponse candidat:
{answer_text}

Contraintes:
- Utilise SoutenanceRubricTool.
- Un score 0-100 par critere exact de la grille.
- Ne change pas question_id.
- Feedback constructif, points forts, concepts manquants, meilleure reponse.
- Retourne uniquement SoutenanceAnswerEvaluationDraft.
""".strip()

    def _strip_json_fence(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.removeprefix("```json").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned.removesuffix("```").strip()
        return cleaned
