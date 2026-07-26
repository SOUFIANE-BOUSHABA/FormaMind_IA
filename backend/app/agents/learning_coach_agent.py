from __future__ import annotations

import json
import logging
import re

from crewai import LLM, Agent, Crew, Task
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.learning_plan import (
    GenerateLearningPlanRequest,
    LearningActivityDraft,
    LearningModuleDraft,
    LearningPlanDraft,
)
from app.tools.assessment_results_tool import AssessmentResultsTool
from app.tools.learning_content_tool import LearningContentTool
from app.tools.study_schedule_tool import StudyScheduleTool

logger = logging.getLogger(__name__)


class LearningCoachAgentError(Exception):
    message = "La generation du plan d'apprentissage a echoue."


class LearningCoachConfigurationError(LearningCoachAgentError):
    message = "Le Learning Coach Agent n'est pas configure."


class LearningCoachOutputError(LearningCoachAgentError):
    message = "Le Learning Coach Agent n'a pas produit un plan valide."


class LearningCoachAgent:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_plan(
        self,
        *,
        request: GenerateLearningPlanRequest,
        assessment_results_tool: AssessmentResultsTool,
        learning_content_tool: LearningContentTool,
        study_schedule_tool: StudyScheduleTool,
    ) -> LearningPlanDraft:
        self._ensure_configured()
        self._prime_tools(
            request=request,
            assessment_results_tool=assessment_results_tool,
            learning_content_tool=learning_content_tool,
        )

        try:
            result = self._run_crew(
                request=request,
                assessment_results_tool=assessment_results_tool,
                learning_content_tool=learning_content_tool,
                study_schedule_tool=study_schedule_tool,
            )
            draft = self._parse_result(result)
            return self._normalize_draft(
                request=request,
                draft=draft,
                learning_content_tool=learning_content_tool,
            )
        except LearningCoachOutputError:
            return self._fallback_draft(
                request=request,
                assessment_results_tool=assessment_results_tool,
                learning_content_tool=learning_content_tool,
            )
        except Exception:
            logger.exception("CrewAI learning plan generation failed; using fallback.")
            return self._fallback_draft(
                request=request,
                assessment_results_tool=assessment_results_tool,
                learning_content_tool=learning_content_tool,
            )

    def _ensure_configured(self) -> None:
        if not self._settings.gemini_api_key:
            raise LearningCoachConfigurationError

    def _prime_tools(
        self,
        *,
        request: GenerateLearningPlanRequest,
        assessment_results_tool: AssessmentResultsTool,
        learning_content_tool: LearningContentTool,
    ) -> None:
        snapshot = assessment_results_tool.snapshot
        assessment_results_tool._run(
            analysis_focus="Identifier les lacunes prioritaires et les acquis",
            include_strong_topics=True,
        )
        concepts = self._priority_concepts(snapshot)
        for concept in concepts[: self._settings.learning_plan_max_modules]:
            learning_content_tool._run(
                topic=concept,
                missing_concepts=[concept],
                target_difficulty=snapshot.level,
                desired_learning_objective=(
                    "Construire une activite de remediation sourcee."
                ),
            )

    def _run_crew(
        self,
        *,
        request: GenerateLearningPlanRequest,
        assessment_results_tool: AssessmentResultsTool,
        learning_content_tool: LearningContentTool,
        study_schedule_tool: StudyScheduleTool,
    ) -> object:
        agent = Agent(
            role="Learning Coach Agent FormaMind",
            goal=(
                "Transformer les resultats d'evaluation en plan "
                "d'apprentissage personnalise, actionnable et source."
            ),
            backstory=(
                "Tu es un coach pedagogique specialise en intelligence "
                "artificielle. Tu analyses les lacunes, choisis les priorites, "
                "retrouves les supports utiles et proposes des taches concretes."
            ),
            tools=[
                assessment_results_tool,
                learning_content_tool,
                study_schedule_tool,
            ],
            llm=self._build_llm(),
            verbose=False,
            allow_delegation=False,
        )
        task = Task(
            description=self._task_description(request),
            expected_output=(
                "Un JSON valide correspondant a LearningPlanDraft. Chaque "
                "activite doit citer au moins une source CONTENT_SOURCE_n."
            ),
            agent=agent,
            output_pydantic=LearningPlanDraft,
        )
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        return crew.kickoff()

    def _build_llm(self) -> LLM:
        return LLM(
            model=self._gemini_model_name(self._settings.gemini_model),
            api_key=self._settings.gemini_api_key,
            temperature=self._settings.learning_coach_temperature,
        )

    def _gemini_model_name(self, model: str) -> str:
        if model.startswith("gemini/"):
            return model
        if model.startswith("models/"):
            return f"gemini/{model.removeprefix('models/')}"
        return f"gemini/{model}"

    def _parse_result(self, result: object) -> LearningPlanDraft:
        pydantic_output = getattr(result, "pydantic", None)
        if isinstance(pydantic_output, LearningPlanDraft):
            return pydantic_output

        for task_output in getattr(result, "tasks_output", []) or []:
            pydantic_output = getattr(task_output, "pydantic", None)
            if isinstance(pydantic_output, LearningPlanDraft):
                return pydantic_output

        json_dict = getattr(result, "json_dict", None)
        if isinstance(json_dict, dict):
            try:
                return LearningPlanDraft.model_validate(json_dict)
            except ValidationError as exc:
                raise LearningCoachOutputError from exc

        raw_output = getattr(result, "raw", None)
        if isinstance(raw_output, str):
            cleaned = self._strip_json_fence(raw_output)
            try:
                return LearningPlanDraft.model_validate_json(cleaned)
            except ValidationError as exc:
                raise LearningCoachOutputError from exc
            except ValueError:
                match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
                if match is None:
                    raise LearningCoachOutputError from None
                try:
                    payload = json.loads(match.group(0))
                    return LearningPlanDraft.model_validate(payload)
                except (json.JSONDecodeError, ValidationError) as exc:
                    raise LearningCoachOutputError from exc

        raise LearningCoachOutputError

    def _normalize_draft(
        self,
        *,
        request: GenerateLearningPlanRequest,
        draft: LearningPlanDraft,
        learning_content_tool: LearningContentTool,
    ) -> LearningPlanDraft:
        source_map = learning_content_tool.source_map
        if not source_map:
            raise LearningCoachOutputError

        modules: list[LearningModuleDraft] = []
        seen_modules: set[str] = set()
        for module in draft.modules:
            module_key = module.title.strip().lower()
            if module_key in seen_modules:
                continue
            seen_modules.add(module_key)
            activities = [
                activity
                for activity in module.activities
                if all(ref in source_map for ref in activity.source_refs)
            ]
            if not activities:
                continue
            modules.append(
                module.model_copy(
                    update={
                        "activities": activities[
                            : self._settings.learning_plan_max_activities_per_module
                        ],
                    }
                )
            )
            if len(modules) == self._settings.learning_plan_max_modules:
                break

        if not modules:
            return self._fallback_draft(
                request=request,
                assessment_results_tool=None,
                learning_content_tool=learning_content_tool,
            )

        return LearningPlanDraft(
            title=(request.title or draft.title)[:180],
            generated_summary=draft.generated_summary,
            modules=modules,
        )

    def _fallback_draft(
        self,
        *,
        request: GenerateLearningPlanRequest,
        assessment_results_tool: AssessmentResultsTool | None,
        learning_content_tool: LearningContentTool,
    ) -> LearningPlanDraft:
        source_items = sorted(learning_content_tool.source_map.items())
        if not source_items:
            raise LearningCoachOutputError

        snapshot = (
            assessment_results_tool.snapshot
            if assessment_results_tool is not None
            else None
        )
        topics = self._priority_concepts(snapshot) if snapshot is not None else []
        if not topics:
            topics = [source_items[0][1].document_title]

        modules: list[LearningModuleDraft] = []
        selected_topics = topics[: self._settings.learning_plan_max_modules]
        for index, topic in enumerate(selected_topics):
            source_ref, chunk = source_items[index % len(source_items)]
            modules.append(
                LearningModuleDraft(
                    title=f"Renforcer: {self._truncate(topic, 90)}",
                    objective=(
                        "Reprendre la notion, la reformuler, puis verifier "
                        "la comprehension avec une mini-activite."
                    ),
                    topic=self._truncate(topic, 160),
                    priority="high" if index == 0 else "medium",
                    activities=[
                        LearningActivityDraft(
                            title=f"Relire la page {chunk.page_number}",
                            instructions=(
                                "Relisez l'extrait source, notez trois idees "
                                "cles, puis expliquez-les avec vos propres mots."
                            ),
                            type="review",
                            duration_minutes=25,
                            source_refs=[source_ref],
                        ),
                        LearningActivityDraft(
                            title="S'entrainer sur la notion",
                            instructions=(
                                "Creez un exemple simple, puis comparez votre "
                                "reponse avec la source citee."
                            ),
                            type="practice",
                            duration_minutes=20,
                            source_refs=[source_ref],
                        ),
                    ],
                )
            )

        return LearningPlanDraft(
            title=request.title or "Plan de remediation personnalise",
            generated_summary=(
                "Plan genere a partir des resultats d'evaluation et des "
                "sources documentaires retrouvees."
            ),
            modules=modules,
        )

    def _priority_concepts(self, snapshot: object) -> list[str]:
        if snapshot is None:
            return []

        concepts: list[str] = []
        for evidence in getattr(snapshot, "evidence", []):
            if evidence.evaluation_status not in {
                "partial",
                "incorrect",
                "unanswered",
            }:
                continue
            concepts.extend(evidence.missing_concepts)
            if not evidence.missing_concepts:
                concepts.append(evidence.question_text)

        concepts.extend(getattr(snapshot, "weak_topics", []))
        return self._unique_limited(concepts, limit=8)

    def _unique_limited(self, values: list[str], *, limit: int) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            cleaned = " ".join(value.split())
            if not cleaned or cleaned.lower() in seen:
                continue
            seen.add(cleaned.lower())
            result.append(self._truncate(cleaned, 160))
            if len(result) == limit:
                break
        return result

    def _truncate(self, text: str, max_length: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= max_length:
            return normalized
        return f"{normalized[: max_length - 1].rstrip()}..."

    def _strip_json_fence(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.removeprefix("```json").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned.removesuffix("```").strip()
        return cleaned

    def _task_description(self, request: GenerateLearningPlanRequest) -> str:
        return f"""
Genere un plan d'apprentissage FormaMind en francais.

Contraintes obligatoires:
- Utilise AssessmentResultsTool pour analyser le score, les lacunes et les acquis.
- Utilise LearningContentTool pour chaque module prioritaire.
- Utilise StudyScheduleTool pour verifier le budget quotidien:
  {request.daily_minutes} minutes par jour.
- Intensite demandee: {request.intensity}.
- Date de debut: {request.start_date.isoformat()}.
- Chaque activite doit avoir type parmi review, practice, quiz, reflection.
- Chaque activite doit citer au moins une source CONTENT_SOURCE_n retournee.
- Ne propose pas d'activite non fondee sur les documents.
- Priorise les questions incorrectes, partielles ou sans reponse.
- Varie les taches: relecture, pratique, mini-verification, synthese.
- Retourne uniquement le JSON demande par LearningPlanDraft.
""".strip()
