import { describe, expect, it } from "vitest";
import type { QueryResultOut, SseEvent } from "../../api/types";
import { chatStreamReducer, startTurn, stepLabel } from "./chatStream";

const SQL = { sql: "SELECT 1", interpretation: "one", assumptions: ["a"] };
const RESULT: QueryResultOut = { columns: ["n"], rows: [[38]], row_count: 1, truncated: false };

function ev<E extends SseEvent["event"]>(
  event: E,
  data: Extract<SseEvent, { event: E }>["data"],
): SseEvent {
  return { event, data } as SseEvent;
}

describe("chatStreamReducer", () => {
  it("accumulates a full answer", () => {
    const t = [
      ev("step", { name: "generating", attempt: 1 }),
      ev("sql", SQL),
      ev("step", { name: "checking", attempt: 1 }),
      ev("step", { name: "running", attempt: 1 }),
      ev("result", RESULT),
      ev("step", { name: "analyzing", attempt: 1 }),
      ev("analysis_delta", { text: "38 " }),
      ev("analysis_delta", { text: "people" }),
      ev("analysis", { text: "38 people", source: "llm", results_shared: true }),
      ev("done", { turn_id: 4 }),
    ].reduce(chatStreamReducer, startTurn("q"));
    expect(t).toMatchObject({
      question: "q",
      status: "done",
      turnId: 4,
      analysisText: "38 people",
      result: RESULT,
      sql: SQL,
      analysis: { text: "38 people", source: "llm", results_shared: true },
    });
  });

  it("starts streaming with empty analysis", () => {
    expect(startTurn("q")).toEqual({ question: "q", status: "streaming", analysisText: "" });
  });

  it("keeps the latest sql and replaces the step", () => {
    const sql2 = { ...SQL, sql: "SELECT 2" };
    const t = [
      ev("step", { name: "generating", attempt: 1 }),
      ev("sql", SQL),
      ev("step", { name: "repairing", attempt: 2 }),
      ev("sql", sql2),
    ].reduce(chatStreamReducer, startTurn("q"));
    expect(t.sql).toEqual(sql2);
    expect(t.step).toEqual({ name: "repairing", attempt: 2 });
  });

  it("local analysis replaces streamed deltas", () => {
    const t = [
      ev("analysis_delta", { text: "partial" }),
      ev("analysis", { text: "local text", source: "local", results_shared: false }),
    ].reduce(chatStreamReducer, startTurn("q"));
    expect(t.analysisText).toBe("local text");
    expect(t.analysis?.source).toBe("local");
  });

  it("clarification", () => {
    const t = [
      ev("clarification", { question: "Academic or calendar year?" }),
      ev("done", { turn_id: 2 }),
    ].reduce(chatStreamReducer, startTurn("q"));
    expect(t).toMatchObject({
      clarification: "Academic or calendar year?",
      status: "done",
      turnId: 2,
    });
  });

  it("error event stays an error after done", () => {
    const t = [
      ev("error", { code: "llm_auth_failed", message: "Bad key" }),
      ev("done", { turn_id: 3 }),
    ].reduce(chatStreamReducer, startTurn("q"));
    expect(t).toMatchObject({
      status: "error",
      error: { code: "llm_auth_failed", message: "Bad key" },
      turnId: 3,
    });
  });

  it("allows a null turn id", () => {
    const t = chatStreamReducer(startTurn("q"), ev("done", { turn_id: null }));
    expect(t).toMatchObject({ status: "done", turnId: null });
  });

  it("does not mutate the input turn", () => {
    const before = startTurn("q");
    const frozen = Object.freeze({ ...before });
    chatStreamReducer(frozen, ev("analysis_delta", { text: "x" }));
    expect(frozen).toEqual(before);
  });
});

describe("stepLabel", () => {
  it("labels", () => {
    expect(stepLabel({ name: "generating" })).toBe("Writing SQL");
    expect(stepLabel({ name: "checking" })).toBe("Checking the query");
    expect(stepLabel({ name: "running" })).toBe("Running the query");
    expect(stepLabel({ name: "repairing", attempt: 2 })).toBe("Fixing the query (attempt 2)");
    expect(stepLabel({ name: "analyzing" })).toBe("Analyzing results");
  });
});
