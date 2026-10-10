"use client";

import React, { useState } from "react";
import { AudioWaveform } from "@/components/ui/AudioWaveform";
import {
  Folder,
  Video,
  FileAudio,
  FileText,
  Search,
  UploadCloud,
  CheckCircle2,
  ChevronRight,
  Play,
  Volume2,
  Sparkles,
} from "lucide-react";

interface WorkspaceShowcaseProps {
  onOpenUpload: () => void;
}

export function WorkspaceShowcase({ onOpenUpload }: WorkspaceShowcaseProps) {
  const [activeTab, setActiveTab] = useState<"transcript" | "notes">("transcript");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFileId, setSelectedFileId] = useState(1);
  const [isPlayingAudio, setIsPlayingAudio] = useState(true);

  const files = [
    {
      id: 1,
      title: "Lecture_04_Neural_Optimization.mp4",
      type: "video",
      size: "428 MB",
      date: "12 mins ago",
      status: "Ready",
      duration: "45:12",
    },
    {
      id: 2,
      title: "Prof_Karp_Office_Hours.m4a",
      type: "audio",
      size: "34 MB",
      date: "2 hours ago",
      status: "Ready",
      duration: "28:40",
    },
    {
      id: 3,
      title: "Whiteboard_Backpropagation.png",
      type: "image",
      size: "4.8 MB",
      date: "Yesterday",
      status: "Ready",
      duration: "OCR 99%",
    },
    {
      id: 4,
      title: "Transformers_Attention.mp4",
      type: "video",
      size: "612 MB",
      date: "3 days ago",
      status: "Ready",
      duration: "58:04",
    },
  ];

  const transcriptLines = [
    { time: "00:02:15", speaker: "Prof. Karp", text: "Today we will analyze how loss surfaces behave under stochastic gradient conditions." },
    { time: "00:04:40", speaker: "Prof. Karp", text: "When batches are small, gradient noise acts as implicit regularization, helping bypass saddle points." },
    { time: "00:08:12", speaker: "Student", text: "Does learning rate warmup prevent early divergence in deep networks?" },
    { time: "00:08:35", speaker: "Prof. Karp", text: "Precisely. Warmup stabilizes variance before momentum accumulates in weight tensors." },
    { time: "00:14:20", speaker: "Prof. Karp", text: "Notice how learning curves flatten without adaptive gradient updates like AdamW." },
  ];

  const filteredTranscripts = transcriptLines.filter((line) =>
    line.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <section id="workspace-preview" className="relative py-24 md:py-32 overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-gradient-to-tr from-stripe-orange/15 via-stripe-coral/10 to-stripe-pink/15 blur-[140px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header matching Screenshot 1 editorial typography */}
        <div className="text-center max-w-3xl mx-auto mb-12 md:mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-stripe-orange/10 text-stripe-orange border border-stripe-orange/20 mb-3">
            <span>Interactive Studio Mockup</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-[-0.03em] text-slate-900 dark:text-white">
            Designed for clarity. Built for depth.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-slate-600 dark:text-slate-300 font-normal">
            A cohesive environment where raw recordings, high-resolution audio extractions,
            searchable transcripts, and synthesized study materials live in lockstep.
          </p>
        </div>

        {/* Browser-Like Frame Mockup */}
        <div className="rounded-2xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl overflow-hidden transition-all duration-300">
          {/* Top Window Chrome */}
          <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex items-center justify-between">
            {/* macOS-style Traffic Lights */}
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-400/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-amber-400/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-emerald-400/80 inline-block" />
              <span className="ml-3 text-xs font-mono text-slate-400 hidden sm:inline-block">
                app.multimediatoolkit.local/workspace/cs482
              </span>
            </div>

            {/* Breadcrumb */}
            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-normal">
              <span>MultimediaToolKit</span>
              <ChevronRight className="w-3 h-3 text-slate-400" />
              <span>Workspace</span>
              <ChevronRight className="w-3 h-3 text-slate-400" />
              <span className="text-slate-900 dark:text-white font-medium">
                Lecture 04
              </span>
            </div>

            {/* Window Right Action */}
            <div className="flex items-center gap-2">
              <button
                onClick={onOpenUpload}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-gradient-to-r from-stripe-orange to-stripe-coral text-white hover:brightness-105 transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Upload New</span>
              </button>
            </div>
          </div>

          {/* Studio Workspace Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[580px]">
            {/* Left Sidebar (Col 1-3) */}
            <div className="lg:col-span-3 border-r border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 p-4 space-y-6">
              {/* Library Navigation */}
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 px-2 block mb-2">
                  Library Navigation
                </span>
                <nav className="space-y-1">
                  <button className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg bg-stripe-orange/10 text-stripe-orange transition-colors text-left cursor-pointer">
                    <Folder className="w-4 h-4" />
                    <span>CS482: Deep Learning</span>
                  </button>
                  <button className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-normal text-slate-600 dark:text-slate-400 hover:text-slate-950 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-900 rounded-lg transition-colors text-left cursor-pointer">
                    <Folder className="w-4 h-4 text-slate-400" />
                    <span>BIO201: Genetics</span>
                  </button>
                  <button className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-normal text-slate-600 dark:text-slate-400 hover:text-slate-950 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-900 rounded-lg transition-colors text-left cursor-pointer">
                    <Folder className="w-4 h-4 text-slate-400" />
                    <span>PHYS110: Mechanics</span>
                  </button>
                </nav>
              </div>

              {/* Upload Drop Target Zone */}
              <div
                onClick={onOpenUpload}
                className="border-2 border-dashed border-slate-200 dark:border-slate-800 hover:border-stripe-orange dark:hover:border-stripe-orange rounded-xl p-4 text-center cursor-pointer transition-colors bg-white dark:bg-slate-900/60"
              >
                <UploadCloud className="w-6 h-6 mx-auto text-stripe-orange mb-2" />
                <p className="text-xs font-medium text-slate-900 dark:text-white">
                  Add files to library
                </p>
                <p className="text-[10px] text-slate-400 mt-1">
                  Click to open upload dialog
                </p>
              </div>

              {/* Recent Files in Folder */}
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 px-2 block mb-2">
                  Folder Files ({files.length})
                </span>
                <div className="space-y-1.5">
                  {files.map((file) => (
                    <div
                      key={file.id}
                      onClick={() => setSelectedFileId(file.id)}
                      className={`p-2.5 rounded-xl cursor-pointer text-xs transition-all border ${
                        selectedFileId === file.id
                          ? "border-stripe-orange/40 bg-stripe-orange/5 dark:bg-stripe-orange/10 text-stripe-orange"
                          : "border-transparent hover:border-slate-200 dark:hover:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-900"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {file.type === "video" ? (
                          <Video className="w-4 h-4 text-stripe-orange shrink-0" />
                        ) : file.type === "audio" ? (
                          <FileAudio className="w-4 h-4 text-stripe-coral shrink-0" />
                        ) : (
                          <FileText className="w-4 h-4 text-stripe-cyan shrink-0" />
                        )}
                        <span className="font-medium truncate text-slate-900 dark:text-white">
                          {file.title}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center justify-between text-[10px] text-slate-400">
                        <span>{file.size}</span>
                        <span>{file.duration}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Middle Media Inspector (Col 4-8) */}
            <div className="lg:col-span-5 border-r border-slate-200 dark:border-slate-800 p-5 space-y-5 bg-white dark:bg-slate-900">
              {/* Media Player Card */}
              <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 relative aspect-video flex items-center justify-center">
                <div className="absolute inset-0 bg-gradient-to-tr from-slate-950 via-slate-900/60 to-stripe-orange/20" />
                <div
                  onClick={() => setIsPlayingAudio(!isPlayingAudio)}
                  className="w-12 h-12 rounded-full bg-white/20 border border-white/40 backdrop-blur-md flex items-center justify-center text-white cursor-pointer hover:scale-105 transition-transform z-10 shadow-lg"
                >
                  <Play className="w-5 h-5 fill-white ml-0.5" />
                </div>
                {/* Overlay Indicators */}
                <div className="absolute top-3 left-3 px-2 py-1 rounded bg-black/70 text-white font-mono text-[10px] backdrop-blur">
                  00:14:32 / 00:45:12
                </div>
                <div className="absolute top-3 right-3 flex items-center gap-1.5">
                  <span className="px-2 py-0.5 rounded bg-emerald-500/80 text-white text-[10px] font-medium">
                    1080p
                  </span>
                </div>
                {/* Audio Sync Waveform Line with LIVE AudioWaveform Component */}
                <div className="absolute bottom-0 inset-x-0 h-11 bg-slate-950/85 backdrop-blur border-t border-white/10 px-4 flex items-center gap-2">
                  <Volume2 className="w-3.5 h-3.5 text-stripe-orange shrink-0" />
                  <div className="flex-1">
                    <AudioWaveform
                      isPlaying={isPlayingAudio}
                      barCount={30}
                      heightClass="h-6"
                      colorScheme="orange-coral"
                    />
                  </div>
                </div>
              </div>

              {/* Media File Details */}
              <div className="p-4 rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-950/50">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                    Lecture_04_Neural_Optimization.mp4
                  </h4>
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3 h-3" /> Ready
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs mt-3">
                  <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400">Audio Track</div>
                    <div className="font-semibold text-slate-900 dark:text-white mt-0.5">AAC 48kHz</div>
                  </div>
                  <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400">Transcript</div>
                    <div className="font-semibold text-stripe-orange mt-0.5">8,420 words</div>
                  </div>
                  <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400">Study Units</div>
                    <div className="font-semibold text-stripe-coral mt-0.5">6 modules</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Pane: Searchable Transcript & Intelligent Outputs (Col 9-12) */}
            <div className="lg:col-span-4 p-5 flex flex-col justify-between bg-white dark:bg-slate-900">
              <div>
                {/* Tab Switcher */}
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3 mb-4">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setActiveTab("transcript")}
                      className={`text-xs font-medium pb-1 transition-colors relative cursor-pointer ${
                        activeTab === "transcript"
                          ? "text-stripe-orange border-b-2 border-stripe-orange"
                          : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                      }`}
                    >
                      Transcript
                    </button>
                    <button
                      onClick={() => setActiveTab("notes")}
                      className={`text-xs font-medium pb-1 transition-colors relative cursor-pointer ${
                        activeTab === "notes"
                          ? "text-stripe-orange border-b-2 border-stripe-orange"
                          : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                      }`}
                    >
                      Study Notes
                    </button>
                  </div>

                  <span className="text-[10px] text-slate-400 font-mono">
                    Synced 14:32
                  </span>
                </div>

                {/* Search Bar */}
                <div className="relative mb-3">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search speech timestamps..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-stripe-orange"
                  />
                </div>

                {/* Content View */}
                {activeTab === "transcript" ? (
                  <div className="space-y-2.5 max-h-[320px] overflow-y-auto pr-1">
                    {filteredTranscripts.map((item, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800/80 bg-slate-50/70 dark:bg-slate-950/40 hover:bg-slate-100 dark:hover:bg-slate-800/50 transition-colors text-xs"
                      >
                        <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                          <span className="font-semibold text-slate-700 dark:text-slate-300">
                            {item.speaker}
                          </span>
                          <span className="font-mono text-stripe-orange">
                            {item.time}
                          </span>
                        </div>
                        <p className="text-slate-600 dark:text-slate-300 text-xs leading-relaxed font-normal">
                          {item.text}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3 text-xs">
                    <div className="p-3 rounded-xl bg-stripe-orange/5 dark:bg-stripe-orange/10 border border-stripe-orange/20">
                      <div className="flex items-center gap-1.5 text-stripe-orange font-semibold text-xs mb-1">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Core Synthesis</span>
                      </div>
                      <p className="text-slate-600 dark:text-slate-300 text-xs leading-relaxed font-normal">
                        SGD with momentum behaves like a physical ball rolling down a noisy loss surface, dampening orthogonal oscillation while accelerating along relevant slopes.
                      </p>
                    </div>

                    <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/40">
                      <div className="font-semibold text-slate-900 dark:text-white text-xs mb-1">
                        Formulas Extracted
                      </div>
                      <code className="text-[11px] font-mono text-stripe-coral block bg-slate-100 dark:bg-slate-900 p-1.5 rounded">
                        v_t = γ * v_{"{t-1}"} + η * ∇_θ J(θ)
                      </code>
                    </div>
                  </div>
                )}
              </div>

              {/* Bottom Actions */}
              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">Export: Markdown, PDF, SRT</span>
                <button
                  onClick={onOpenUpload}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-medium text-xs hover:bg-stripe-orange dark:hover:bg-stripe-orange dark:hover:text-white transition-colors cursor-pointer"
                >
                  Process New File
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
