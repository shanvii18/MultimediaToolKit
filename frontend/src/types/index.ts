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

export type MediaFormat = "text" | "image" | "audio" | "video" | "animation";
export type ConversionStatus = "available" | "unavailable" | "coming_soon";

export interface ConversionParam {
  name: string;
  label: string;
  type: "select" | "number" | "boolean" | "text" | "textarea";
  default: any;
  choices: { value: string; label: string }[] | null;
  min: number | null;
  max: number | null;
  step: number | null;
  max_length: number | null;
  help: string;
  modes: string[] | null;
}

export interface ConversionMode {
  id: string;
  label: string;
  description: string;
  status: ConversionStatus;
  reason: string | null;
  engines: string[];
}

export interface Conversion {
  id: string;
  source: MediaFormat;
  target: MediaFormat;
  title: string;
  description: string;
  category: "normal" | "generative" | "workflow";
  status: ConversionStatus;
  input_kind: "file" | "text" | "file_or_text";
  accepted_extensions: string[];
  modes: ConversionMode[];
  params: ConversionParam[];
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
  /** Short-lived signed download path (relative to the API base URL). */
  download_url?: string;
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
  progress_message?: string | null;
  input_asset_ids: string[];
  params_json: Record<string, any>;
  error_code?: string;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  outputs?: JobOutput[];
}
