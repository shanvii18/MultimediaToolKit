import { Project, Asset, Job, Conversion } from "@/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Me {
  id: string;
  email: string;
  role: string;
  auth_mode: "access_key" | "dev_open";
}

export interface AuthSession {
  token: string;
  expires_at: string;
  user: { id: string; email: string; role: string };
}

/** Session token from email + password sign-in, sent as a Bearer header. */
const SESSION_STORAGE = "mtk_session";
// Older builds stored an invite access key here; it is cleared on first load.
const LEGACY_KEY_STORAGE = "mtk_access_key";

function getSessionToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(SESSION_STORAGE);
  } catch (_) {
    return null;
  }
}

function authHeaders(): Record<string, string> {
  const token = getSessionToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

if (typeof window !== "undefined") {
  try {
    window.localStorage.removeItem(LEGACY_KEY_STORAGE);
  } catch (_) {}
}

/** Fired when the API answers 401 so the shell can send the user to the sign-in page. */
function notifyUnauthorized(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("mtk:unauthorized"));
}

// ---------------------------------------------------------------------------
// Backend reachability + error classification
// ---------------------------------------------------------------------------
/**
 * online      - the last request reached the API
 * waking      - the API is starting (Render Free sleeps when idle, or restarts); requests are retried
 * unreachable - retries were exhausted without reaching the API
 */
export type BackendStatus = "checking" | "online" | "waking" | "unreachable";

export type ApiErrorKind =
  | "waking" // proxy answered 502/503/504 without an API body: server starting or restarting
  | "network" // the request never reached the API (offline, DNS, server down, proxy error without CORS)
  | "timeout" // no answer within the time limit
  | "auth" // 401: not signed in / session expired
  | "rate_limited" // 429
  | "server" // 5xx answered by the API itself
  | "client"; // other 4xx answered by the API (validation, not found...)

export class ApiError extends Error {
  kind: ApiErrorKind;
  status?: number;
  constructor(message: string, kind: ApiErrorKind, status?: number) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
  }
  /** Transient problems that are safe to retry for idempotent requests. */
  get transient(): boolean {
    return this.kind === "waking" || this.kind === "network" || this.kind === "timeout";
  }
}

let backendStatus: BackendStatus = "checking";
function setBackendStatus(next: BackendStatus): void {
  if (next === backendStatus) return;
  backendStatus = next;
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("mtk:backend-status", { detail: next }));
}
export function getBackendStatus(): BackendStatus {
  return backendStatus;
}

/** Human-readable message for any error thrown by ApiClient. */
export function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    switch (err.kind) {
      case "waking":
        return "The server is starting up (free hosting sleeps when idle). Please wait about a minute and try again.";
      case "network":
        return "Cannot reach the server right now. It may be restarting; please try again in a minute.";
      case "timeout":
        return "The server took too long to answer. Please try again.";
      default:
        return err.message;
    }
  }
  return (err as any)?.message || "Something went wrong.";
}

const RETRY_DELAYS_MS = [1000, 2000, 4000, 8000, 15000, 20000]; // ~50 s in total: covers a Render cold start
const DEFAULT_TIMEOUT_MS = 30000;
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

interface RequestOpts extends RequestInit {
  /** Retry transient failures with exponential backoff (default: GET/HEAD only). */
  retry?: boolean;
  timeoutMs?: number;
}

async function fetchOnce(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (e: any) {
    if (e?.name === "AbortError") throw new ApiError("Request timed out.", "timeout");
    throw new ApiError("Network error.", "network");
  } finally {
    clearTimeout(timer);
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  let detail = "";
  if (isJson) {
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch (_) {}
  }
  if (res.status === 401) return new ApiError(detail || "Please sign in to continue.", "auth", 401);
  if (res.status === 429) return new ApiError(detail || "Too many requests. Please wait a moment.", "rate_limited", 429);
  if ([502, 503, 504].includes(res.status) && !isJson) return new ApiError("Server is starting.", "waking", res.status);
  if (res.status >= 500) return new ApiError(detail || `Server error (${res.status}).`, "server", res.status);
  return new ApiError(detail || `Request failed (${res.status}).`, "client", res.status);
}

async function sendWithRetry(url: string, init: RequestInit, retry: boolean, timeoutMs: number): Promise<Response> {
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetchOnce(url, init, timeoutMs);
      if (res.ok) {
        setBackendStatus("online");
        return res;
      }
      const err = await toApiError(res);
      if (err.kind !== "waking") setBackendStatus("online"); // the API itself answered
      throw err;
    } catch (e) {
      const err = e instanceof ApiError ? e : new ApiError("Network error.", "network");
      if (err.kind === "auth") notifyUnauthorized();
      if (!retry || !err.transient || attempt >= RETRY_DELAYS_MS.length) {
        if (err.transient) setBackendStatus("unreachable");
        throw err;
      }
      setBackendStatus("waking");
      await sleep(RETRY_DELAYS_MS[attempt]);
    }
  }
}

function newIdempotencyKey(): string {
  try {
    return crypto.randomUUID();
  } catch (_) {
    return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

export class ApiClient {
  private static async request<T>(endpoint: string, options: RequestOpts = {}): Promise<T> {
    const { retry, timeoutMs, ...init } = options;
    const method = (init.method || "GET").toUpperCase();
    const headers = { ...authHeaders(), ...((init.headers as Record<string, string>) || {}) };
    const res = await sendWithRetry(
      `${API_BASE}${endpoint}`,
      { ...init, headers },
      retry ?? (method === "GET" || method === "HEAD"),
      timeoutMs ?? DEFAULT_TIMEOUT_MS,
    );
    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  }

  /** Resolves once the API answers /health (waits through a cold start); throws ApiError otherwise. */
  static async waitForBackend(): Promise<void> {
    await this.request<{ status: string }>("/health", { retry: true, timeoutMs: 20000 });
  }

  // Accounts: public email + password sign-up / sign-in
  private static storeSession(session: AuthSession): AuthSession {
    try {
      window.localStorage.setItem(SESSION_STORAGE, session.token);
    } catch (_) {}
    return session;
  }

  static async signUp(email: string, password: string): Promise<AuthSession> {
    const session = await this.request<AuthSession>("/api/v1/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return this.storeSession(session);
  }

  static async signIn(email: string, password: string): Promise<AuthSession> {
    const session = await this.request<AuthSession>("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return this.storeSession(session);
  }

  static async signOut(): Promise<void> {
    try {
      if (getSessionToken()) await this.request<void>("/api/v1/auth/logout", { method: "POST" });
    } catch (_) {
      // Signing out locally must work even if the server is asleep or unreachable.
    } finally {
      try {
        window.localStorage.removeItem(SESSION_STORAGE);
      } catch (_) {}
    }
  }

  static isSignedIn(): boolean {
    return !!getSessionToken();
  }

  static async getMe(): Promise<Me> {
    return this.request<Me>("/api/v1/me");
  }

  // Health
  static async getHealth(retry = false): Promise<{ status: string }> {
    return this.request<{ status: string }>("/health", { retry, timeoutMs: 20000 });
  }

  // Projects
  static async listProjects(): Promise<Project[]> {
    return this.request<Project[]>("/api/v1/projects");
  }

  static async createProject(title: string, description?: string): Promise<Project> {
    return this.request<Project>("/api/v1/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description }),
    });
  }

  static async getProject(id: string): Promise<Project> {
    return this.request<Project>(`/api/v1/projects/${id}`);
  }

  static async getProjectAssets(projectId: string): Promise<Asset[]> {
    return this.request<Asset[]>(`/api/v1/projects/${projectId}/assets`);
  }

  // Assets
  static async listAssets(): Promise<Asset[]> {
    return this.request<Asset[]>("/api/v1/assets");
  }

  static async uploadMedia(file: File, projectId?: string): Promise<Asset> {
    const formData = new FormData();
    formData.append("file", file);
    if (projectId) {
      formData.append("project_id", projectId);
    }

    // Make sure a sleeping server is awake first; the upload itself is not retried blindly
    // (a retry after a lost response would store the file twice).
    await this.waitForBackend();
    const res = await sendWithRetry(`${API_BASE}/api/v1/media`, { method: "POST", headers: authHeaders(), body: formData },
      false, 300000);
    return res.json() as Promise<Asset>;
  }

  /**
   * Download links use the short-lived signed `download_url` returned by the API,
   * because <a href> and <audio src> cannot send the Authorization header.
   */
  static getDownloadUrl(asset?: Pick<Asset, "download_url"> | null): string {
    if (!asset || !asset.download_url) return "#";
    return `${API_BASE}${asset.download_url}`;
  }

  static async deleteAsset(assetId: string): Promise<void> {
    await this.request<void>(`/api/v1/assets/${assetId}`, { method: "DELETE" });
  }

  // Conversions catalogue (20 directed conversions with live engine availability)
  static async listConversions(): Promise<Conversion[]> {
    return this.request<Conversion[]>("/api/v1/conversions");
  }

  // Jobs
  static async listJobs(): Promise<Job[]> {
    return this.request<Job[]>("/api/v1/jobs");
  }

  static async getJob(jobId: string): Promise<Job> {
    return this.request<Job>(`/api/v1/jobs/${jobId}`);
  }

  static async createJob(tool: string, inputAssetIds: string[] = [], paramsJson: Record<string, any> = {}, projectId?: string): Promise<Job> {
    await this.waitForBackend();
    // The same Idempotency-Key on every retry: the server returns the first job, never a duplicate.
    return this.request<Job>("/api/v1/jobs", {
      method: "POST",
      retry: true,
      headers: { "Content-Type": "application/json", "Idempotency-Key": newIdempotencyKey() },
      body: JSON.stringify({
        tool,
        input_asset_ids: inputAssetIds,
        params_json: paramsJson,
        project_id: projectId,
      }),
    });
  }
}
