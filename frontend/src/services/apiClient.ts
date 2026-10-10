import { Project, Asset, Job } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiClient {
  private static async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      ...options.headers,
    };

    const res = await fetch(url, { ...options, headers });
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
    return res.json() as Promise<T>;
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
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Upload failed");
    }

    return res.json() as Promise<Asset>;
  }

  static getDownloadUrl(assetId: string): string {
    return `${API_BASE}/api/v1/assets/${assetId}/download`;
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
