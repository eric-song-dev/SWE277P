// The only module that calls fetch, all in hubFetch: credentials (and 401 handling, once login
// exists) attach there.

export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown;

  constructor(status: number, code: string, message: string, details: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export async function toApiError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    const err = body?.error;
    if (err && typeof err.code === "string" && typeof err.message === "string") {
      return new ApiError(res.status, err.code, err.message, err.details ?? null);
    }
  } catch {
    // Not JSON (for example an HTML 502 page from nginx).
  }
  return new ApiError(res.status, `http_${res.status}`, res.statusText || `HTTP ${res.status}`);
}

// The one fetch seam. Exported for sse.ts only; features use the helpers below.
export async function hubFetch(path: string, init: RequestInit = {}): Promise<Response> {
  try {
    return await fetch(path, { ...init, credentials: "same-origin" });
  } catch (err) {
    // An abort stays an AbortError, so callers can tell it from a lost connection.
    if (init.signal?.aborted || !(err instanceof TypeError)) throw err;
    throw new ApiError(0, "network_error", "Could not reach the server.");
  }
}

async function readJson<T>(res: Response): Promise<T> {
  if (!res.ok) throw await toApiError(res);
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  const init: RequestInit = { method, headers };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  return readJson<T>(await hubFetch(path, init));
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>("GET", path);
}

export function apiSend<T>(
  method: "POST" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
): Promise<T> {
  return request<T>(method, path, body);
}

export async function apiUpload<T>(path: string, files: File[]): Promise<T> {
  const form = new FormData();
  for (const file of files) form.append("files", file);
  // No Content-Type: the browser adds the multipart boundary.
  return readJson<T>(await hubFetch(path, { method: "POST", body: form }));
}

export interface DownloadResult {
  fileName: string;
  truncated: boolean;
  rowCap: number | null;
}

export async function apiDownload(path: string): Promise<DownloadResult> {
  const res = await hubFetch(path);
  if (!res.ok) throw await toApiError(res);
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const fileName = /filename="([^"]+)"/.exec(disposition)?.[1] ?? "download";
  const cap = Number.parseInt(res.headers.get("X-Hub-Row-Cap") ?? "", 10);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
  return {
    fileName,
    truncated: res.headers.get("X-Hub-Truncated") === "true",
    rowCap: Number.isNaN(cap) ? null : cap,
  };
}
