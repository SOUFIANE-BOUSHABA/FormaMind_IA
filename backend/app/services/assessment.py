from __future__ import annotations

from math import ceil
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.assessment import (
    Assessment,
    AssessmentDocument,
    Question,
    QuestionOption,
)
from app.models.document import Document
from app.models.user import User
from app.rag.retriever import RetrieverTool
from app.repositories.assessment import (
    AssessmentRepository,
    get_ready_documents_for_user,
)
from app.schemas.assessment import (
    AssessmentDraft,
    AssessmentListResponse,
    AssessmentRead,
    AssessmentSort,
    AssessmentSummary,
    GenerateAssessmentRequest,
    GeneratedQuestionDraft,
    PublicAssessmentDocument,
    PublicQuestion,
    PublicQuestionOption,
)
from app.schemas.rag import RetrievedChunk


class AssessmentServiceError(Exception):
    message = "La gestion des evaluations a echoue."


class AssessmentDocumentsNotFoundError(AssessmentServiceError):
    message = (
        "Un ou plusieurs documents selectionnes sont introuvables ou non analyses."
    )


class AssessmentGenerationUnavailableError(AssessmentServiceError):
    message = "Le service de generation d'evaluations est temporairement indisponible."


class AssessmentGenerationConfigurationError(AssessmentServiceError):
    message = "Le service de generation d'evaluations n'est pas configure."


class AssessmentGenerationInvalidOutputError(AssessmentServiceError):
    message = (
        "Les documents selectionnes ne contiennent pas assez "
        "d'informations pour generer cette evaluation."
    )


class AssessmentNotFoundError(AssessmentServiceError):
    message = "L'evaluation demandee est introuvable."


class AssessmentService:
    def __init__(
        self,
        *,
        db: Session,
        settings: Settings,
        assessment_agent: Any | None = None,
        retriever_tool: RetrieverTool | None = None,
    ) -> None:
        self._db = db
        self._settings = settings
        self._repository = AssessmentRepository(db)
        if assessment_agent is None:
            from app.agents.assessment_agent import AssessmentAgent

            assessment_agent = AssessmentAgent(settings)
        self._assessment_agent = assessment_agent
        self._retriever_tool = retriever_tool

    def generate_assessment(
        self,
        *,
        current_user: User,
        request: GenerateAssessmentRequest,
    ) -> AssessmentRead:
        documents = self._get_ready_documents(
            current_user=current_user,
            document_ids=request.document_ids,
        )

        if self._retriever_tool is None:
            raise AssessmentGenerationUnavailableError

        from app.tools.assessment_context_tool import AssessmentContextTool

        context_tool = AssessmentContextTool(
            user_id=current_user.id,
            document_ids=request.document_ids,
            retriever_tool=self._retriever_tool,
        )

        from app.agents.assessment_agent import (
            AssessmentAgentConfigurationError,
            AssessmentAgentError,
            AssessmentAgentOutputError,
        )

        try:
            draft = self._assessment_agent.generate_assessment(
                request=request,
                context_tool=context_tool,
            )
        except AssessmentAgentConfigurationError as exc:
            raise AssessmentGenerationConfigurationError from exc
        except AssessmentAgentOutputError as exc:
            raise AssessmentGenerationInvalidOutputError from exc
        except AssessmentAgentError as exc:
            raise AssessmentGenerationUnavailableError from exc

        assessment = self._save_assessment(
            current_user=current_user,
            documents=documents,
            request=request,
            draft=draft,
            source_map=context_tool.source_map,
        )
        return self._to_read(assessment)

    def list_assessments(
        self,
        *,
        current_user: User,
        page: int,
        page_size: int,
        sort: AssessmentSort,
    ) -> AssessmentListResponse:
        offset = (page - 1) * page_size
        assessments, total = self._repository.list_for_user(
            user_id=current_user.id,
            limit=page_size,
            offset=offset,
            sort=sort,
        )
        total_pages = ceil(total / page_size) if total else 0

        return AssessmentListResponse(
            items=[self._to_summary(assessment) for assessment in assessments],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    def get_assessment(
        self,
        *,
        current_user: User,
        assessment_id: int,
    ) -> AssessmentRead:
        assessment = self._repository.get_by_id_for_user(
            assessment_id=assessment_id,
            user_id=current_user.id,
        )
        if assessment is None:
            raise AssessmentNotFoundError

        return self._to_read(assessment)

    def _get_ready_documents(
        self,
        *,
        current_user: User,
        document_ids: list[int],
    ) -> list[Document]:
        documents = get_ready_documents_for_user(
            db=self._db,
            user_id=current_user.id,
            document_ids=document_ids,
        )

        found_ids = {document.id for document in documents}
        if found_ids != set(document_ids):
            raise AssessmentDocumentsNotFoundError

        return documents

    def _save_assessment(
        self,
        *,
        current_user: User,
        documents: list[Document],
        request: GenerateAssessmentRequest,
        draft: AssessmentDraft,
        source_map: dict[str, RetrievedChunk],
    ) -> Assessment:
        assessment = Assessment(
            user_id=current_user.id,
            title=request.title or draft.title,
            difficulty=request.difficulty,
            status="generated",
            question_count=len(draft.questions),
        )

        for document in documents:
            assessment.documents.append(AssessmentDocument(document_id=document.id))

        for index, question_draft in enumerate(draft.questions):
            assessment.questions.append(
                self._question_from_draft(
                    draft=question_draft,
                    index=index,
                    source_map=source_map,
                )
            )

        self._repository.add(assessment)
        self._repository.commit()

        saved = self._repository.get_by_id_for_user(
            assessment_id=assessment.id,
            user_id=current_user.id,
        )
        if saved is None:
            raise AssessmentNotFoundError
        return saved

    def _question_from_draft(
        self,
        *,
        draft: GeneratedQuestionDraft,
        index: int,
        source_map: dict[str, RetrievedChunk],
    ) -> Question:
        source = source_map.get(draft.source_ref)
        if source is None:
            raise AssessmentGenerationInvalidOutputError

        question = Question(
            type=draft.type,
            text=draft.text,
            correct_answer=draft.correct_answer,
            explanation=draft.explanation,
            points=draft.points,
            order_index=index,
            source_document_id=source.document_id,
            source_page_number=source.page_number,
            source_excerpt=source.text,
        )

        for option_index, option in enumerate(draft.options):
            question.options.append(
                QuestionOption(
                    text=option.text,
                    is_correct=option.is_correct,
                    order_index=option_index,
                )
            )

        return question

    def _to_summary(self, assessment: Assessment) -> AssessmentSummary:
        return AssessmentSummary(
            id=assessment.id,
            title=assessment.title,
            difficulty=assessment.difficulty,
            status=assessment.status,
            question_count=assessment.question_count,
            created_at=assessment.created_at.isoformat(),
            updated_at=assessment.updated_at.isoformat(),
        )

    def _to_read(self, assessment: Assessment) -> AssessmentRead:
        return AssessmentRead(
            id=assessment.id,
            title=assessment.title,
            difficulty=assessment.difficulty,
            status=assessment.status,
            question_count=assessment.question_count,
            created_at=assessment.created_at.isoformat(),
            updated_at=assessment.updated_at.isoformat(),
            documents=[
                PublicAssessmentDocument(
                    id=item.document.id,
                    title=item.document.title,
                    page_count=item.document.page_count,
                )
                for item in assessment.documents
                if item.document is not None
            ],
            questions=[
                self._to_public_question(question)
                for question in sorted(
                    assessment.questions,
                    key=lambda item: item.order_index,
                )
            ],
        )

    def _to_public_question(self, question: Question) -> PublicQuestion:
        return PublicQuestion(
            id=question.id,
            type=question.type,
            text=question.text,
            points=question.points,
            order_index=question.order_index,
            source_document_id=question.source_document_id,
            source_document_title=question.source_document.title,
            source_page_number=question.source_page_number,
            source_excerpt=question.source_excerpt,
            options=[
                PublicQuestionOption(
                    id=option.id,
                    text=option.text,
                    order_index=option.order_index,
                )
                for option in sorted(
                    question.options,
                    key=lambda item: item.order_index,
                )
            ],
        )
