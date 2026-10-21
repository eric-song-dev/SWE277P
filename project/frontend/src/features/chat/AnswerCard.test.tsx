import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiDownload } from "../../api/client";
import type { QueryResultOut, TurnOut } from "../../api/types";
import AnswerCard from "./AnswerCard";
import type { LiveTurn } from "./chatStream";

// Keep the real ApiError class; automocking would blank its constructor.
vi.mock("../../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../api/client")>()),
  apiDownload: vi.fn(),
}));

const SQL = "SELECT count(DISTINCT person_key) AS people FROM attendance_view";

const turn: TurnOut = {
  id: 4,
  seq: 1,
  question: "How many people came to the Bagel Breakfast?",
  kind: "answer",
  sql: SQL,
  interpretation: "Count distinct attendees of the Bagel Breakfast",
  assumptions: ["Bagel Breakfast means the October event"],
  clarification_question: null,
  row_count: 1,
  truncated: false,
  analysis_text: "38 people attended.",
  analysis_source: "llm",
  results_shared: true,
  llm_profile_id: 1,
  model: "scripted",
  error_code: null,
  created_at: "2026-10-21T10:00:00Z",
};

const result: QueryResultOut = { columns: ["people"], rows: [[38]], row_count: 1, truncated: false };

function renderCard(props: Parameters<typeof AnswerCard>[0]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <AnswerCard {...props} />
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

describe("AnswerCard", () => {
  beforeEach(() => vi.clearAllMocks());

  it("labels LLM analysis and keeps SQL collapsed", async () => {
    const user = renderCard({ turn, result });
    expect(screen.getByText("38 people attended.")).toBeInTheDocument();
    expect(screen.getByText("AI-generated summary. Check it against the table.")).toBeInTheDocument();
    expect(screen.queryByText(SQL)).not.toBeInTheDocument();
    const bar = screen.getByRole("button", { name: "Show the SQL query" });
    expect(bar).toHaveAttribute("aria-expanded", "false");
    await user.click(bar);
    expect(await screen.findByText(SQL)).toBeVisible();
    expect(screen.getByRole("button", { name: "Copy" })).toBeInTheDocument();
  });

  it("orders the sections", () => {
    renderCard({ turn, result });
    const caption = screen.getByText("AI-generated summary. Check it against the table.");
    const grid = screen.getByRole("grid");
    const heading = screen.getByRole("heading", { name: "How I read your question" });
    const bar = screen.getByRole("button", { name: "Show the SQL query" });
    const count = screen.getByText("1 row");
    const excel = screen.getByRole("button", { name: "Download Excel (.xlsx)" });
    const chain = [caption, grid, heading, bar, count, excel];
    for (let i = 0; i < chain.length - 1; i++) {
      expect(chain[i].compareDocumentPosition(chain[i + 1]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
  });

  it("does not label a local summary", () => {
    renderCard({ turn: { ...turn, analysis_text: "people: 38", analysis_source: "local" }, result });
    expect(screen.getByText("people: 38")).toBeInTheDocument();
    expect(screen.queryByText(/AI-generated summary/)).not.toBeInTheDocument();
  });

  it("shows the result table with each column by name", () => {
    renderCard({
      turn,
      result: {
        columns: ["name", "name", "meta"],
        rows: [["Ada Lovelace", null, { term: "Fall 2026" }]],
        row_count: 1,
        truncated: false,
      },
    });
    const grid = screen.getByRole("grid");
    expect(within(grid).getAllByRole("columnheader", { name: "name" })).toHaveLength(2);
    expect(within(grid).getByRole("columnheader", { name: "meta" })).toBeInTheDocument();
    const cells = within(grid).getAllByRole("gridcell");
    expect(cells.map((c) => c.textContent)).toEqual(["Ada Lovelace", "", '{"term":"Fall 2026"}']);
    expect(screen.getByText("1 row")).toBeInTheDocument();
  });

  it("shows the truncation notice", () => {
    renderCard({
      turn,
      result: { columns: ["name"], rows: [["Ada Lovelace"]], row_count: 1000, truncated: true },
    });
    expect(screen.getByText("Showing the first 1000 rows. Download the file to get all rows.")).toBeInTheDocument();
    expect(screen.getByText("More than 1000 rows")).toBeInTheDocument();
    expect(screen.queryByText("1000 rows")).not.toBeInTheDocument();
  });

  it("shows the interpretation and assumptions as bullets; null assumptions are none", () => {
    const { rerender } = render(
      <QueryClientProvider client={new QueryClient()}>
        <AnswerCard turn={turn} result={result} />
      </QueryClientProvider>,
    );
    expect(screen.getByText("How I read your question")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem").map((li) => li.textContent)).toEqual([
      "Count distinct attendees of the Bagel Breakfast",
      "Bagel Breakfast means the October event",
    ]);
    rerender(
      <QueryClientProvider client={new QueryClient()}>
        <AnswerCard turn={{ ...turn, assumptions: null }} result={result} />
      </QueryClientProvider>,
    );
    expect(screen.getAllByRole("listitem")).toHaveLength(1);
  });

  it("copies the SQL", async () => {
    const user = renderCard({ turn, result });
    await user.click(screen.getByRole("button", { name: "Show the SQL query" }));
    await user.click(await screen.findByRole("button", { name: "Copy" }));
    expect(await navigator.clipboard.readText()).toBe(SQL);
  });

  describe("Copy confirmation", () => {
    afterEach(() => {
      vi.useRealTimers();
      vi.restoreAllMocks();
    });

    function mockClipboard(writeText: () => Promise<void>) {
      Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    }

    it("reads Copied for about 2 s, then Copy again", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      const writeText = vi.fn().mockResolvedValue(undefined);
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      mockClipboard(writeText); // after setup(): user-event installs its own clipboard stub
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnswerCard turn={turn} result={result} />
        </QueryClientProvider>,
      );
      await user.click(screen.getByRole("button", { name: "Show the SQL query" }));
      await user.click(await screen.findByRole("button", { name: "Copy" }));
      expect(writeText).toHaveBeenCalledWith(SQL);
      expect(await screen.findByRole("button", { name: "Copied" })).toBeInTheDocument();
      act(() => {
        vi.advanceTimersByTime(2100);
      });
      expect(screen.getByRole("button", { name: "Copy" })).toBeInTheDocument();
    });

    it("reads Copy failed when the clipboard write fails", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      mockClipboard(vi.fn().mockRejectedValue(new Error("denied")));
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnswerCard turn={turn} result={result} />
        </QueryClientProvider>,
      );
      await user.click(screen.getByRole("button", { name: "Show the SQL query" }));
      await user.click(await screen.findByRole("button", { name: "Copy" }));
      expect(await screen.findByRole("button", { name: "Copy failed" })).toBeInTheDocument();
      act(() => {
        vi.advanceTimersByTime(2100);
      });
      expect(screen.getByRole("button", { name: "Copy" })).toBeInTheDocument();
    });
  });

  it("export buttons download the turn", async () => {
    vi.mocked(apiDownload).mockResolvedValue({ fileName: "hub-turn-4.xlsx", truncated: false, rowCap: 100000 });
    const user = renderCard({ turn, result });
    await user.click(screen.getByRole("button", { name: "Download Excel (.xlsx)" }));
    expect(apiDownload).toHaveBeenCalledWith("/api/chat/turns/4/export?format=xlsx");
    await user.click(screen.getByRole("button", { name: "Download CSV (.csv)" }));
    expect(apiDownload).toHaveBeenLastCalledWith("/api/chat/turns/4/export?format=csv");
    expect(screen.queryByText(/This file stops at/)).not.toBeInTheDocument();
  });

  it("says when the exported file stops at the row cap", async () => {
    vi.mocked(apiDownload).mockResolvedValueOnce({ fileName: "hub-turn-4.csv", truncated: true, rowCap: 100000 });
    const user = renderCard({ turn, result });
    await user.click(screen.getByRole("button", { name: "Download CSV (.csv)" }));
    expect(await screen.findByText("This file stops at 100,000 rows.")).toBeInTheDocument();
  });

  it("shows the error when an export fails", async () => {
    vi.mocked(apiDownload).mockRejectedValueOnce(new ApiError(404, "turn_not_found", "That question no longer exists."));
    const user = renderCard({ turn, result });
    await user.click(screen.getByRole("button", { name: "Download Excel (.xlsx)" }));
    expect(await screen.findByText("That question no longer exists.")).toBeInTheDocument();
  });

  it("persisted turn without rows offers Show results; a re-run result is labeled", async () => {
    const onShowResults = vi.fn();
    const user = renderCard({ turn, onShowResults });
    expect(screen.queryByRole("grid")).not.toBeInTheDocument();
    expect(screen.getByText("1 row")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show results" }));
    expect(onShowResults).toHaveBeenCalledTimes(1);
  });

  it("labels a re-run table", () => {
    renderCard({ turn, result, rerun: true });
    expect(screen.getByText("Re-run on current data")).toBeInTheDocument();
    expect(screen.getByRole("grid")).toBeInTheDocument();
  });

  it("shows the current step and the latest SQL while streaming, without exports", async () => {
    const live: LiveTurn = {
      question: "How many?",
      status: "streaming",
      step: { name: "repairing", attempt: 1 },
      sql: { sql: SQL, interpretation: "Count attendees", assumptions: [] },
      analysisText: "",
      afterSeq: 0,
    };
    const user = renderCard({ turn: live });
    expect(screen.getByText("Fixing the query (attempt 2)")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Download Excel (.xlsx)" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Show results" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show the SQL query" }));
    expect(await screen.findByText(SQL)).toBeInTheDocument();
  });

  it("labels streamed analysis and offers exports once the live turn has an id", () => {
    const live: LiveTurn = {
      question: "How many?",
      status: "done",
      sql: { sql: SQL, interpretation: "Count attendees", assumptions: [] },
      result,
      analysisText: "38 people attended.",
      afterSeq: 0,
      analysis: { text: "38 people attended.", source: "llm", results_shared: true },
      turnId: 4,
    };
    renderCard({ turn: live, result });
    expect(screen.queryByText("Fixing the query (attempt 2)")).not.toBeInTheDocument();
    expect(screen.getByText("AI-generated summary. Check it against the table.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download Excel (.xlsx)" })).toBeInTheDocument();
  });
});
