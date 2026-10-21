import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiGet, apiSend } from "./client";

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

  it("falls back to http_<status> for non-JSON errors", async () => {
    stubFetch(new Response("<html>Bad Gateway</html>", { status: 502 }));
    await expect(apiGet("/api/health")).rejects.toMatchObject({ status: 502, code: "http_502" });
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
});
