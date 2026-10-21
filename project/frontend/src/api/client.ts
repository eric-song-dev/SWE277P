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

async function toApiError(res: Response): Promise<ApiError> {
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
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
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
