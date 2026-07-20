import { apiRequest } from "@/lib/api-client";
import { endpoints } from "@/services/endpoints";
import {
  type AskQuestionRequest,
  type AskQuestionResponse,
  type SourceCitation,
} from "@/features/assistant/types/assistant";

type ApiSourceCitation = {
  document_id: number;
  document_title: string;
  page_number: number;
  excerpt: string;
};

type ApiAskQuestionResponse = {
  answer: string;
  has_sufficient_context: boolean;
  sources: ApiSourceCitation[];
};

function mapCitation(citation: ApiSourceCitation): SourceCitation {
  return {
    documentId: citation.document_id,
    documentTitle: citation.document_title,
    pageNumber: citation.page_number,
    excerpt: citation.excerpt,
  };
}

function mapAskQuestionResponse(
  response: ApiAskQuestionResponse,
): AskQuestionResponse {
  return {
    answer: response.answer,
    hasSufficientContext: response.has_sufficient_context,
    sources: response.sources.map(mapCitation),
  };
}

export async function askAssistant(
  accessToken: string,
  request: AskQuestionRequest,
): Promise<AskQuestionResponse> {
  const response = await apiRequest<ApiAskQuestionResponse>(
    endpoints.assistant.ask,
    {
      accessToken,
      json: {
        question: request.question,
        document_ids: request.documentIds,
      },
      method: "POST",
    },
  );

  return mapAskQuestionResponse(response);
}
