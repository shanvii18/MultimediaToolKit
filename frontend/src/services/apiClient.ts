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

export class ApiClient {
  private static async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      ...authHeaders(),
      ...options.headers,
    };

    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) notifyUnauthorized();
    if (!res.ok) {
      let errorMsg = `Request failed with status ${res.status}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorMsg = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch (_) {}
      throw new Error(errorMsg);
    }
    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
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
  static async getHealth(): Promise<{ status: string }> {
    return this.request<{ status: string }>("/health");
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

    const res = await fetch(`${API_BASE}/api/v1/media`, {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });

    if (res.status === 401) notifyUnauthorized();
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Upload failed");
    }

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
    return this.request<Job>("/api/v1/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tool,
        input_asset_ids: inputAssetIds,
        params_json: paramsJson,
        project_id: projectId,
      }),
    });
  }
}
