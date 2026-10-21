import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiSend } from "../../api/client";
import { streamSse } from "../../api/sse";
import type { ConversationOut, QueryResultOut } from "../../api/types";
import { chatStreamReducer, startTurn, type LiveTurn } from "./chatStream";

interface Request {
  question: string;
  llmProfileId: number | null;
  shareResults: boolean;
}

function toTurnError(err: unknown): { code: string; message: string } {
  if (err instanceof ApiError) {
    if (err.code === "stream_interrupted" || err.code === "network_error") {
      return { code: err.code, message: "Connection lost. Retry." };
    }
    return { code: err.code, message: err.message };
  }
  return { code: "unknown_error", message: "Something went wrong. Retry." };
}

export function useChatStream(
  conversationId: number | null,
  onConversationCreated?: (id: number) => void,
) {
  const queryClient = useQueryClient();
  const [live, setLive] = useState<LiveTurn | null>(null);
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
      let turn = startTurn(request.question);
      setLive(turn);

      try {
        let id = conversationId ?? createdIdRef.current;
        if (id === null) {
          const created = await apiSend<ConversationOut>("POST", "/api/conversations");
          if (controller.signal.aborted) return;
          id = created.id;
          createdIdRef.current = id;
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
        turn = { ...turn, status: "error", error: toTurnError(err) };
        setLive(turn);
      } finally {
        if (controllerRef.current === controller) {
          streamingRef.current = false;
        }
      }
    },
    [conversationId, queryClient],
  );

  const send = useCallback(
    (question: string, llmProfileId: number | null, shareResults: boolean) => {
      if (streamingRef.current) return;
      void run({ question, llmProfileId, shareResults });
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
