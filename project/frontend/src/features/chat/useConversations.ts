import { skipToken, useQuery } from "@tanstack/react-query";
import { ApiError, apiGet } from "../../api/client";
import type { ConversationDetail, ConversationOut } from "../../api/types";

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: () => apiGet<ConversationOut[]>("/api/conversations"),
  });
}

// null is the /chat draft, which has nothing to load yet.
export function useConversation(id: number | null) {
  return useQuery({
    queryKey: ["conversation", id],
    queryFn: id === null ? skipToken : () => apiGet<ConversationDetail>(`/api/conversations/${id}`),
    // A deleted conversation stays deleted; retrying only delays the message.
    retry: (failures, error) => !(error instanceof ApiError && error.status === 404) && failures < 3,
  });
}
