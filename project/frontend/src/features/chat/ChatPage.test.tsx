import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiGet, apiSend } from "../../api/client";
import { streamSse } from "../../api/sse";
import type {
  ConversationDetail,
  ConversationOut,
  LlmProfileOut,
  QueryResultOut,
  SseEvent,
  TurnOut,
} from "../../api/types";
import ChatPage from "./ChatPage";
import Thread from "./Thread";

// Keep the real ApiError class; automocking would blank its constructor.
vi.mock("../../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../api/client")>()),
  apiGet: vi.fn(),
  apiSend: vi.fn(),
  apiDownload: vi.fn(),
}));
vi.mock("../../api/sse", () => ({ streamSse: vi.fn() }));

const SHARE = "Let AI see the results";
const ON_HELP = "On: the AI reads the results to summarize them. PII (such as emails and names) may be shared with the AI.";
const OFF_HELP = "Off: the AI sees only your question. You get the results without an AI summary.";

const lab: LlmProfileOut = {
  id: 1,
  name: "Lab model",
  preset: "fake",
  base_url: null,
  model: "scripted",
  api_key_hint: null,
  has_api_key: false,
  share_results_with_llm: true,
  json_mode: null,
  is_default: true,
  last_tested_at: null,
  last_test_ok: null,
};
const campus: LlmProfileOut = { ...lab, id: 2, name: "Campus model", is_default: false };
const closed: LlmProfileOut = { ...lab, id: 3, name: "Private model", share_results_with_llm: false, is_default: false };

const stamp = "2026-10-21T10:00:00Z";
const conversations: ConversationOut[] = [
  { id: 1, title: "Bagel Breakfast attendance", created_at: stamp, updated_at: stamp },
  { id: 2, title: null, created_at: stamp, updated_at: stamp },
];

function savedTurn(overrides: Partial<TurnOut>): TurnOut {
  return {
    id: 4,
    seq: 1,
    question: "How many people came to the Bagel Breakfast?",
    kind: "answer",
    sql: "SELECT count(*) AS people FROM attendance_view",
    interpretation: "Count attendees",
    assumptions: null,
    clarification_question: null,
    row_count: 1,
    truncated: false,
    analysis_text: "people: 38",
    analysis_source: "local",
    results_shared: false,
    llm_profile_id: 1,
    model: "scripted",
    error_code: null,
    created_at: stamp,
    ...overrides,
  };
}

const RESULT: QueryResultOut = { columns: ["people"], rows: [[38]], row_count: 1, truncated: false };
const LIVE_SQL = "SELECT count(DISTINCT person_key) AS people FROM attendance_view";
const FAILED_SQL = "SELECT people FROM attendance_view WHERE term = 'Fall 2026'";

let profiles: LlmProfileOut[];
let details: Record<number, ConversationDetail | ApiError>;

function detail(id: number, turns: TurnOut[] = []): ConversationDetail {
  return { id, title: null, created_at: stamp, updated_at: stamp, turns };
}

function routeGet(path: string): unknown {
  if (path === "/api/llm-profiles") return profiles;
  if (path === "/api/conversations") return conversations;
  if (path === "/api/chat/turns/4/rerun") return RESULT;
  const match = /^\/api\/conversations\/(\d+)$/.exec(path);
  const found = match ? details[Number(match[1])] : undefined;
  if (found instanceof ApiError) throw found;
  if (found) return found;
  throw new Error(`unexpected GET ${path}`);
}

// A stream the test drives by hand.
function pendingStream() {
  let emit: (e: SseEvent) => void = () => {};
  let finish: (err?: unknown) => void = () => {};
  let signal: AbortSignal | undefined;
  vi.mocked(streamSse).mockImplementationOnce((_path, _body, onEvent, s) => {
    emit = onEvent;
    signal = s;
    return new Promise<void>((resolve, reject) => {
      finish = (err) => (err ? reject(err) : resolve());
    });
  });
  return {
    emit: (e: SseEvent) => act(() => emit(e)),
    finish: (err?: unknown) => act(async () => finish(err)),
    get signal() {
      return signal;
    },
  };
}

function bodies() {
  return vi.mocked(streamSse).mock.calls.map((call) => call[1]);
}

function renderPage(path: string) {
  // retryDelay 0: useConversation retries other errors itself, and the tests should not wait.
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, retryDelay: 0 } } });
  const router = createMemoryRouter(
    [
      { path: "/chat/:conversationId?", element: <ChatPage /> },
      { path: "/settings", element: <p>Settings page</p> },
    ],
    { initialEntries: [path] },
  );
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router, client, user: userEvent.setup() };
}

async function ask(user: ReturnType<typeof userEvent.setup>, question: string) {
  await user.type(await screen.findByRole("textbox"), `${question}{Enter}`);
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  profiles = [lab, campus, closed];
  details = { 1: detail(1), 2: detail(2), 7: detail(7) };
  vi.mocked(apiGet).mockImplementation(async (path) => routeGet(path));
});

describe("ChatPage", () => {
  it("sends once while streaming", async () => {
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    const box = await screen.findByRole("textbox");
    await user.type(box, "How many came?");
    await user.keyboard("{Enter}{Enter}");
    expect(streamSse).toHaveBeenCalledTimes(1);
    expect(bodies()[0]).toEqual({ question: "How many came?", llm_profile_id: 1, share_results: true });
    expect(screen.getByRole("textbox")).toBeDisabled();
    expect(screen.getByRole("textbox")).toHaveValue("");
    await s.emit({ event: "done", data: { turn_id: null } });
    await s.finish();
    expect(screen.getByRole("textbox")).toBeEnabled();
  });

  it("keeps a question typed between done and the end of the body", async () => {
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    await ask(user, "How many came?");
    await s.emit({ event: "done", data: { turn_id: null } });
    const box = screen.getByRole("textbox");
    expect(box).toBeEnabled(); // the turn is done, but the body has not ended
    await user.type(box, "And last month?{Enter}");
    expect(streamSse).toHaveBeenCalledTimes(1);
    expect(box).toHaveValue("And last month?");
    await s.finish();
    const second = pendingStream();
    await user.keyboard("{Enter}");
    expect(bodies()[1]).toMatchObject({ question: "And last month?" });
    expect(box).toHaveValue("");
    await second.finish();
  });

  it("aborts the stream when switching conversations", async () => {
    const s = pendingStream();
    const { router, user } = renderPage("/chat/1");
    await ask(user, "How many came?");
    expect(screen.getByText("How many came?")).toBeInTheDocument();
    await act(() => router.navigate("/chat/2"));
    expect(s.signal?.aborted).toBe(true);
    await s.finish(new DOMException("aborted", "AbortError"));
    expect(screen.queryByText("How many came?")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeEnabled();
  });

  it("keeps streaming when the first send on /chat creates the conversation", async () => {
    vi.mocked(apiSend).mockResolvedValueOnce({ id: 7, title: null, created_at: stamp, updated_at: stamp });
    const s = pendingStream();
    const { router, user } = renderPage("/chat");
    await user.click(await screen.findByLabelText(SHARE));
    await ask(user, "How many came?");
    await waitFor(() => expect(router.state.location.pathname).toBe("/chat/7"));
    expect(router.state.historyAction).toBe("REPLACE");
    expect(apiSend).toHaveBeenCalledWith("POST", "/api/conversations");
    expect(vi.mocked(streamSse).mock.calls[0][0]).toBe("/api/conversations/7/messages");
    expect(s.signal?.aborted).toBe(false);
    await s.emit({ event: "step", data: { name: "running", attempt: 1 } });
    expect(screen.getByText("Running the query")).toBeInTheDocument();
    await s.emit({ event: "result", data: RESULT });
    expect(within(screen.getByRole("grid")).getByText("38")).toBeInTheDocument();
    // Same conversation, so the user's switch choice stays.
    expect(screen.getByLabelText(SHARE)).not.toBeChecked();
    expect(screen.getAllByRole("textbox")).toHaveLength(1);
    await s.emit({ event: "done", data: { turn_id: 9 } });
    await s.finish();
  });

  it("renders the live turn in place of its saved copy", async () => {
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    await ask(user, "How many came?");
    await s.emit({ event: "result", data: RESULT });
    await s.emit({ event: "analysis", data: { text: "people: 38", source: "local", results_shared: false } });
    // The refetch after done brings an earlier turn (asked elsewhere) and this turn's saved copy.
    details[1] = detail(1, [
      savedTurn({ id: 8, seq: 1, question: "An earlier question" }),
      savedTurn({ id: 9, seq: 2, question: "How many came?" }),
    ]);
    await s.emit({ event: "done", data: { turn_id: 9 } });
    await s.finish();
    expect(await screen.findByText("An earlier question")).toBeInTheDocument();
    expect(screen.getAllByText("How many came?")).toHaveLength(1);
    expect(screen.getAllByText("people: 38")).toHaveLength(2); // the earlier turn's and this one's
    expect(screen.getAllByRole("grid")).toHaveLength(1);
    expect(screen.getAllByRole("button", { name: "Show results" })).toHaveLength(1); // the earlier turn only
  });

  it("keeps the live card's state when its saved copy arrives", async () => {
    // An earlier turn, so the live turn is seq 2 both before and after the refetch.
    details[1] = detail(1, [savedTurn({ id: 8, seq: 1, question: "An earlier question" })]);
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    await screen.findByText("An earlier question");
    await ask(user, "How many came?");
    await s.emit({ event: "sql", data: { sql: LIVE_SQL, interpretation: "Count attendees", assumptions: [] } });
    await user.click(screen.getAllByRole("button", { name: "Show the SQL query" })[1]);
    expect(await screen.findByText(LIVE_SQL)).toBeVisible();
    await s.emit({ event: "result", data: RESULT });
    // The earlier turn's text changes only so the test can see that the refetch has rendered.
    details[1] = detail(1, [
      savedTurn({ id: 8, seq: 1, question: "An earlier question", analysis_text: "Refetched" }),
      savedTurn({ id: 9, seq: 2, question: "How many came?" }),
    ]);
    await s.emit({ event: "done", data: { turn_id: 9 } });
    await s.finish();
    expect(await screen.findByText("Refetched")).toBeInTheDocument();
    expect(screen.getByText(LIVE_SQL)).toBeVisible(); // the accordion is still open: no remount
  });

  it("shows the SQL of a saved failed turn", async () => {
    details[1] = detail(1, [
      savedTurn({ id: 6, kind: "error", sql: FAILED_SQL, row_count: null, error_code: "query_failed", analysis_text: null }),
    ]);
    const { user } = renderPage("/chat/1");
    expect(await screen.findByText("The query failed to run.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show the SQL query" }));
    expect(await screen.findByText(FAILED_SQL)).toBeVisible();
  });

  it("keeps showing the SQL when a live turn fails after it", async () => {
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    await ask(user, "How many came?");
    await s.emit({ event: "sql", data: { sql: FAILED_SQL, interpretation: "Count attendees", assumptions: [] } });
    await s.emit({ event: "error", data: { code: "query_failed", message: "The query failed to run." } });
    await s.emit({ event: "done", data: { turn_id: null } });
    await s.finish();
    expect(screen.getByText("The query failed to run.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show the SQL query" }));
    expect(await screen.findByText(FAILED_SQL)).toBeVisible();
  });

  it("keeps the alert, Retry and the SQL bar on failed turns, and disables both Retry buttons while streaming", async () => {
    details[1] = detail(1, [
      savedTurn({ id: 6, kind: "error", sql: FAILED_SQL, row_count: null, error_code: "query_failed", analysis_text: null }),
    ]);
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    expect(await screen.findByText("The query failed to run.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Show the SQL query" })).toBeInTheDocument();
    await ask(user, "And by school?");
    // The saved failed turn stays on screen while the new question streams.
    expect(screen.getByText("The query failed to run.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Show the SQL query" })).toBeInTheDocument();
    await s.emit({ event: "done", data: { turn_id: null } });
    await s.finish();
  });

  it("shows the alert, a disabled Retry and the SQL bar on a live failed turn while another streams", () => {
    const live = {
      question: "How many came?",
      status: "error" as const,
      sql: { sql: FAILED_SQL, interpretation: "Count attendees", assumptions: [] },
      analysisText: "",
      error: { code: "query_failed", message: "The query failed to run." },
    };
    const client = new QueryClient();
    const { rerender } = render(
      <QueryClientProvider client={client}>
        <Thread turns={[]} live={live} resultsByTurnId={{}} busy={false} onRetryLive={() => {}} onResend={() => {}} />
      </QueryClientProvider>,
    );
    expect(screen.getByText("The query failed to run.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Show the SQL query" })).toHaveAttribute("aria-expanded", "false");
    rerender(
      <QueryClientProvider client={client}>
        <Thread turns={[]} live={live} resultsByTurnId={{}} busy={true} onRetryLive={() => {}} onResend={() => {}} />
      </QueryClientProvider>,
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeDisabled();
  });

  it("shows saved turns: answers re-run on demand, clarifications, and errors with Retry", async () => {
    details[1] = detail(1, [
      savedTurn({ id: 6, seq: 3, kind: "error", question: "And by school?", sql: null, row_count: null, error_code: "turn_timeout", analysis_text: null }),
      savedTurn({ id: 4, seq: 1 }),
      savedTurn({ id: 5, seq: 2, kind: "clarification", question: "This year?", sql: null, row_count: null, clarification_question: "Do you mean the 2026-27 academic year?", analysis_text: null }),
    ]);
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    const questions = await screen.findAllByText(/Bagel Breakfast\?|This year\?|And by school\?/);
    expect(questions.map((q) => q.textContent)).toEqual([
      "How many people came to the Bagel Breakfast?",
      "This year?",
      "And by school?",
    ]);
    expect(screen.getByText("Do you mean the 2026-27 academic year?")).toBeInTheDocument();
    expect(screen.getByText("This question took too long to answer.")).toBeInTheDocument();

    expect(screen.queryByRole("grid")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show results" }));
    expect(apiGet).toHaveBeenCalledWith("/api/chat/turns/4/rerun");
    expect(await screen.findByText("Re-run on current data")).toBeInTheDocument();
    expect(within(screen.getByRole("grid")).getByText("38")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(bodies()).toEqual([{ question: "And by school?", llm_profile_id: 1, share_results: true }]);
    await s.emit({ event: "done", data: { turn_id: null } });
    await s.finish();
  });

  it("does not carry a re-run result into another conversation", async () => {
    details[1] = detail(1, [savedTurn({ id: 4, seq: 1 })]);
    details[2] = detail(2, [savedTurn({ id: 12, seq: 1, question: "Who came to the Career Panel?" })]);
    // Visit 2 first so it is cached and renders at once when we come back.
    const { router, user } = renderPage("/chat/2");
    expect(await screen.findByText("Who came to the Career Panel?")).toBeInTheDocument();
    await act(() => router.navigate("/chat/1"));
    await user.click(await screen.findByRole("button", { name: "Show results" }));
    expect(await screen.findByRole("grid")).toBeInTheDocument();
    await act(() => router.navigate("/chat/2"));
    expect(await screen.findByText("Who came to the Career Panel?")).toBeInTheDocument();
    expect(screen.queryByRole("grid")).not.toBeInTheDocument();
    expect(screen.queryByText("Re-run on current data")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Show results" })).toBeInTheDocument();
  });

  it("disables Show results with a pending label while the re-run is in flight", async () => {
    details[1] = detail(1, [savedTurn({ id: 4, seq: 1 })]);
    let resolve: (v: QueryResultOut) => void = () => {};
    vi.mocked(apiGet).mockImplementation(async (path) =>
      path === "/api/chat/turns/4/rerun" ? new Promise<QueryResultOut>((r) => (resolve = r)) : routeGet(path),
    );
    const { user } = renderPage("/chat/1");
    await user.click(await screen.findByRole("button", { name: "Show results" }));
    expect(screen.getByRole("button", { name: "Loading results…" })).toBeDisabled();
    await act(async () => resolve(RESULT));
    expect(await screen.findByRole("grid")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Loading results…" })).not.toBeInTheDocument();
  });

  it("shows the error when a re-run fails", async () => {
    details[1] = detail(1, [savedTurn({ id: 8 })]);
    vi.mocked(apiGet).mockImplementation(async (path) => {
      if (path === "/api/chat/turns/8/rerun") {
        throw new ApiError(422, "query_failed", "The saved query no longer runs.");
      }
      return routeGet(path);
    });
    const { user } = renderPage("/chat/1");
    await user.click(await screen.findByRole("button", { name: "Show results" }));
    expect(await screen.findByText("The saved query no longer runs.")).toBeInTheDocument();
  });

  it("shows a lost connection with Retry, which resends the question with the current model and switch", async () => {
    const first = pendingStream();
    const { user } = renderPage("/chat/1");
    await ask(user, "How many came?");
    await first.finish(new ApiError(0, "stream_interrupted", "Connection lost."));
    expect(screen.getByText("Connection lost. Retry.")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeEnabled();
    // After the failure: another model, and the results kept on this computer.
    await user.click(screen.getByRole("combobox", { name: "AI model" }));
    await user.click(await screen.findByRole("option", { name: "Campus model" }));
    await user.click(screen.getByLabelText(SHARE));
    const second = pendingStream();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(bodies()).toEqual([
      { question: "How many came?", llm_profile_id: 1, share_results: true },
      { question: "How many came?", llm_profile_id: 2, share_results: false },
    ]);
    await second.emit({ event: "done", data: { turn_id: null } });
    await second.finish();
  });

  it("share switch starts at the profile value and is sent with each question", async () => {
    const { user } = renderPage("/chat/1");
    const toggle = await screen.findByLabelText(SHARE);
    expect(toggle).toBeChecked();
    expect(screen.getByText(ON_HELP)).toBeInTheDocument();
    expect(toggle).toHaveAccessibleDescription(ON_HELP);
    expect(screen.getAllByLabelText(SHARE)).toHaveLength(1);
    await user.click(toggle);
    expect(toggle).not.toBeChecked();
    expect(screen.getByText(OFF_HELP)).toBeInTheDocument();
    expect(screen.queryByText(ON_HELP)).not.toBeInTheDocument();

    const first = pendingStream();
    await ask(user, "First question");
    await first.emit({ event: "done", data: { turn_id: 10 } });
    await first.finish();
    const second = pendingStream();
    await ask(user, "Second question");
    await second.emit({ event: "done", data: { turn_id: 11 } });
    await second.finish();
    expect(bodies().map((b) => (b as { share_results: boolean }).share_results)).toEqual([false, false]);
    expect(screen.getByLabelText(SHARE)).not.toBeChecked();
  });

  it("share switch is disabled when the profile doesn't allow sharing", async () => {
    localStorage.setItem("hub.chat.profileId", "3");
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    const toggle = await screen.findByLabelText(SHARE);
    expect(toggle).not.toBeChecked();
    expect(toggle).toBeDisabled();
    await user.hover(screen.getByText(SHARE));
    expect(await screen.findByRole("tooltip")).toHaveTextContent(
      "This AI model isn't allowed to receive results. Change it in Settings.",
    );
    await ask(user, "How many came?");
    expect(bodies()[0]).toEqual({ question: "How many came?", llm_profile_id: 3, share_results: false });
    await s.emit({ event: "done", data: { turn_id: null } });
    await s.finish();
  });

  it("tabs from the question to the switch to Send", async () => {
    const { user } = renderPage("/chat/1");
    await user.type(await screen.findByRole("textbox"), "How many came?");
    await user.tab();
    expect(screen.getByRole("switch", { name: SHARE })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("button", { name: "Send" })).toHaveFocus();
  });

  it("switching to a profile that disallows sharing turns the switch off with the Off text", async () => {
    const { user } = renderPage("/chat/1");
    expect(await screen.findByLabelText(SHARE)).toBeChecked();
    await user.click(screen.getByRole("combobox", { name: "AI model" }));
    await user.click(await screen.findByRole("option", { name: "Private model" }));
    const toggle = screen.getByLabelText(SHARE);
    expect(toggle).toBeDisabled();
    expect(toggle).not.toBeChecked();
    expect(screen.getByText(OFF_HELP)).toBeInTheDocument();
    await user.hover(screen.getByText(SHARE));
    expect(await screen.findByRole("tooltip")).toHaveTextContent(
      "This AI model isn't allowed to receive results. Change it in Settings.",
    );
  });

  it("share switch resets on profile or conversation change", async () => {
    const { router, user } = renderPage("/chat/1");
    await user.click(await screen.findByLabelText(SHARE));
    expect(screen.getByLabelText(SHARE)).not.toBeChecked();

    await user.click(screen.getByRole("combobox", { name: "AI model" }));
    await user.click(await screen.findByRole("option", { name: "Campus model" }));
    expect(screen.getByLabelText(SHARE)).toBeChecked();

    await user.click(screen.getByLabelText(SHARE));
    await act(() => router.navigate("/chat/2"));
    expect(screen.getByLabelText(SHARE)).toBeChecked();

    // Back to the first conversation: still the profile's value, not the old choice.
    await user.click(screen.getByLabelText(SHARE));
    await act(() => router.navigate("/chat/1"));
    expect(screen.getByLabelText(SHARE)).toBeChecked();
  });

  it("preselects the remembered profile and remembers a new choice", async () => {
    localStorage.setItem("hub.chat.profileId", "2");
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    expect(await screen.findByRole("combobox", { name: "AI model" })).toHaveTextContent("Campus model");
    await user.click(screen.getByRole("combobox", { name: "AI model" }));
    await user.click(await screen.findByRole("option", { name: "Lab model" }));
    expect(localStorage.getItem("hub.chat.profileId")).toBe("1");
    await ask(user, "How many came?");
    expect(bodies()[0]).toMatchObject({ llm_profile_id: 1 });
    await s.emit({ event: "done", data: { turn_id: null } });
    await s.finish();
  });

  it("falls back to the default profile when the remembered one is gone or storage fails", async () => {
    localStorage.setItem("hub.chat.profileId", "99");
    renderPage("/chat/1");
    expect(await screen.findByRole("combobox", { name: "AI model" })).toHaveTextContent("Lab model");
  });

  it("uses the default profile when localStorage throws", async () => {
    const getItem = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    renderPage("/chat/1");
    expect(await screen.findByRole("combobox", { name: "AI model" })).toHaveTextContent("Lab model");
    getItem.mockRestore();
  });

  it("does not send whitespace-only or overlong questions", async () => {
    const { user } = renderPage("/chat/1");
    const box = await screen.findByRole("textbox");
    await user.type(box, "   {Enter}");
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    await user.clear(box);
    await user.click(box);
    await user.paste("x".repeat(2001));
    expect(screen.getByText(/2,001 \/ 2,000 characters/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    await user.keyboard("{Enter}");
    expect(streamSse).not.toHaveBeenCalled();
  });

  it("Shift+Enter adds a newline and Enter during IME composition does nothing", async () => {
    const { user } = renderPage("/chat/1");
    const box = await screen.findByRole("textbox");
    await user.type(box, "first{Shift>}{Enter}{/Shift}second");
    expect(box).toHaveValue("first\nsecond");
    fireEvent.keyDown(box, { key: "Enter", isComposing: true });
    expect(streamSse).not.toHaveBeenCalled();
    expect(box).toHaveValue("first\nsecond");
  });

  it("trims the question before sending", async () => {
    const s = pendingStream();
    const { user } = renderPage("/chat/1");
    await ask(user, "  How many came?  ");
    expect(bodies()[0]).toMatchObject({ question: "How many came?" });
    await s.emit({ event: "done", data: { turn_id: null } });
    await s.finish();
  });

  it("lists conversations by title; New chat goes to /chat", async () => {
    const { router, user } = renderPage("/chat/1");
    const list = await screen.findByRole("navigation", { name: "Conversations" });
    expect(await within(list).findByRole("link", { name: "Bagel Breakfast attendance" })).toHaveAttribute("href", "/chat/1");
    expect(within(list).getByRole("link", { name: "New conversation" })).toHaveAttribute("href", "/chat/2");
    await user.click(screen.getByRole("button", { name: "New chat" }));
    expect(router.state.location.pathname).toBe("/chat");
    expect(apiSend).not.toHaveBeenCalled();
  });

  it("shows the empty-draft hint", async () => {
    renderPage("/chat");
    expect(await screen.findByText("Ask a question about your data to start.")).toBeInTheDocument();
  });

  it("shows a visible AI model label and exactly one combobox with that name", async () => {
    renderPage("/chat");
    expect(await screen.findAllByText("AI model")).not.toHaveLength(0);
    expect(screen.getAllByRole("combobox", { name: "AI model" })).toHaveLength(1);
  });

  it("marks the open conversation and has no Conversations heading", async () => {
    renderPage("/chat/1");
    const list = await screen.findByRole("navigation", { name: "Conversations" });
    expect(await within(list).findByRole("link", { name: "Bagel Breakfast attendance" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(list).getByRole("link", { name: "New conversation" })).not.toHaveAttribute("aria-current");
    expect(screen.queryByRole("heading", { name: "Conversations" })).toBeNull();
  });

  it("says when the conversation no longer exists", async () => {
    details[1] = new ApiError(404, "conversation_not_found", "That conversation no longer exists.");
    renderPage("/chat/1");
    expect(await screen.findByText("This conversation no longer exists.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start a new chat" })).toHaveAttribute("href", "/chat");
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("keeps the open conversation when a background refetch fails", async () => {
    details[1] = detail(1, [savedTurn({ id: 4, seq: 1 })]);
    const { client } = renderPage("/chat/1");
    expect(await screen.findByText("How many people came to the Bagel Breakfast?")).toBeInTheDocument();
    details[1] = new ApiError(0, "network_error", "Could not reach the server.");
    await act(async () => {
      await client.refetchQueries({ queryKey: ["conversation", 1] });
      await new Promise((resolve) => setTimeout(resolve, 0)); // TanStack notifies on a timer
    });
    expect(client.getQueryState(["conversation", 1])?.status).toBe("error");
    expect(screen.getByText("How many people came to the Bagel Breakfast?")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeEnabled();
    expect(screen.queryByText("Could not load this conversation.")).not.toBeInTheDocument();
  });

  it("offers Retry when the conversation cannot be loaded", async () => {
    details[1] = new ApiError(0, "network_error", "Could not reach the server.");
    const { user } = renderPage("/chat/1");
    expect(await screen.findByText("Could not load this conversation.")).toBeInTheDocument();
    details[1] = detail(1, [savedTurn({ id: 4, seq: 1 })]);
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("How many people came to the Bagel Breakfast?")).toBeInTheDocument();
    expect(screen.queryByText("Could not load this conversation.")).not.toBeInTheDocument();
  });

  it("asks for an AI model when there are no profiles", async () => {
    profiles = [];
    renderPage("/chat");
    expect(await screen.findByText(/Add an AI model in Settings to start/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to Settings" })).toHaveAttribute("href", "/settings");
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    // One hint, not two competing ones.
    expect(screen.queryByText(/Ask a question about your data to start/)).not.toBeInTheDocument();
  });
});
