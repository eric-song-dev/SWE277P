import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiSend } from "../../api/client";
import { streamSse } from "../../api/sse";
import type { QueryResultOut, SseEvent } from "../../api/types";
import { useChatStream } from "./useChatStream";

vi.mock("../../api/client", async (orig) => ({
  ...(await orig<typeof import("../../api/client")>()),
  apiSend: vi.fn(),
}));
vi.mock("../../api/sse", () => ({ streamSse: vi.fn() }));

const RESULT: QueryResultOut = { columns: ["n"], rows: [[1]], row_count: 1, truncated: false };

type Handler = (e: SseEvent) => void;

function setup(initialId: number | null, onCreated?: (id: number) => void) {
  const queryClient = new QueryClient();
  const invalidate = vi.spyOn(queryClient, "invalidateQueries");
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  const hook = renderHook(({ id }) => useChatStream(id, onCreated), {
    wrapper,
    initialProps: { id: initialId },
  });
  return { ...hook, invalidate };
}

// A stream the test finishes by hand; resolves or rejects on demand.
function pendingStream() {
  let emit: Handler = () => {};
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

beforeEach(() => {
  vi.clearAllMocks();
});

describe("useChatStream", () => {
  it("streams to the conversation and stores the result on done", async () => {
    const s = pendingStream();
    const { result, invalidate } = setup(7);
    act(() => result.current.send("how many?", 3, true));
    expect(streamSse).toHaveBeenCalledWith(
      "/api/conversations/7/messages",
      { question: "how many?", llm_profile_id: 3, share_results: true },
      expect.any(Function),
      expect.any(AbortSignal),
    );
    await s.emit({ event: "result", data: RESULT });
    await s.emit({ event: "done", data: { turn_id: 9 } });
    await s.finish();
    expect(result.current.live?.status).toBe("done");
    expect(result.current.resultsByTurnId[9]).toEqual(RESULT);
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["conversation", 7] });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["conversations"] });
  });

  it("interrupted stream becomes a retryable error; retry resends the same question", async () => {
    const first = pendingStream();
    const { result } = setup(7);
    act(() => result.current.send("how many?", 3, false));
    await first.finish(new ApiError(0, "stream_interrupted", "Connection lost."));
    expect(result.current.live).toMatchObject({
      status: "error",
      error: { code: "stream_interrupted", message: "Connection lost. Retry." },
    });

    const second = pendingStream();
    act(() => result.current.retry());
    expect(streamSse).toHaveBeenCalledTimes(2);
    expect(vi.mocked(streamSse).mock.calls[1][1]).toEqual({
      question: "how many?",
      llm_profile_id: 3,
      share_results: false,
    });
    expect(result.current.live?.status).toBe("streaming");
    await second.finish();
  });

  it("maps a network error the same way", async () => {
    const s = pendingStream();
    const { result } = setup(7);
    act(() => result.current.send("q", null, true));
    await s.finish(new ApiError(0, "network_error", "Could not reach the server."));
    expect(result.current.live?.error).toEqual({
      code: "network_error",
      message: "Connection lost. Retry.",
    });
  });

  it("keeps the server code and message for other API errors", async () => {
    const s = pendingStream();
    const { result } = setup(7);
    act(() => result.current.send("q", null, true));
    await s.finish(new ApiError(404, "conversation_not_found", "No such conversation."));
    expect(result.current.live?.error).toEqual({
      code: "conversation_not_found",
      message: "No such conversation.",
    });
  });

  it("ignores send and retry while streaming", async () => {
    const s = pendingStream();
    const { result } = setup(7);
    act(() => {
      result.current.send("one", null, true);
      result.current.send("two", null, true);
    });
    act(() => result.current.retry());
    expect(streamSse).toHaveBeenCalledTimes(1);
    await s.finish();
  });

  it("creates a conversation when the id is null and keeps streaming across the id change", async () => {
    vi.mocked(apiSend).mockResolvedValueOnce({ id: 21 });
    const s = pendingStream();
    const onCreated = vi.fn();
    const { result, rerender } = setup(null, onCreated);
    await act(async () => result.current.send("q", null, true));
    expect(apiSend).toHaveBeenCalledWith("POST", "/api/conversations");
    expect(onCreated).toHaveBeenCalledWith(21);
    expect(vi.mocked(streamSse).mock.calls[0][0]).toBe("/api/conversations/21/messages");

    rerender({ id: 21 });
    expect(s.signal?.aborted).toBe(false);
    expect(result.current.live?.status).toBe("streaming");
    await s.emit({ event: "done", data: { turn_id: 1 } });
    await s.finish();
    expect(result.current.live?.status).toBe("done");
  });

  it("ignores a second send while the conversation is being created", async () => {
    let resolve: (v: { id: number }) => void = () => {};
    vi.mocked(apiSend).mockReturnValueOnce(new Promise((r) => (resolve = r)));
    const s = pendingStream();
    const { result } = setup(null);
    act(() => {
      result.current.send("one", null, true);
      result.current.send("two", null, true);
    });
    await act(async () => resolve({ id: 5 }));
    expect(apiSend).toHaveBeenCalledTimes(1);
    expect(streamSse).toHaveBeenCalledTimes(1);
    await s.finish();
  });

  it("shows the ApiError when creating the conversation fails", async () => {
    vi.mocked(apiSend).mockRejectedValueOnce(new ApiError(500, "internal_error", "Boom."));
    const { result } = setup(null);
    await act(async () => result.current.send("q", null, true));
    expect(result.current.live).toMatchObject({
      status: "error",
      error: { code: "internal_error", message: "Boom." },
    });
    expect(streamSse).not.toHaveBeenCalled();
  });

  it("aborts and resets when switching between existing conversations", async () => {
    const s = pendingStream();
    const { result, rerender } = setup(1);
    act(() => result.current.send("q", null, true));
    rerender({ id: 2 });
    expect(s.signal?.aborted).toBe(true);
    expect(result.current.live).toBeNull();
    await s.finish(new DOMException("aborted", "AbortError"));
    expect(result.current.live).toBeNull();
    // the new conversation accepts a send
    const s2 = pendingStream();
    act(() => result.current.send("q2", null, true));
    expect(vi.mocked(streamSse).mock.calls[1][0]).toBe("/api/conversations/2/messages");
    await s2.finish();
  });

  it("aborts on unmount without state updates", async () => {
    const s = pendingStream();
    const { result, unmount } = setup(1);
    act(() => result.current.send("q", null, true));
    unmount();
    expect(s.signal?.aborted).toBe(true);
    await s.finish(new DOMException("aborted", "AbortError"));
    await waitFor(() => expect(s.signal?.aborted).toBe(true));
  });
});
