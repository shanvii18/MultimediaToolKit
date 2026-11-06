"use client";

import React from "react";
import { AudioLines, Clapperboard, FileText, Film, Image as ImageIcon } from "lucide-react";
import { ModeKind, ConversionStatus, MediaFormat } from "@/types";

export const FORMAT_LABELS: Record<MediaFormat, string> = {
  text: "Text",
  image: "Image",
  audio: "Audio",
  video: "Video",
  animation: "Animation",
};

export function FormatIcon({ format, className }: { format: MediaFormat; className?: string }) {
  switch (format) {
    case "text":
      return <FileText className={className} />;
    case "image":
      return <ImageIcon className={className} />;
    case "audio":
      return <AudioLines className={className} />;
    case "video":
      return <Film className={className} />;
    default:
      return <Clapperboard className={className} />;
  }
}

export function StatusBadge({ status, reason }: { status: ConversionStatus; reason?: string | null }) {
  const styles: Record<ConversionStatus, string> = {
    available: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
    temporarily_unavailable: "bg-orange-500/10 text-orange-300 border-orange-500/30",
    needs_config: "bg-sky-500/10 text-sky-300 border-sky-500/30",
    unavailable: "bg-amber-500/10 text-amber-300 border-amber-500/30",
    coming_soon: "bg-slate-700/30 text-slate-400 border-slate-700",
  };
  const labels: Record<ConversionStatus, string> = {
    available: "Available",
    temporarily_unavailable: "Temporarily unavailable",
    needs_config: "Configuration required",
    unavailable: "Engine not installed",
    coming_soon: "Coming soon",
  };
  return (
    <span
      title={reason || undefined}
      className={`inline-flex items-center px-2 py-0.5 rounded-md border text-[11px] font-medium ${styles[status]}`}
    >
      {labels[status]}
    </span>
  );
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function KindBadge({ kind }: { kind: ModeKind }) {
  const map: Record<ModeKind, [string, string, string]> = {
    ai_provider: ["AI provider", "border-violet-500/40 bg-violet-500/10 text-violet-300", "Runs on a hosted AI model"],
    ai_local: ["AI model · server", "border-indigo-500/40 bg-indigo-500/10 text-indigo-300", "Neural model running on the server CPU"],
    cpu: ["CPU", "border-slate-700 text-slate-400", "Deterministic processing (no generative AI)"],
  };
  const [label, cls, title] = map[kind] || map.cpu;
  return (
    <span title={title} className={`px-1.5 py-0.5 rounded border text-[10px] font-semibold ${cls}`}>
      {label}
    </span>
  );
}
