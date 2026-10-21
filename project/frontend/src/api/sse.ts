import { ApiError, hubFetch, toApiError } from "./client";
import type { SseEvent } from "./types";

export type { SseEvent } from "./types";

// Feed decoded text chunks; calls onEvent once per complete "event:/data:" block.
export function createSseParser(onEvent: (e: SseEvent) => void): (chunk: string) => void {
  let buffer = "";

  function dispatch(block: string) {
    let event = "message";
    const data: string[] = [];
    for (const line of block.split("\n")) {
      if (line === "" || line.startsWith(":")) continue;
      const colon = line.indexOf(":");
      const field = colon === -1 ? line : line.slice(0, colon);
      let value = colon === -1 ? "" : line.slice(colon + 1);
      if (value.startsWith(" ")) value = value.slice(1);
      if (field === "event") event = value;
      else if (field === "data") data.push(value);
    }
    if (data.length === 0) return;
    onEvent({ event, data: JSON.parse(data.join("\n")) } as SseEvent);
  }

  return (chunk) => {
    buffer += chunk.replace(/\r\n?/g, "\n");
    let end = buffer.indexOf("\n\n");
    while (end !== -1) {
      dispatch(buffer.slice(0, end));
      buffer = buffer.slice(end + 2);
      end = buffer.indexOf("\n\n");
    }
  };
}

export async function streamSse(
  path: string,
  body: unknown,
  onEvent: (e: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  // A fetch failure rejects with network_error; an abort, with the AbortError.
  const res = await hubFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) throw await toApiError(res);

  let done = false;
  // An error thrown by onEvent is the caller's bug, not a lost connection: it passes through as is.
  let handlerError: { error: unknown } | null = null;
  const feed = createSseParser((e) => {
    if (signal?.aborted) return;
    if (e.event === "done") done = true;
    try {
      onEvent(e);
    } catch (error) {
      handlerError = { error };
      throw error;
    }
  });
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  try {
    if (!res.body) throw new Error("empty body");
    reader = res.body.getReader();
    const active = reader;
    // A pending read() does not always settle on abort; cancel unblocks it.
    signal?.addEventListener("abort", () => void active.cancel().catch(() => {}), { once: true });
    const decoder = new TextDecoder();
    for (;;) {
      const { done: finished, value } = await active.read();
      if (signal?.aborted) break;
      if (finished) break;
      feed(decoder.decode(value, { stream: true }));
    }
  } catch (err) {
    if (handlerError) {
      void reader?.cancel().catch(() => {});
      throw (handlerError as { error: unknown }).error;
    }
    if (signal?.aborted) throw signal.reason ?? err;
    throw new ApiError(0, "stream_interrupted", "Connection lost.");
  }
  if (signal?.aborted) throw signal.reason;
  if (!done) throw new ApiError(0, "stream_interrupted", "Connection lost.");
}
