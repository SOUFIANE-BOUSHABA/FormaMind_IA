import { useMutation } from "@tanstack/react-query";

import { askAssistant } from "@/features/assistant/api/assistant-api";
import { type AskQuestionRequest } from "@/features/assistant/types/assistant";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function useAskAssistant() {
  const auth = useAuth();

  return useMutation({
    mutationFn: (request: AskQuestionRequest) =>
      askAssistant(auth.accessToken ?? "", request),
  });
}
