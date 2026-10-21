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
}

export function startTurn(question: string): LiveTurn {
  return { question, status: "streaming", analysisText: "" };
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
      return `Fixing the query (attempt ${step.attempt})`;
    case "analyzing":
      return "Analyzing results";
  }
}
