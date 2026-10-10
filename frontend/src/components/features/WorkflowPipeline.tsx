"use client";

import React, { useState } from "react";
import {
  Video,
  FileAudio,
  Image as ImageIcon,
  FileText,
  Cpu,
  Sparkles,
  ArrowRight,
  Layers,
  CheckCircle2,
} from "lucide-react";

interface WorkflowPipelineProps {
  onOpenUpload: () => void;
}

export function WorkflowPipeline({ onOpenUpload }: WorkflowPipelineProps) {
  const [selectedFormatIndex, setSelectedFormatIndex] = useState(0);

  const formats = [
    {
      title: "Video Recordings",
      formats: "MP4, MOV, MKV",
      icon: Video,
      color: "text-stripe-orange",
      bg: "bg-stripe-orange/10",
      accent: "from-stripe-orange to-stripe-coral",
      pipelineRole: "Lossless audio demuxing & keyframe timeline extraction",
      outputKey: "Isolated audio stream & video-synced playback stamps",
    },
    {
      title: "Audio Streams",
      formats: "WAV, MP3, M4A",
      icon: FileAudio,
      color: "text-stripe-coral",
      bg: "bg-stripe-coral/10",
      accent: "from-stripe-coral to-stripe-pink",
      pipelineRole: "Acoustic frequency modeling & Whisper token transcription",
      outputKey: "Timestamp-indexed speech script with speaker diarization",
    },
    {
      title: "Document Images",
      formats: "PNG, JPG, HEIC",
      icon: ImageIcon,
      color: "text-stripe-pink",
      bg: "bg-stripe-pink/10",
      accent: "from-stripe-pink to-stripe-magenta",
      pipelineRole: "Deskew, denoise, and Tesseract optical character parsing",
      outputKey: "Structured markdown notes with math LaTeX formulas",
    },
    {
      title: "Lecture Slides & PDFs",
      formats: "PDF, Presentations",
      icon: FileText,
      color: "text-stripe-violet",
      bg: "bg-stripe-violet/10",
      accent: "from-stripe-magenta to-stripe-violet",
      pipelineRole: "Multi-column layout detection and table row parsing",
      outputKey: "Exam practice questions and active recall flashcards",
    },
  ];

  const current = formats[selectedFormatIndex];

  return (
    <section id="workflow" className="relative py-24 md:py-32 overflow-hidden border-y border-slate-200/80 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40">
      {/* Radiant Background Field */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[850px] h-[450px] bg-gradient-to-r from-stripe-orange/15 via-stripe-coral/20 to-stripe-pink/15 blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header with refined typography matching Screenshot 1 */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-stripe-orange/10 text-stripe-orange border border-stripe-orange/20 mb-3">
            <Layers className="w-3.5 h-3.5" />
            <span>Unified Processing Pipeline</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-[-0.03em] text-slate-900 dark:text-white">
            How raw multimedia transforms into intelligence.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-slate-600 dark:text-slate-300 font-normal">
            A single, continuous pipeline that takes any visual, auditory, or document input,
            extracts the core signal, and outputs immediately actionable study units.
          </p>
        </div>

        {/* Interactive End-to-End Pipeline Composition */}
        <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl p-6 sm:p-10 relative overflow-hidden">
          {/* Top Format Selector Ribbon */}
          <div className="flex items-center justify-between pb-6 border-b border-slate-100 dark:border-slate-800 mb-8 overflow-x-auto">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 shrink-0 mr-4">
              Select Input Media:
            </span>
            <div className="flex items-center gap-2 min-w-max">
              {formats.map((fmt, idx) => {
                const Icon = fmt.icon;
                const isSelected = selectedFormatIndex === idx;
                return (
                  <button
                    key={fmt.title}
                    onClick={() => setSelectedFormatIndex(idx)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all cursor-pointer ${
                      isSelected
                        ? "bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-sm scale-[1.02]"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isSelected ? "text-stripe-orange" : fmt.color}`} />
                    <span>{fmt.title}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Connected 3-Stage Pipeline Diagram */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Stage 1: Selected Ingestion Source (Col 1-4) */}
            <div className="lg:col-span-4 p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/70 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-stripe-orange bg-stripe-orange/10 px-2 py-0.5 rounded-full">
                  Stage 01 • Ingestion
                </span>
                <span className="text-xs font-mono text-slate-400">
                  {current.formats}
                </span>
              </div>

              <div className="flex items-center gap-3 pt-1">
                <div className={`w-12 h-12 rounded-xl ${current.bg} ${current.color} flex items-center justify-center font-bold shadow-sm`}>
                  {React.createElement(current.icon, { className: "w-6 h-6" })}
                </div>
                <div>
                  <h4 className="text-base font-semibold text-slate-900 dark:text-white">
                    {current.title}
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Auto-detected container stream
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300">
                <span className="font-semibold text-slate-900 dark:text-white block mb-1">
                  Ingestion Rule:
                </span>
                Zero pre-transcoding needed. Supports multi-gigabyte recordings and high-res camera captures.
              </div>
            </div>

            {/* Central Animated Pipeline Core (Col 5-8) */}
            <div className="lg:col-span-4 flex flex-col items-center justify-center p-4 text-center relative">
              {/* Animated Connector Beam */}
              <div className="hidden lg:block absolute inset-x-0 top-1/2 -translate-y-1/2 h-1 bg-gradient-to-r from-stripe-orange via-stripe-coral to-stripe-pink opacity-50 -z-0" />

              <div className="w-30 h-30 rounded-full p-1 bg-gradient-to-br from-stripe-orange via-stripe-coral to-stripe-pink shadow-xl relative z-10 flex items-center justify-center animate-pulse-subtle">
                <div className="w-full h-full rounded-full bg-slate-950 dark:bg-slate-900 flex flex-col items-center justify-center p-3 text-white">
                  <Cpu className="w-7 h-7 text-stripe-orange animate-spin [animation-duration:14s] mb-1" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">
                    MTK Engine
                  </span>
                  <span className="text-[8px] text-stripe-amber font-mono">
                    FastAPI + Python
                  </span>
                </div>
              </div>

              <div className="mt-4 relative z-10">
                <h5 className="text-xs font-semibold text-slate-900 dark:text-white">
                  {current.pipelineRole}
                </h5>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full mt-1.5">
                  <CheckCircle2 className="w-3 h-3" /> Asynchronous Worker Queue
                </span>
              </div>
            </div>

            {/* Stage 3: Synthesized Output (Col 9-12) */}
            <div className="lg:col-span-4 p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/70 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-stripe-pink bg-stripe-pink/10 px-2 py-0.5 rounded-full">
                  Stage 02 • Output Hub
                </span>
                <span className="text-xs font-mono text-emerald-500">
                  Ready to Study
                </span>
              </div>

              <div className="flex items-center gap-3 pt-1">
                <div className="w-12 h-12 rounded-xl bg-stripe-pink/10 text-stripe-pink flex items-center justify-center font-bold shadow-sm">
                  <Sparkles className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-base font-semibold text-slate-900 dark:text-white">
                    Actionable Knowledge
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Synced with original timestamps
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300">
                <span className="font-semibold text-slate-900 dark:text-white block mb-1">
                  Generated Assets:
                </span>
                {current.outputKey}
              </div>
            </div>
          </div>

          {/* Bottom Callout Bar */}
          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Want to see this pipeline handle your actual course files?
            </span>
            <button
              onClick={onOpenUpload}
              className="px-5 py-2.5 rounded-lg text-xs font-medium text-white bg-gradient-to-r from-stripe-orange to-stripe-coral hover:brightness-105 transition-all shadow-md flex items-center gap-2 cursor-pointer"
            >
              <span>Test with an upload</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
