"use client";

import React from "react";
import { AudioLines, Clapperboard, FileText, Film, Image as ImageIcon } from "lucide-react";
import { ConversionStatus, MediaFormat } from "@/types";

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
    unavailable: "bg-amber-500/10 text-amber-300 border-amber-500/30",
    coming_soon: "bg-slate-700/30 text-slate-400 border-slate-700",
  };
  const labels: Record<ConversionStatus, string> = {
    available: "Available",
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
