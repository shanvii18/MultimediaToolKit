"use client";

import React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Sparkles,
  Server,
  Layers,
  Cpu,
  FileCode,
  ShieldCheck,
  AlertTriangle,
  Play,
  CheckCircle2,
  Clock,
  ExternalLink,
} from "lucide-react";
import { getModuleBySlug, TOOLKIT_MODULES } from "@/services/modulesCatalog";

export default function ModuleDetailPage() {
  const params = useParams();
  const slug = Array.isArray(params?.slug) ? params.slug[0] : (params?.slug as string);
  const toolkitModule = getModuleBySlug(slug);

  if (!toolkitModule) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-6">
        <Link
          href="/modules"
          className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to 20 Modules Directory</span>
        </Link>

        <div className="p-10 rounded-3xl bg-slate-900/60 border border-slate-800 text-center space-y-4 shadow-xl">
          <AlertTriangle className="h-12 w-12 text-amber-400 mx-auto" />
          <h1 className="text-2xl font-bold text-white">Module Not Found</h1>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            The requested module slug <span className="font-mono text-orange-400 font-semibold">&ldquo;{slug}&rdquo;</span> does not
            match any of the 20 blueprints defined in MultimediaToolKit.
          </p>
          <div className="pt-4">
            <Link
              href="/modules"
              className="px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-xs font-semibold inline-flex items-center gap-2 transition-colors"
            >
              <span>Explore All 20 Modules</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isOperational = toolkitModule.status === "operational";

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Navigation breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          href="/modules"
          className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to 20 Modules Directory</span>
        </Link>
        <span className="font-mono text-xs text-slate-500">BLUEPRINT ID: #{toolkitModule.id}</span>
      </div>

      {/* Module Title Card */}
      <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-md bg-orange-500/10 text-orange-400 border border-orange-500/20">
                MODULE #{toolkitModule.id}
              </span>
              <span
                className={`text-xs font-mono px-3 py-1 rounded-md border ${
                  isOperational
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : toolkitModule.status === "integrated"
                    ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                    : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                }`}
              >
                {toolkitModule.statusLabel}
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">{toolkitModule.name}</h1>
            <p className="text-xs text-slate-400 font-medium">{toolkitModule.group}</p>
          </div>

          <div>
            {isOperational ? (
              <Link
                href={toolkitModule.route || "/workspace"}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-medium text-sm inline-flex items-center gap-2 shadow-lg shadow-orange-500/25 transition-all"
              >
                <Play className="h-4 w-4" />
                <span>Launch Operational Tool</span>
              </Link>
            ) : (
              <div className="px-4 py-2 rounded-xl bg-slate-800/80 border border-slate-700/80 text-xs font-mono text-slate-300 flex items-center gap-2">
                <Clock className="h-3.5 w-3.5 text-amber-400" />
                <span>Roadmap Stage (Coming Soon)</span>
              </div>
            )}
          </div>
        </div>

        <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">{toolkitModule.description}</p>
      </div>

      {/* Honest Architectural Status Banner */}
      {!isOperational && (
        <div className="p-6 rounded-2xl bg-amber-950/20 border border-amber-800/40 space-y-3">
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
            <ShieldCheck className="h-4 w-4" />
            <span>Honest Engineering Notice — Zero Fake Success</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            In strict compliance with MultimediaToolKit engineering standards, this module does{" "}
            <strong>not</strong> fabricate fake progress bars, synthetic mock data, or pretend to execute cloud
            pipelines. The production specifications below detail the exact target architecture scheduled for worker
            container deployments.
          </p>
        </div>
      )}

      {/* Technical Specifications Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Specification 1: Blueprint Role */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-orange-400">
            <Layers className="h-4 w-4" />
            <h3 className="font-bold text-sm text-white">Blueprint Role & Lifecycle</h3>
          </div>
          <p className="text-xs text-slate-300 font-mono">
            {toolkitModule.blueprintRole || "Multimedia Transformation Pipeline"}
          </p>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Directly mapped from the authoritative PPT specification. Formats and protocols conform to the unified
            pipeline: IDEA → UNDERSTAND → CREATE → POLISH → DELIVER.
          </p>
        </div>

        {/* Specification 2: Worker Engine */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-amber-400">
            <Cpu className="h-4 w-4" />
            <h3 className="font-bold text-sm text-white">Worker & Processing Engine</h3>
          </div>
          <p className="text-xs text-slate-300 font-mono">
            {toolkitModule.workerEngine || "FastAPI Asynchronous Worker Adapter"}
          </p>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Target execution environment:{" "}
            <span className="text-amber-300 font-mono">{toolkitModule.executionTier || "Worker Runtime"}</span>. Designed to
            run as non-blocking background tasks or standalone Redis queue workers.
          </p>
        </div>

        {/* Specification 3: Target API Endpoint */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-blue-400">
            <Server className="h-4 w-4" />
            <h3 className="font-bold text-sm text-white">Target REST API Route</h3>
          </div>
          <code className="text-xs text-emerald-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 block font-mono">
            {toolkitModule.targetEndpoint || "/api/v1/jobs"}
          </code>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Registered in the FastAPI v1 specification. Asynchronous task state is stored with standard status
            transitions: <code className="text-slate-300">queued → running → succeeded / failed</code>.
          </p>
        </div>

        {/* Specification 4: Formats & Payload */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400">
            <FileCode className="h-4 w-4" />
            <h3 className="font-bold text-sm text-white">Supported Formats & Payloads</h3>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {toolkitModule.supportedFormats && toolkitModule.supportedFormats.length > 0 ? (
              toolkitModule.supportedFormats.map((fmt) => (
                <span
                  key={fmt}
                  className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800"
                >
                  {fmt}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500 font-mono">Textual / Multimodal Prompts</span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Storage handled by the SHA-256 StorageService with path traversal sanitization and 100MB upload limits.
          </p>
        </div>
      </div>

      {/* Ready-to-use Operational Modules Section */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-orange-400" />
          <span>Currently Operational Tools Ready to Execute</span>
        </h3>
        <p className="text-xs text-slate-400">
          The following core modules are fully operational today with genuine test coverage:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
          <Link
            href="/workspace?tool=media-extractor"
            className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-orange-500/40 hover:bg-slate-900 transition-colors space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-orange-400 font-bold">#06</span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Operational
              </span>
            </div>
            <h4 className="text-xs font-bold text-white">Media Extractor</h4>
            <p className="text-[11px] text-slate-400">Native FFmpeg video-to-audio MP3 extraction & download.</p>
          </Link>

          <Link
            href="/workspace?tool=idea-to-storyboard"
            className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-orange-500/40 hover:bg-slate-900 transition-colors space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-orange-400 font-bold">#17</span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Operational
              </span>
            </div>
            <h4 className="text-xs font-bold text-white">Storyboard Studio</h4>
            <p className="text-[11px] text-slate-400">Structured multi-scene directorial generation with JSON export.</p>
          </Link>

          <Link
            href="/projects"
            className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-orange-500/40 hover:bg-slate-900 transition-colors space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-orange-400 font-bold">#19</span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Operational
              </span>
            </div>
            <h4 className="text-xs font-bold text-white">Projects & Assets</h4>
            <p className="text-[11px] text-slate-400">Workspace management, asset storage and file persistence.</p>
          </Link>

          <Link
            href="/jobs"
            className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-orange-500/40 hover:bg-slate-900 transition-colors space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-orange-400 font-bold">#20</span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Operational
              </span>
            </div>
            <h4 className="text-xs font-bold text-white">Job Monitor</h4>
            <p className="text-[11px] text-slate-400">Live task tracking, progress monitoring, and output downloads.</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
