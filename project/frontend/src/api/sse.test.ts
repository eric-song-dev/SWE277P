import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "./client";
import { createSseParser, streamSse, type SseEvent } from "./sse";

afterEach(() => vi.unstubAllGlobals());

const encoder = new TextEncoder();

function sseResponse(chunks: string[], init: ResponseInit = { status: 200 }) {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const c of chunks) controller.enqueue(encoder.encode(c));
      controller.close();
    },
  });
  return new Response(body, init);
}

const STEP = 'event: step\ndata: {"name":"generating","attempt":1}\n\n';
const DONE = 'event: done\ndata: {"turn_id":7}\n\n';

describe("createSseParser", () => {
  it("parses events split across chunks", () => {
    const seen: SseEvent[] = [];
    const feed = createSseParser((e) => seen.push(e));
    feed('event: step\ndata: {"name":"gene');
    feed('rating","attempt":1}\n\nevent: done\ndata: {"turn_id":7}\n\n');
    expect(seen).toEqual([
      { event: "step", data: { name: "generating", attempt: 1 } },
      { event: "done", data: { turn_id: 7 } },
    ]);
  });

  it("handles CRLF, multi-line data, comments, and blocks without data", () => {
    const seen: SseEvent[] = [];
    const feed = createSseParser((e) => seen.push(e));
    feed(": keep-alive\r\n\r\n");
    feed("event: error\r\ndata:{\"code\":\"x\",\r\ndata: \"message\":\"y\"}\r\n\r\n");
    feed("event: step\n\n");
    expect(seen).toEqual([{ event: "error", data: { code: "x", message: "y" } }]);
  });
});

describe("streamSse", () => {
  it("posts JSON with SSE headers and resolves after done", async () => {
    const fn = vi.fn().mockResolvedValue(sseResponse([STEP, DONE]));
    vi.stubGlobal("fetch", fn);
    const seen: SseEvent[] = [];
    await streamSse("/api/conversations/1/messages", { question: "hi" }, (e) => seen.push(e));
    expect(seen.map((e) => e.event)).toEqual(["step", "done"]);
    const [url, init] = fn.mock.calls[0];
    expect(url).toBe("/api/conversations/1/messages");
    expect(init.method).toBe("POST");
    expect(init.headers.Accept).toBe("text/event-stream");
    expect(init.headers["Content-Type"]).toBe("application/json");
    expect(init.body).toBe(JSON.stringify({ question: "hi" }));
    expect(init.credentials).toBe("same-origin");
  });

  it("rejects with stream_interrupted when the stream ends without done", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([STEP])));
    await expect(streamSse("/s", {}, () => {})).rejects.toMatchObject({
      status: 0,
      code: "stream_interrupted",
    });
  });

  it("rejects with stream_interrupted when reading the body throws", async () => {
    const body = new ReadableStream<Uint8Array>({
      start(c) {
        c.enqueue(encoder.encode(STEP));
        c.error(new TypeError("network"));
      },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body)));
    await expect(streamSse("/s", {}, () => {})).rejects.toMatchObject({ code: "stream_interrupted" });
  });

  it("lets an error thrown by onEvent through instead of reporting a lost connection", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([STEP, DONE])));
    const boom = new Error("handler bug");
    const p = streamSse("/s", {}, () => {
      throw boom;
    });
    await expect(p).rejects.toBe(boom);
  });

  it("decodes a multi-byte character split across two chunks", async () => {
    const bytes = encoder.encode('event: analysis\ndata: {"text":"caf\u00e9 \u2713"}\n\n' + DONE);
    // Cut between the two bytes of the first "é".
    const at = bytes.indexOf(encoder.encode("é")[0]) + 1;
    expect(at).toBeGreaterThan(0);
    const body = new ReadableStream<Uint8Array>({
      start(c) {
        c.enqueue(bytes.slice(0, at));
        c.enqueue(bytes.slice(at));
        c.close();
      },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body)));
    const seen: SseEvent[] = [];
    await streamSse("/s", {}, (e) => seen.push(e));
    expect(seen[0]).toEqual({ event: "analysis", data: { text: "café ✓" } });
  });

  it("rejects with network_error when fetch throws", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(streamSse("/s", {}, () => {})).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
  });

  it("rejects with the API error for a non-2xx response", async () => {
    const res = new Response(
      JSON.stringify({ error: { code: "conversation_not_found", message: "Nope", details: null } }),
      { status: 404 },
    );
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(res));
    const p = streamSse("/s", {}, () => {});
    await expect(p).rejects.toBeInstanceOf(ApiError);
    await expect(p).rejects.toMatchObject({ status: 404, code: "conversation_not_found" });
  });

  it("aborting before the response arrives rejects with AbortError, not network_error", async () => {
    const controller = new AbortController();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_path: string, init: RequestInit) =>
          new Promise<Response>((_resolve, reject) => {
            init.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
          }),
      ),
    );
    const p = streamSse("/s", {}, () => {}, controller.signal);
    controller.abort();
    await expect(p).rejects.toMatchObject({ name: "AbortError" });
    await expect(p).rejects.not.toBeInstanceOf(ApiError);
  });

  it("aborting stops delivery and rejects with AbortError", async () => {
    const controller = new AbortController();
    const body = new ReadableStream<Uint8Array>({
      start(c) {
        c.enqueue(encoder.encode(STEP)); // then stays open
      },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body)));
    const seen: SseEvent[] = [];
    const p = streamSse("/s", {}, (e) => {
      seen.push(e);
      controller.abort();
    }, controller.signal);
    await expect(p).rejects.toMatchObject({ name: "AbortError" });
    expect(seen.map((e) => e.event)).toEqual(["step"]);
  });

  it("drops events that arrive in the same chunk after an abort", async () => {
    const controller = new AbortController();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([STEP + DONE])));
    const seen: SseEvent[] = [];
    const p = streamSse("/s", {}, (e) => {
      seen.push(e);
      controller.abort();
    }, controller.signal);
    await expect(p).rejects.toMatchObject({ name: "AbortError" });
    expect(seen.map((e) => e.event)).toEqual(["step"]);
  });
});
