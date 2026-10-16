export type ModuleGroup =
  | "Conversion & Utilities"
  | "Audio, Video & Media Understanding"
  | "Generative AI Creative Studio"
  | "Idea-to-Content Workflow"
  | "Workspace & Delivery";

export type ModuleStatus = "operational" | "integrated" | "roadmap";

export interface ToolkitModule {
  id: string; // 01 to 20
  slug: string;
  name: string;
  group: ModuleGroup;
  description: string;
  status: ModuleStatus;
  statusLabel: string;
  iconName: string;
  supportedFormats?: string[];
  route?: string;
  blueprintRole?: string;
  targetEndpoint?: string;
  workerEngine?: string;
  executionTier?: string;
}

export interface Project {
  id: string;
  owner_id?: string;
  title: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: string;
  project_id?: string;
  owner_id?: string;
  filename: string;
  media_type: string;
  size: number;
  checksum?: string;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface JobOutput {
  id: string;
  job_id: string;
  asset_id: string;
  output_type: string;
  created_at: string;
  asset?: Asset;
}

export interface Job {
  id: string;
  project_id?: string;
  user_id?: string;
  tool: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  progress: number;
  input_asset_ids: string[];
  params_json: Record<string, any>;
  error_code?: string;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  outputs?: JobOutput[];
}
