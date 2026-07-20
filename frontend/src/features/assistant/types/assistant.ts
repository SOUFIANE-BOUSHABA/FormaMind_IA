export type SourceCitation = {
  documentId: number;
  documentTitle: string;
  pageNumber: number;
  excerpt: string;
};

export type AskQuestionRequest = {
  question: string;
  documentIds: number[];
};

export type AskQuestionResponse = {
  answer: string;
  hasSufficientContext: boolean;
  sources: SourceCitation[];
};

export type AssistantMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
  sources?: SourceCitation[];
};
