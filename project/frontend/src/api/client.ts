// The only module that calls fetch. Auth headers or tokens attach here later.

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

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  const init: RequestInit = { method, headers, credentials: "same-origin" };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const res = await fetch(path, init);
  if (!res.ok) throw await toApiError(res);
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
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
  const res = await fetch(path, { method: "POST", body: form, credentials: "same-origin" });
  if (!res.ok) throw await toApiError(res);
  return (await res.json()) as T;
}

export interface DownloadResult {
  fileName: string;
  truncated: boolean;
  rowCap: number | null;
}

export async function apiDownload(path: string): Promise<DownloadResult> {
  const res = await fetch(path, { credentials: "same-origin" });
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
