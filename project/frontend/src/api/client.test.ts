import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiDownload, apiGet, apiSend, apiUpload } from "./client";

afterEach(() => vi.unstubAllGlobals());

function stubFetch(response: Response) {
  const fn = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("api client", () => {
  it("parses the error shape into ApiError", async () => {
    stubFetch(
      new Response(
        JSON.stringify({ error: { code: "import_not_found", message: "Not found", details: null } }),
        { status: 404 },
      ),
    );
    await expect(apiGet("/api/imports/9")).rejects.toMatchObject({
      status: 404,
      code: "import_not_found",
    });
    await expect(apiGet("/api/imports/9")).rejects.toBeInstanceOf(ApiError);
  });

  it("returns parsed JSON on success", async () => {
    stubFetch(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    await expect(apiGet<{ status: string }>("/api/health")).resolves.toEqual({ status: "ok" });
  });

  it("returns undefined on 204", async () => {
    stubFetch(new Response(null, { status: 204 }));
    await expect(apiSend("DELETE", "/api/things/1")).resolves.toBeUndefined();
  });

  it("gives a non-JSON 5xx (nginx while the api restarts) a plain message", async () => {
    stubFetch(new Response("<html>Bad Gateway</html>", { status: 502, statusText: "Bad Gateway" }));
    await expect(apiGet("/api/health")).rejects.toMatchObject({
      status: 502,
      code: "server_unavailable",
      message: "The Hub server isn't responding. Check that it is running, then try again.",
    });
  });

  it("falls back to http_<status> for other non-JSON errors", async () => {
    stubFetch(new Response("<html>Too large</html>", { status: 413, statusText: "Payload Too Large" }));
    await expect(apiGet("/api/health")).rejects.toMatchObject({
      status: 413,
      code: "http_413",
      message: "Payload Too Large",
    });
  });

  it("sends same-origin credentials on a GET", async () => {
    const fn = stubFetch(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    await apiGet("/api/health");
    expect(fn.mock.calls[0][1].credentials).toBe("same-origin");
  });

  it("maps a fetch failure to network_error for JSON requests and uploads", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const networkError = { status: 0, code: "network_error", message: "Could not reach the server." };
    await expect(apiGet("/api/health")).rejects.toMatchObject(networkError);
    await expect(apiSend("POST", "/api/things", { a: 1 })).rejects.toMatchObject(networkError);
    await expect(apiUpload("/api/imports", [])).rejects.toMatchObject(networkError);
    await expect(apiGet("/api/health")).rejects.toBeInstanceOf(ApiError);
  });

  it("sends same-origin credentials and a JSON body", async () => {
    const fn = stubFetch(new Response(JSON.stringify({ id: 1 }), { status: 200 }));
    await apiSend("POST", "/api/things", { a: 1 });
    const [url, init] = fn.mock.calls[0];
    expect(url).toBe("/api/things");
    expect(init.credentials).toBe("same-origin");
    expect(init.method).toBe("POST");
    expect(init.headers["Content-Type"]).toBe("application/json");
    expect(init.body).toBe(JSON.stringify({ a: 1 }));
  });

  it("returns undefined for any empty 2xx body", async () => {
    stubFetch(new Response("", { status: 200 }));
    await expect(apiSend("POST", "/api/things")).resolves.toBeUndefined();
    stubFetch(new Response("", { status: 201 }));
    await expect(apiSend("POST", "/api/things")).resolves.toBeUndefined();
  });

  it("uploads files as multipart under 'files' without a Content-Type header", async () => {
    const fn = stubFetch(new Response(JSON.stringify({ files: [] }), { status: 200 }));
    const a = new File(["a"], "a.csv");
    const b = new File(["b"], "b.csv");
    await expect(apiUpload("/api/imports", [a, b])).resolves.toEqual({ files: [] });
    const [url, init] = fn.mock.calls[0];
    expect(url).toBe("/api/imports");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("same-origin");
    expect(init.headers?.["Content-Type"]).toBeUndefined();
    expect((init.body as FormData).getAll("files")).toEqual([a, b]);
  });

  it("returns undefined for an empty 2xx upload response", async () => {
    stubFetch(new Response("", { status: 200 }));
    await expect(apiUpload("/api/imports", [])).resolves.toBeUndefined();
  });

  it("maps upload errors to ApiError", async () => {
    stubFetch(
      new Response(JSON.stringify({ error: { code: "bad_file", message: "Bad", details: null } }), {
        status: 422,
      }),
    );
    await expect(apiUpload("/api/imports", [])).rejects.toMatchObject({ status: 422, code: "bad_file" });
  });
});

describe("apiDownload", () => {
  function stubUrls() {
    const create = vi.fn().mockReturnValue("blob:fake");
    const revoke = vi.fn();
    vi.stubGlobal("URL", Object.assign(URL, { createObjectURL: create, revokeObjectURL: revoke }));
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    return { create, revoke, click };
  }

  afterEach(() => vi.restoreAllMocks());

  it("returns the server file name and clicks an object-URL anchor", async () => {
    const { create, revoke, click } = stubUrls();
    stubFetch(
      new Response("data", {
        status: 200,
        headers: {
          "Content-Disposition": 'attachment; filename="hub-turn-3-20261105-1010.xlsx"',
        },
      }),
    );
    await expect(apiDownload("/api/chat/turns/3/export?format=xlsx")).resolves.toEqual({
      fileName: "hub-turn-3-20261105-1010.xlsx",
      truncated: false,
      rowCap: null,
    });
    expect(create).toHaveBeenCalledTimes(1);
    expect(click).toHaveBeenCalledTimes(1);
    expect(revoke).toHaveBeenCalledWith("blob:fake");
  });

  it("reports truncation and the row cap, and falls back to 'download'", async () => {
    stubUrls();
    stubFetch(
      new Response("data", {
        status: 200,
        headers: { "X-Hub-Truncated": "true", "X-Hub-Row-Cap": "100000" },
      }),
    );
    await expect(apiDownload("/api/dataset/export?format=csv")).resolves.toEqual({
      fileName: "download",
      truncated: true,
      rowCap: 100000,
    });
  });

  it("sends same-origin credentials and maps a fetch failure to network_error", async () => {
    stubUrls();
    const fn = stubFetch(new Response("data", { status: 200 }));
    await apiDownload("/api/dataset/export?format=csv");
    expect(fn.mock.calls[0][1].credentials).toBe("same-origin");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(apiDownload("/api/dataset/export?format=csv")).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
  });

  it("rejects with ApiError on a non-2xx response", async () => {
    stubUrls();
    stubFetch(
      new Response(JSON.stringify({ error: { code: "turn_not_found", message: "No", details: null } }), {
        status: 404,
      }),
    );
    await expect(apiDownload("/api/chat/turns/9/export?format=csv")).rejects.toMatchObject({
      code: "turn_not_found",
    });
  });
});
