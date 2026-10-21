import type { QueryResultOut, SseEvent } from "../../api/types";

export type StepName = "generating" | "checking" | "running" | "repairing" | "analyzing";

export interface LiveTurn {
  question: string;
  status: "streaming" | "done" | "error";
  step?: { name: StepName; attempt?: number };
  sql?: { sql: string; interpretation: string; assumptions: string[] };
  result?: QueryResultOut;
  analysisText: string;
  analysis?: { text: string; source: "llm" | "local"; results_shared: boolean };
  clarification?: string;
  error?: { code: string; message: string };
  turnId?: number | null;
  // The highest saved seq in the conversation when this turn started (0 for a new one).
  afterSeq: number;
}

export function startTurn(question: string, afterSeq: number): LiveTurn {
  return { question, status: "streaming", analysisText: "", afterSeq };
}

export function chatStreamReducer(turn: LiveTurn, e: SseEvent): LiveTurn {
  switch (e.event) {
    case "step":
      return { ...turn, step: { name: e.data.name as StepName, attempt: e.data.attempt } };
    case "sql":
      return { ...turn, sql: e.data };
    case "result":
      return { ...turn, result: e.data };
    case "analysis_delta":
      return { ...turn, analysisText: turn.analysisText + e.data.text };
    case "analysis":
      return { ...turn, analysis: e.data, analysisText: e.data.text };
    case "clarification":
      return { ...turn, clarification: e.data.question };
    case "error":
      return { ...turn, status: "error", error: e.data };
    case "done":
      return {
        ...turn,
        status: turn.status === "error" ? "error" : "done",
        turnId: e.data.turn_id,
      };
    default:
      // An event this client does not know (a newer server, a keep-alive) changes nothing.
      return turn;
  }
}

export function stepLabel(step: { name: StepName; attempt?: number }): string {
  switch (step.name) {
    case "generating":
      return "Writing SQL";
    case "checking":
      return "Checking the query";
    case "running":
      return "Running the query";
    case "repairing":
      // The event carries the attempt that failed; the label names the one being made.
      return `Fixing the query (attempt ${(step.attempt ?? 1) + 1})`;
    case "analyzing":
      return "Analyzing results";
  }
}

const SAVED_ERRORS: Record<string, string> = {
  client_disconnected: "This answer was interrupted before it finished.",
  turn_timeout: "This question took too long to answer.",
  profile_missing_key: "The AI model has no usable API key. Re-enter it in Settings.",
  profile_not_found: "The AI model used for this question was deleted.",
  sql_rejected: "The AI wrote a query the Hub doesn't allow.",
  query_failed: "The query failed to run.",
  invalid_llm_reply: "The AI's reply couldn't be understood.",
  internal_error: "Something went wrong on the server.",
  // Same wording as backend/app/llm/errors.py, so a saved turn reads like the live error.
  llm_auth_failed: "The AI provider rejected the API key. Check this profile in Settings.",
  llm_rate_limited: "The AI provider is rate-limiting requests. Wait a moment and try again.",
  llm_unavailable: "Could not reach the AI provider, or it had an error. Try again in a moment.",
  llm_model_not_found: "The AI provider does not know this model or URL. Check the model name and base URL.",
  llm_bad_request: "The AI provider rejected the request. Check the model and settings of this profile.",
};

// A saved turn keeps only its error code, not the message the stream sent.
export function savedErrorText(code: string | null): string {
  if (code === null) return "This question could not be answered.";
  if (Object.hasOwn(SAVED_ERRORS, code)) return SAVED_ERRORS[code];
  if (code.startsWith("llm_")) return "The AI provider returned an error.";
  return `This question could not be answered (${code}).`;
}
