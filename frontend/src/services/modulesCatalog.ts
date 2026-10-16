import { ToolkitModule } from "@/types";

export const TOOLKIT_MODULES: ToolkitModule[] = [
  // Group 1 — Multimedia Conversion & Utilities (01-06)
  {
    id: "01",
    slug: "document-pdf-studio",
    name: "Document & PDF Studio",
    group: "Conversion & Utilities",
    description: "Merge, split, compress, extract pages, and convert supported document formats.",
    status: "integrated",
    statusLabel: "Integrated Utility",
    iconName: "FileText",
    supportedFormats: [".pdf", ".docx", ".txt"],
    route: "/modules/document-pdf-studio",
    blueprintRole: "Conversion & Utilities (Slide 6)",
    targetEndpoint: "/api/v1/documents/process",
    workerEngine: "PyPDF2 / PDFMiner Microservice",
    executionTier: "Free Tier CPU Worker"
  },
  {
    id: "02",
    slug: "image-converter",
    name: "Image Converter",
    group: "Conversion & Utilities",
    description: "Image format conversion, resizing, cropping, and smart compression.",
    status: "integrated",
    statusLabel: "Integrated Utility",
    iconName: "Image",
    supportedFormats: [".png", ".jpg", ".webp", ".svg", ".bmp"],
    route: "/modules/image-converter",
    blueprintRole: "Conversion & Utilities (Slide 6)",
    targetEndpoint: "/api/v1/images/convert",
    workerEngine: "Pillow (PIL) Image Pipeline",
    executionTier: "Free Tier CPU Worker"
  },
  {
    id: "03",
    slug: "audio-converter",
    name: "Audio Converter",
    group: "Conversion & Utilities",
    description: "Audio format conversion, precision trimming, bitrate adjustment, and compression.",
    status: "integrated",
    statusLabel: "Integrated Utility",
    iconName: "Music",
    supportedFormats: [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    route: "/modules/audio-converter",
    blueprintRole: "Conversion & Utilities (Slide 6)",
    targetEndpoint: "/api/v1/audio/convert",
    workerEngine: "FFmpeg Audio Transcoding Engine",
    executionTier: "Container Native FFmpeg"
  },
  {
    id: "04",
    slug: "video-converter",
    name: "Video Converter",
    group: "Conversion & Utilities",
    description: "Video format conversion, resolution downscaling/upscaling, and compression presets.",
    status: "integrated",
    statusLabel: "Integrated Utility",
    iconName: "Video",
    supportedFormats: [".mp4", ".mov", ".mkv", ".webm", ".avi"],
    route: "/modules/video-converter",
    blueprintRole: "Conversion & Utilities (Slide 6)",
    targetEndpoint: "/api/v1/video/transcode",
    workerEngine: "FFmpeg H.264/H.265 Transcoding Engine",
    executionTier: "Container Native FFmpeg"
  },
  {
    id: "05",
    slug: "ocr-text-extraction",
    name: "OCR & Text Extraction",
    group: "Conversion & Utilities",
    description: "Extract editable text from images, scanned documents, and infographics.",
    status: "integrated",
    statusLabel: "Integrated Utility",
    iconName: "ScanText",
    supportedFormats: [".png", ".jpg", ".pdf"],
    route: "/modules/ocr-text-extraction",
    blueprintRole: "Conversion & Utilities (Slide 6)",
    targetEndpoint: "/api/v1/ocr/extract",
    workerEngine: "Tesseract OCR / EasyOCR Runtime",
    executionTier: "Free Tier CPU Worker"
  },
  {
    id: "06",
    slug: "media-extractor",
    name: "Media Extractor",
    group: "Conversion & Utilities",
    description: "Extract lossless audio tracks, keyframes, and metadata inspect specs from video files.",
    status: "operational",
    statusLabel: "Operational (P1 Core)",
    iconName: "FileSpreadsheet",
    supportedFormats: [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    route: "/workspace?tool=media-extractor",
    blueprintRole: "Conversion & Utilities — Core Extractor (Slide 6 & 8)",
    targetEndpoint: "/api/v1/jobs (tool: video_to_audio)",
    workerEngine: "FFmpeg Audio Extraction Adapter",
    executionTier: "Native FFmpeg Active"
  },

  // Group 2 — Audio, Video & Media Understanding (07-10)
  {
    id: "07",
    slug: "speech-to-text",
    name: "Speech-to-Text",
    group: "Audio, Video & Media Understanding",
    description: "Transcribe audio/video speech with accurate timestamps and multi-language support.",
    status: "roadmap",
    statusLabel: "Provider Roadmap",
    iconName: "Mic",
    supportedFormats: [".mp3", ".wav", ".m4a", ".mp4"],
    route: "/modules/speech-to-text",
    blueprintRole: "Media Understanding — Transcription (Slide 7 & 8)",
    targetEndpoint: "/api/v1/jobs (tool: speech_to_text)",
    workerEngine: "OpenAI Whisper / Whisper.cpp Adapter",
    executionTier: "Worker Background Runtime"
  },
  {
    id: "08",
    slug: "subtitle-caption-generator",
    name: "Subtitle & Caption Generator",
    group: "Audio, Video & Media Understanding",
    description: "Create standard SRT/VTT formatted caption files with inline timing review and export.",
    status: "integrated",
    statusLabel: "Integrated Pipeline",
    iconName: "Subtitles",
    supportedFormats: [".mp3", ".mp4", ".srt", ".vtt"],
    route: "/modules/subtitle-caption-generator",
    blueprintRole: "Media Understanding (Slide 7)",
    targetEndpoint: "/api/v1/subtitles/generate",
    workerEngine: "Whisper Timing Synthesizer",
    executionTier: "Worker Background Runtime"
  },
  {
    id: "09",
    slug: "ai-media-understanding",
    name: "AI Media Understanding",
    group: "Audio, Video & Media Understanding",
    description: "Interpret images or clips, generating contextual scene descriptions and visual QA.",
    status: "roadmap",
    statusLabel: "Provider Roadmap",
    iconName: "BrainCircuit",
    supportedFormats: [".png", ".jpg", ".mp4"],
    route: "/modules/ai-media-understanding",
    blueprintRole: "Media Understanding — Vision LLM (Slide 7)",
    targetEndpoint: "/api/v1/understand/vision",
    workerEngine: "Multimodal Vision Model Adapter (OpenAI / Claude / Gemini)",
    executionTier: "Cloud API Provider"
  },
  {
    id: "10",
    slug: "video-summarizer-storyboard",
    name: "Video Summarizer & Storyboard Extractor",
    group: "Audio, Video & Media Understanding",
    description: "Sample keyframes across long video feeds and assemble a structured summary storyboard.",
    status: "roadmap",
    statusLabel: "Roadmap Stage",
    iconName: "Film",
    supportedFormats: [".mp4", ".mov"],
    route: "/modules/video-summarizer-storyboard",
    blueprintRole: "Media Understanding (Slide 7)",
    targetEndpoint: "/api/v1/video/summarize",
    workerEngine: "SceneDetect + Keyframe Extractor + Vision LLM",
    executionTier: "Worker Background Runtime"
  },

  // Group 3 — Generative AI Creative Studio (11-16)
  {
    id: "11",
    slug: "text-to-image",
    name: "Text-to-Image",
    group: "Generative AI Creative Studio",
    description: "Synthesize high-fidelity visual artwork and production assets from textual briefs.",
    status: "integrated",
    statusLabel: "Provider Adapter",
    iconName: "Sparkles",
    supportedFormats: [".png", ".jpg", ".webp"],
    route: "/modules/text-to-image",
    blueprintRole: "Generative Creative Studio (Slide 7)",
    targetEndpoint: "/api/v1/generate/image",
    workerEngine: "Stable Diffusion XL / SD-Turbo Adapter",
    executionTier: "Cloud GPU Worker"
  },
  {
    id: "12",
    slug: "text-to-video",
    name: "Text-to-Video",
    group: "Generative AI Creative Studio",
    description: "Generate video sequences from detailed narrative prompts via generative video engines.",
    status: "roadmap",
    statusLabel: "Cloud Roadmap",
    iconName: "Clapperboard",
    supportedFormats: [".mp4"],
    route: "/modules/text-to-video",
    blueprintRole: "Generative Creative Studio (Slide 7)",
    targetEndpoint: "/api/v1/generate/video",
    workerEngine: "CogVideoX / Runway Gen-3 Cloud Adapter",
    executionTier: "Cloud GPU Infrastructure"
  },
  {
    id: "13",
    slug: "image-to-video",
    name: "Image-to-Video / Animation",
    group: "Generative AI Creative Studio",
    description: "Animate still images into fluid cinematic camera moves with motion controls.",
    status: "roadmap",
    statusLabel: "Cloud Roadmap",
    iconName: "PlayCircle",
    supportedFormats: [".png", ".jpg", ".mp4"],
    route: "/modules/image-to-video",
    blueprintRole: "Generative Creative Studio (Slide 7)",
    targetEndpoint: "/api/v1/animate/image",
    workerEngine: "Stable Video Diffusion (SVD) Adapter",
    executionTier: "Cloud GPU Infrastructure"
  },
  {
    id: "14",
    slug: "video-to-animation",
    name: "Video-to-Animation / Restyling",
    group: "Generative AI Creative Studio",
    description: "Apply artistic styles, anime filters, and 3D restyling across video sequences.",
    status: "roadmap",
    statusLabel: "Advanced Roadmap",
    iconName: "Palette",
    supportedFormats: [".mp4"],
    route: "/modules/video-to-animation",
    blueprintRole: "Generative Creative Studio (Slide 7)",
    targetEndpoint: "/api/v1/restyle/video",
    workerEngine: "ControlNet / AnimateDiff Pipeline",
    executionTier: "Cloud GPU Infrastructure"
  },
  {
    id: "15",
    slug: "voice-text-to-speech",
    name: "Voice & Text-to-Speech",
    group: "Generative AI Creative Studio",
    description: "Convert written script into expressive natural speech with voice timbre selection.",
    status: "integrated",
    statusLabel: "Integrated Engine",
    iconName: "Volume2",
    supportedFormats: [".mp3", ".wav"],
    route: "/modules/voice-text-to-speech",
    blueprintRole: "Generative Creative Studio (Slide 7)",
    targetEndpoint: "/api/v1/speech/synthesize",
    workerEngine: "Edge-TTS / Coqui TTS Adapter",
    executionTier: "Free Tier CPU Worker"
  },
  {
    id: "16",
    slug: "thumbnail-creative-assets",
    name: "Thumbnail & Creative Asset Generator",
    group: "Generative AI Creative Studio",
    description: "Generate click-worthy thumbnail designs, punchy titles, and branded assets.",
    status: "integrated",
    statusLabel: "Integrated Studio",
    iconName: "Layers",
    supportedFormats: [".png", ".jpg"],
    route: "/modules/thumbnail-creative-assets",
    blueprintRole: "Generative Creative Studio (Slide 7)",
    targetEndpoint: "/api/v1/generate/thumbnail",
    workerEngine: "Canvas Compositor + Generative Infill",
    executionTier: "Free Tier CPU Worker"
  },

  // Group 4 — Idea-to-Content Workflow (17-18)
  {
    id: "17",
    slug: "idea-to-storyboard",
    name: "Idea-to-Storyboard Studio",
    group: "Idea-to-Content Workflow",
    description: "Transform raw ideas or briefs into multi-scene cinematic storyboards with camera cues.",
    status: "operational",
    statusLabel: "Operational (P2 Demo)",
    iconName: "Wand2",
    supportedFormats: [".txt", ".json"],
    route: "/workspace?tool=idea-to-storyboard",
    blueprintRole: "Idea-to-Content Workflow (Slide 8)",
    targetEndpoint: "/api/v1/jobs (tool: idea_to_storyboard)",
    workerEngine: "Contextual Directorial Heuristic Engine v2",
    executionTier: "Native Backend Active"
  },
  {
    id: "18",
    slug: "multistep-creation-pipeline",
    name: "Multi-Step Creation Pipeline",
    group: "Idea-to-Content Workflow",
    description: "Chain multimodal stages into an automated sequential pipeline from prompt to final package.",
    status: "integrated",
    statusLabel: "Workflow Orchestrator",
    iconName: "Workflow",
    supportedFormats: [".json"],
    route: "/modules/multistep-creation-pipeline",
    blueprintRole: "Idea-to-Content Workflow (Slide 8)",
    targetEndpoint: "/api/v1/pipelines/execute",
    workerEngine: "DAG Workflow Orchestrator Runtime",
    executionTier: "Worker Background Runtime"
  },

  // Group 5 — Workspace & Delivery (19-20)
  {
    id: "19",
    slug: "project-workspace-media-library",
    name: "Project Workspace & Media Library",
    group: "Workspace & Delivery",
    description: "Organize projects, assets, uploaded files, and generated outputs in one place.",
    status: "operational",
    statusLabel: "Operational (P0 Foundation)",
    iconName: "FolderKanban",
    supportedFormats: ["*"],
    route: "/projects",
    blueprintRole: "Workspace & Delivery (Slide 9)",
    targetEndpoint: "/api/v1/projects & /api/v1/assets",
    workerEngine: "PostgreSQL / SQLite Storage Engine",
    executionTier: "Database Service Active"
  },
  {
    id: "20",
    slug: "job-monitor-export-center",
    name: "Job Monitor & Export Center",
    group: "Workspace & Delivery",
    description: "Track queue execution, worker states, error details, and download completed artifacts.",
    status: "operational",
    statusLabel: "Operational (P0 Foundation)",
    iconName: "Activity",
    supportedFormats: ["*"],
    route: "/jobs",
    blueprintRole: "Workspace & Delivery (Slide 9)",
    targetEndpoint: "/api/v1/jobs & /api/v1/assets/{id}/download",
    workerEngine: "Background Task Queue & File Delivery",
    executionTier: "Background Task Engine Active"
  }
];

export function getModuleRoute(module: ToolkitModule): string {
  if (module.route) return module.route;
  if (module.status === "operational") {
    if (module.slug === "media-extractor") return "/workspace?tool=media-extractor";
    if (module.slug === "idea-to-storyboard") return "/workspace?tool=idea-to-storyboard";
    if (module.slug === "project-workspace-media-library") return "/projects";
    if (module.slug === "job-monitor-export-center") return "/jobs";
  }
  return `/modules/${module.slug}`;
}

export function getModuleBySlug(slug: string): ToolkitModule | undefined {
  return TOOLKIT_MODULES.find((m) => m.slug === slug);
}
