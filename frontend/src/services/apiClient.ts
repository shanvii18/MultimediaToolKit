import { Project, Asset, Job, Conversion } from "@/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Me {
  id: string;
  email: string;
  role: string;
  auth_mode: "access_key" | "dev_open";
}

const ACCESS_KEY_STORAGE = "mtk_access_key";
const ACCESS_KEY_PARAM = "access_key";

/**
 * Invite-only access: a personal invite link (`/?access_key=...`) is opened once.
 * The key is moved into localStorage and removed from the address bar so it is not
 * left in history, bookmarks or screenshots. It is then sent as a Bearer header.
 */
function captureAccessKeyFromUrl(): void {
  if (typeof window === "undefined") return;
  try {
    const url = new URL(window.location.href);
    const key = url.searchParams.get(ACCESS_KEY_PARAM);
    if (key) {
      window.localStorage.setItem(ACCESS_KEY_STORAGE, key.trim());
      url.searchParams.delete(ACCESS_KEY_PARAM);
      window.history.replaceState(window.history.state, "", url.toString());
    }
  } catch (_) {
    // Storage unavailable (private mode / blocked): requests proceed without a key.
  }
}

function getAccessKey(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(ACCESS_KEY_STORAGE);
  } catch (_) {
    return null;
  }
}

function authHeaders(): Record<string, string> {
  const key = getAccessKey();
  return key ? { Authorization: `Bearer ${key}` } : {};
}

captureAccessKeyFromUrl();

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

  // Access keys (invite-only accounts)
  static setAccessKey(key: string): void {
    window.localStorage.setItem(ACCESS_KEY_STORAGE, key.trim());
  }

  static clearAccessKey(): void {
    try {
      window.localStorage.removeItem(ACCESS_KEY_STORAGE);
    } catch (_) {}
  }

  static hasAccessKey(): boolean {
    return !!getAccessKey();
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
