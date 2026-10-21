import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { TurnOut } from "../../api/types";
import type { LiveTurn } from "./chatStream";
import Thread from "./Thread";

function saved(seq: number, question: string, disconnected = false): TurnOut {
  return {
    id: seq * 10,
    seq,
    question,
    kind: disconnected ? "error" : "clarification",
    sql: null,
    interpretation: null,
    assumptions: null,
    clarification_question: disconnected ? null : "Which one?",
    row_count: null,
    truncated: false,
    analysis_text: null,
    analysis_source: null,
    results_shared: false,
    llm_profile_id: null,
    model: null,
    error_code: disconnected ? "client_disconnected" : null,
    created_at: "2026-10-21T00:00:00Z",
  };
}

function lost(overrides: Partial<LiveTurn> = {}): LiveTurn {
  return {
    question: "Q3",
    status: "error",
    analysisText: "",
    error: { code: "stream_interrupted", message: "Connection lost. Retry." },
    afterSeq: 2,
    ...overrides,
  };
}

function renderThread(turns: TurnOut[], live: LiveTurn) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <Thread turns={turns} live={live} resultsByTurnId={{}} busy={false} onRetryLive={() => {}} onResend={() => {}} />
    </QueryClientProvider>,
  );
}

const INTERRUPTED = "This answer was interrupted before it finished.";

describe("Thread, a dropped stream", () => {
  it("absorbs the saved client_disconnected copy into the live card", () => {
    renderThread([saved(1, "Q1"), saved(2, "Q2"), saved(3, "Q3", true)], lost());
    expect(screen.getAllByText("Q3")).toHaveLength(1);
    expect(screen.getAllByText("Connection lost. Retry.")).toHaveLength(1);
    expect(screen.queryByText(INTERRUPTED)).not.toBeInTheDocument();
  });

  it("does not adopt a saved turn with another question", () => {
    renderThread([saved(1, "Q1"), saved(2, "Q2"), saved(3, "Other", true)], lost());
    expect(screen.getByText("Connection lost. Retry.")).toBeInTheDocument();
    expect(screen.getByText(INTERRUPTED)).toBeInTheDocument();
  });

  it("does not adopt an earlier identical question", () => {
    renderThread([saved(1, "Q1"), saved(2, "Q2"), saved(3, "Q3", true)], lost({ afterSeq: 3 }));
    expect(screen.getAllByText("Q3")).toHaveLength(2);
    expect(screen.getByText(INTERRUPTED)).toBeInTheDocument();
    expect(screen.getByText("Connection lost. Retry.")).toBeInTheDocument();
  });

  it("appends a live error whose done arrived without a recorded turn", () => {
    renderThread([saved(1, "Q1"), saved(2, "Q2"), saved(3, "Q3", true)], lost({ turnId: null }));
    expect(screen.getAllByText("Q3")).toHaveLength(2);
    expect(screen.getByText(INTERRUPTED)).toBeInTheDocument();
  });
});
