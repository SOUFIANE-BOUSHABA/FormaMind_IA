from __future__ import annotations

import json
import logging
import re

from crewai import LLM, Agent, Crew, Task
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.assessment import (
    AssessmentDraft,
    GenerateAssessmentRequest,
    GeneratedQuestionDraft,
    QuestionType,
)
from app.schemas.rag import RetrievedChunk
from app.tools.assessment_context_tool import AssessmentContextTool

logger = logging.getLogger(__name__)


class AssessmentAgentError(Exception):
    message = "La generation de l'evaluation a echoue."


class AssessmentAgentConfigurationError(AssessmentAgentError):
    message = "Le service de generation d'evaluations n'est pas configure."


class AssessmentAgentOutputError(AssessmentAgentError):
    message = "La generation n'a pas produit une evaluation valide."


class AssessmentAgent:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate_assessment(
        self,
        *,
        request: GenerateAssessmentRequest,
        context_tool: AssessmentContextTool,
    ) -> AssessmentDraft:
        self._ensure_configured()
        self._prime_context(request=request, context_tool=context_tool)

        try:
            result = self._run_crew(request=request, context_tool=context_tool)
            draft = self._parse_result(result)
            return self._normalize_draft(
                request=request,
                draft=draft,
                source_map=context_tool.source_map,
            )
        except AssessmentAgentOutputError:
            return self._fallback_draft(
                request=request,
                source_map=context_tool.source_map,
            )
        except Exception:
            logger.exception("CrewAI assessment generation failed; using fallback.")
            return self._fallback_draft(
                request=request,
                source_map=context_tool.source_map,
            )

    def _run_crew(
        self,
        *,
        request: GenerateAssessmentRequest,
        context_tool: AssessmentContextTool,
    ) -> object:
        agent = Agent(
            role="Agent d'evaluation pedagogique FormaMind",
            goal=(
                "Creer des evaluations fiables, utiles et strictement fondees "
                "sur les supports de formation selectionnes."
            ),
            backstory=(
                "Tu es un expert en ingenierie pedagogique. Tu rediges des "
                "questions claires, corrigees et sourcees pour verifier la "
                "comprehension des apprenants a partir du contexte fourni."
            ),
            tools=[context_tool],
            llm=self._build_llm(),
            verbose=False,
            allow_delegation=False,
        )

        task = Task(
            description=self._task_description(request),
            expected_output=(
                "Un objet JSON valide contenant title, difficulty et questions. "
                "Chaque question doit etre basee sur une source retournee par "
                "AssessmentContextTool."
            ),
            agent=agent,
            output_pydantic=AssessmentDraft,
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        return crew.kickoff()

    def _ensure_configured(self) -> None:
        if not self._settings.gemini_api_key:
            raise AssessmentAgentConfigurationError

    def _build_llm(self) -> LLM:
        return LLM(
            model=self._gemini_model_name(self._settings.gemini_model),
            api_key=self._settings.gemini_api_key,
            temperature=self._settings.assessment_agent_temperature,
        )

    def _gemini_model_name(self, model: str) -> str:
        if model.startswith("gemini/"):
            return model
        if model.startswith("models/"):
            return f"gemini/{model.removeprefix('models/')}"
        return f"gemini/{model}"

    def _prime_context(
        self,
        *,
        request: GenerateAssessmentRequest,
        context_tool: AssessmentContextTool,
    ) -> None:
        for topic in request.topics:
            for query in self._context_queries(topic):
                context_tool._run(topic=query, difficulty=request.difficulty)

    def _context_queries(self, topic: str) -> list[str]:
        cleaned = topic.strip()
        return [
            cleaned,
            f"{cleaned} concepts cles",
            f"{cleaned} definitions importantes",
            f"{cleaned} processus et etapes",
            f"{cleaned} exemples et limites",
        ]

    def _parse_result(self, result: object) -> AssessmentDraft:
        pydantic_output = getattr(result, "pydantic", None)
        if isinstance(pydantic_output, AssessmentDraft):
            return pydantic_output

        for task_output in getattr(result, "tasks_output", []) or []:
            pydantic_output = getattr(task_output, "pydantic", None)
            if isinstance(pydantic_output, AssessmentDraft):
                return pydantic_output

        json_dict = getattr(result, "json_dict", None)
        if isinstance(json_dict, dict):
            try:
                return AssessmentDraft.model_validate(json_dict)
            except ValidationError as exc:
                raise AssessmentAgentOutputError from exc

        raw_output = getattr(result, "raw", None)
        if isinstance(raw_output, str):
            return self._parse_raw_json(raw_output)

        raise AssessmentAgentOutputError

    def _parse_raw_json(self, raw_output: str) -> AssessmentDraft:
        cleaned = self._strip_json_fence(raw_output)

        try:
            return AssessmentDraft.model_validate_json(cleaned)
        except ValidationError as exc:
            raise AssessmentAgentOutputError from exc
        except ValueError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if match is None:
                raise AssessmentAgentOutputError from None

        try:
            payload = json.loads(match.group(0))
            return AssessmentDraft.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise AssessmentAgentOutputError from exc

    def _strip_json_fence(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.removeprefix("```json").strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned.removesuffix("```").strip()
        return cleaned

    def _normalize_draft(
        self,
        *,
        request: GenerateAssessmentRequest,
        draft: AssessmentDraft,
        source_map: dict[str, RetrievedChunk],
    ) -> AssessmentDraft:
        valid_questions = [
            question
            for question in draft.questions
            if (
                question.source_ref in source_map
                and question.type in request.question_types
            )
        ]

        fallback = self._fallback_draft(request=request, source_map=source_map)
        merged = valid_questions + fallback.questions
        seen: set[str] = set()
        questions: list[GeneratedQuestionDraft] = []

        for question in merged:
            key = self._question_identity(question)
            if key in seen:
                continue
            seen.add(key)
            questions.append(question)
            if len(questions) == request.question_count:
                break

        return AssessmentDraft(
            title=(request.title or draft.title or fallback.title)[:180],
            difficulty=request.difficulty,
            questions=questions,
        )

    def _question_identity(self, question: GeneratedQuestionDraft) -> str:
        normalized_text = re.sub(r"\W+", " ", question.text.lower()).strip()
        normalized_answer = re.sub(
            r"\W+",
            " ",
            question.correct_answer.lower(),
        ).strip()
        return f"{question.type}:{normalized_text}:{normalized_answer}"

    def _fallback_draft(
        self,
        *,
        request: GenerateAssessmentRequest,
        source_map: dict[str, RetrievedChunk],
    ) -> AssessmentDraft:
        source_items = self._ordered_sources(source_map)
        if not source_items:
            raise AssessmentAgentOutputError

        questions: list[GeneratedQuestionDraft] = []
        for index in range(request.question_count):
            source_ref, chunk = source_items[index % len(source_items)]
            question_type = request.question_types[index % len(request.question_types)]
            questions.append(
                self._fallback_question(
                    question_type=question_type,
                    source_ref=source_ref,
                    chunk=chunk,
                    index=index,
                )
            )

        title = request.title or f"Evaluation - {', '.join(request.topics[:2])}"
        return AssessmentDraft(
            title=title[:180],
            difficulty=request.difficulty,
            questions=questions,
        )

    def _ordered_sources(
        self,
        source_map: dict[str, RetrievedChunk],
    ) -> list[tuple[str, RetrievedChunk]]:
        return sorted(
            source_map.items(),
            key=lambda item: (
                -(item[1].relevance_score or 0),
                item[1].document_id,
                item[1].page_number,
                item[1].chunk_index,
            ),
        )

    def _fallback_question(
        self,
        *,
        question_type: QuestionType,
        source_ref: str,
        chunk: RetrievedChunk,
        index: int,
    ) -> GeneratedQuestionDraft:
        statement = self._statement_for_question(chunk.text, index)
        answer = self._truncate(statement, 500)

        if question_type == "multiple_choice":
            templates = [
                (
                    f"Selon {chunk.document_title}, page {chunk.page_number}, "
                    "quelle proposition resume le mieux l'idee principale ?"
                ),
                (
                    f"Dans {chunk.document_title}, page {chunk.page_number}, "
                    "quel element est correctement explique par l'extrait ?"
                ),
                (
                    f"Que faut-il retenir du passage de {chunk.document_title}, "
                    f"page {chunk.page_number} ?"
                ),
                (
                    f"Quelle affirmation correspond au contenu source de la "
                    f"page {chunk.page_number} ?"
                ),
                (
                    f"Quelle idee du document {chunk.document_title} est "
                    "appuyee par cet extrait ?"
                ),
            ]
            distractor_sets = [
                [
                    "Une conclusion absente du support.",
                    "Une definition sans lien avec l'extrait.",
                    "Une etape technique non mentionnee ici.",
                ],
                [
                    "Une interpretation qui n'est pas citee dans la source.",
                    "Un exemple non present dans le document.",
                    "Une generalisation qui depasse l'extrait.",
                ],
                [
                    "Une idee opposee au passage source.",
                    "Un detail administratif sans rapport.",
                    "Une recommandation que le texte ne donne pas.",
                ],
                [
                    "Un resultat non justifie par l'extrait.",
                    "Une notion qui appartient a un autre sujet.",
                    "Une hypothese ajoutee hors document.",
                ],
                [
                    "Une phrase qui contredit la source.",
                    "Une action non demandee par le passage.",
                    "Une synthese trop vague pour etre correcte.",
                ],
            ]
            template_index = index % len(templates)
            return GeneratedQuestionDraft(
                type="multiple_choice",
                text=templates[template_index],
                options=[
                    {"text": answer, "is_correct": True},
                    *[
                        {"text": distractor, "is_correct": False}
                        for distractor in distractor_sets[template_index]
                    ],
                ],
                correct_answer=answer,
                explanation=(
                    "La bonne reponse reprend directement l'information "
                    f"sourcee dans {chunk.document_title}, page {chunk.page_number}."
                ),
                points=1,
                source_ref=source_ref,
            )

        if question_type == "true_false":
            return GeneratedQuestionDraft(
                type="true_false",
                text=f"Vrai ou faux: {answer}",
                options=[
                    {"text": "Vrai", "is_correct": True},
                    {"text": "Faux", "is_correct": False},
                ],
                correct_answer="Vrai",
                explanation=(
                    "L'affirmation est appuyee par l'extrait source "
                    f"page {chunk.page_number}."
                ),
                points=1,
                source_ref=source_ref,
            )

        if question_type == "short_answer":
            return GeneratedQuestionDraft(
                type="short_answer",
                text=(
                    f"En une phrase, quel point faut-il retenir de "
                    f"{chunk.document_title}, page {chunk.page_number} ?"
                ),
                correct_answer=answer,
                explanation=(
                    "La reponse attendue doit reprendre l'idee centrale "
                    "du passage source."
                ),
                points=1,
                source_ref=source_ref,
            )

        return GeneratedQuestionDraft(
            type="explanation",
            text=(
                f"Expliquez l'idee suivante avec vos mots: "
                f"{self._truncate(statement, 220)}"
            ),
            correct_answer=answer,
            explanation=(
                "L'explication doit rester coherente avec le passage source "
                f"du document {chunk.document_title}."
            ),
            points=1,
            source_ref=source_ref,
        )

    def _statement_for_question(self, text: str, index: int) -> str:
        normalized = " ".join(text.split())
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized)
            if len(sentence.strip()) >= 24
        ]
        if sentences:
            return sentences[index % len(sentences)]

        words = normalized.split()
        if len(words) <= 28:
            return normalized

        window_size = 28
        start = (index * window_size) % max(len(words) - window_size + 1, 1)
        return " ".join(words[start : start + window_size])

    def _truncate(self, text: str, max_length: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= max_length:
            return normalized
        return f"{normalized[: max_length - 1].rstrip()}..."

    def _task_description(self, request: GenerateAssessmentRequest) -> str:
        title_instruction = request.title or "Creer un titre pedagogique concis"

        return f"""
Genere une evaluation FormaMind en francais.

Contraintes obligatoires:
- Titre demande: {title_instruction}
- Difficulte: {request.difficulty}
- Nombre exact de questions: {request.question_count}
- Types autorises: {", ".join(request.question_types)}
- Sujets a couvrir: {", ".join(request.topics)}
- Utilise AssessmentContextTool pour rechercher le contexte documentaire.
- N'invente jamais une information absente du contexte.
- Chaque question doit contenir source_ref avec une valeur SOURCE_1, SOURCE_2, etc.
- Varie les formulations et evite les questions triviales.
- Les explications doivent aider l'apprenant a comprendre la bonne reponse.

Regles par type:
- multiple_choice: exactement 4 options, une seule correcte.
- true_false: exactement deux options, "Vrai" et "Faux", une seule correcte.
- short_answer: aucune option, reponse courte attendue.
- explanation: aucune option, reponse explicative attendue.

Retourne uniquement la structure demandee par le schema.
""".strip()
