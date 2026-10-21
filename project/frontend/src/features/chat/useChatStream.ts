import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiSend } from "../../api/client";
import { streamSse } from "../../api/sse";
import type { ConversationDetail, ConversationOut, QueryResultOut } from "../../api/types";
import { chatStreamReducer, startTurn, type LiveTurn } from "./chatStream";

interface Request {
  question: string;
  llmProfileId: number | null;
  shareResults: boolean;
}

const LOST_CONNECTION = new Set(["stream_interrupted", "network_error", "server_unavailable"]);

function toTurnError(err: unknown): { code: string; message: string } {
  if (err instanceof ApiError) {
    if (LOST_CONNECTION.has(err.code)) {
      return { code: err.code, message: "Connection lost. Retry." };
    }
    return { code: err.code, message: err.message };
  }
  // Not an error the server sent: a bug in this client. Keep the evidence for the console.
  console.error("Chat stream failed with an unexpected error", err);
  return { code: "unknown_error", message: "Something went wrong. Retry." };
}

export function useChatStream(
  conversationId: number | null,
  onConversationCreated?: (id: number) => void,
) {
  const queryClient = useQueryClient();
  const [liveTurn, setLive] = useState<LiveTurn | null>(null);
  // The conversation the live turn belongs to (null: the /chat draft, which `created` then names), so a
  // turn is not shown in another conversation during the render before the reset effect clears it.
  const [owner, setOwner] = useState<{ id: number | null; created: number | null }>({ id: null, created: null });
  const live =
    liveTurn !== null && (owner.id === conversationId || (owner.id === null && owner.created === conversationId))
      ? liveTurn
      : null;
  const [resultsByTurnId, setResultsByTurnId] = useState<Record<number, QueryResultOut>>({});

  const controllerRef = useRef<AbortController | null>(null);
  const streamingRef = useRef(false);
  const lastQuestionRef = useRef<string | null>(null);
  // The conversation this hook created itself, so the null -> id prop change that follows
  // is not mistaken for navigating away.
  const createdIdRef = useRef<number | null>(null);
  const previousIdRef = useRef(conversationId);
  const onCreatedRef = useRef(onConversationCreated);
  useEffect(() => {
    onCreatedRef.current = onConversationCreated;
  }, [onConversationCreated]);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    streamingRef.current = false;
  }, []);

  useEffect(() => {
    const previous = previousIdRef.current;
    previousIdRef.current = conversationId;
    if (previous === conversationId) return;
    if (previous === null && conversationId === createdIdRef.current) return;
    cancel();
    createdIdRef.current = null;
    lastQuestionRef.current = null;
    setLive(null);
    setResultsByTurnId({});
  }, [conversationId, cancel]);

  useEffect(() => cancel, [cancel]);

  const run = useCallback(
    async (request: Request) => {
      const controller = new AbortController();
      controllerRef.current = controller;
      streamingRef.current = true;
      lastQuestionRef.current = request.question;
      let id = conversationId ?? createdIdRef.current;
      const cached = id === null ? undefined : queryClient.getQueryData<ConversationDetail>(["conversation", id]);
      const afterSeq = cached?.turns.reduce((max, t) => Math.max(max, t.seq), 0) ?? 0;
      let turn = startTurn(request.question, afterSeq);
      setLive(turn);
      setOwner({ id: conversationId, created: null });

      try {
        if (id === null) {
          const created = await apiSend<ConversationOut>("POST", "/api/conversations");
          if (controller.signal.aborted) return;
          id = created.id;
          createdIdRef.current = id;
          setOwner({ id: null, created: id });
          onCreatedRef.current?.(id);
        }
        const targetId = id;
        await streamSse(
          `/api/conversations/${targetId}/messages`,
          {
            question: request.question,
            llm_profile_id: request.llmProfileId,
            share_results: request.shareResults,
          },
          (e) => {
            turn = chatStreamReducer(turn, e);
            setLive(turn);
            if (e.event === "done") {
              if (turn.result && typeof e.data.turn_id === "number") {
                const stored = { [e.data.turn_id]: turn.result };
                setResultsByTurnId((prev) => ({ ...prev, ...stored }));
              }
              void queryClient.invalidateQueries({ queryKey: ["conversation", targetId] });
              void queryClient.invalidateQueries({ queryKey: ["conversations"] });
            }
          },
          controller.signal,
        );
      } catch (err) {
        if (controller.signal.aborted) return;
        const error = toTurnError(err);
        turn = { ...turn, status: "error", error };
        setLive(turn);
        if (LOST_CONNECTION.has(error.code) && id !== null) {
          // The backend saved the dropped turn as client_disconnected; fetch it so the thread can absorb it.
          void queryClient.invalidateQueries({ queryKey: ["conversation", id] });
          void queryClient.invalidateQueries({ queryKey: ["conversations"] });
        }
      } finally {
        if (controllerRef.current === controller) {
          streamingRef.current = false;
        }
      }
    },
    [conversationId, queryClient],
  );

  const send = useCallback(
    // false when the question was not taken (a stream is still open), so the caller keeps it.
    (question: string, llmProfileId: number | null, shareResults: boolean): boolean => {
      if (streamingRef.current) return false;
      void run({ question, llmProfileId, shareResults });
      return true;
    },
    [run],
  );

  // Resends the last question with the settings chosen now, not the ones that failed.
  const retry = useCallback(
    (llmProfileId: number | null, shareResults: boolean) => {
      const question = lastQuestionRef.current;
      if (streamingRef.current || question === null) return;
      void run({ question, llmProfileId, shareResults });
    },
    [run],
  );

  const abort = useCallback(() => {
    cancel();
    setLive(null);
  }, [cancel]);

  return { live, resultsByTurnId, send, retry, abort };
}
