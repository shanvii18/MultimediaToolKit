"use client";

import React, { useState } from "react";
import { AudioWaveform } from "@/components/ui/AudioWaveform";
import { Video, Music, ArrowRight, Play, CheckCircle2, Sliders, Volume2 } from "lucide-react";

export function VideoToAudioSection() {
  const [isPlaying, setIsPlaying] = useState(true);

  return (
    <section id="video-to-audio" className="relative py-20 md:py-28 overflow-hidden">
      {/* Warm Orange-to-Pink Ambient Glow */}
      <div className="absolute top-1/2 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-stripe-orange/20 via-stripe-coral/20 to-transparent blur-[120px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          {/* Left Column: Visual Composition (Video -> Ribbon Extraction -> Waveform) */}
          <div className="lg:col-span-7 order-2 lg:order-1">
            <div className="relative rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xl overflow-hidden">
              {/* Decorative Ribbon Accent */}
              <div className="absolute -right-20 -bottom-20 w-80 h-80 rounded-full bg-gradient-to-tr from-stripe-orange/25 to-stripe-coral/25 blur-3xl pointer-events-none" />

              {/* Source Video Frame */}
              <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 relative aspect-[16/9] shadow-md">
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-900/40 to-transparent" />
                <div className="absolute top-3 left-3 px-2.5 py-1 rounded-md bg-black/70 text-white font-mono text-[10px] backdrop-blur flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  Keynote_Opening_Lecture.mp4 (4K 60fps)
                </div>

                <div className="absolute inset-0 flex items-center justify-center">
                  <div
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="w-13 h-13 rounded-full bg-white/20 border border-white/40 backdrop-blur-md flex items-center justify-center text-white shadow-xl hover:scale-105 transition-transform cursor-pointer"
                  >
                    <Play className="w-5 h-5 fill-white ml-0.5" />
                  </div>
                </div>

                {/* Extraction Ribbon Vector Path Overlay */}
                <div className="absolute bottom-3 inset-x-3 flex items-center justify-between text-[11px] text-white/90 font-mono">
                  <span>00:12:15</span>
                  <div className="flex-1 mx-3 h-1.5 rounded-full bg-white/20 overflow-hidden relative">
                    <div className="w-2/3 h-full bg-gradient-to-r from-stripe-orange to-stripe-coral" />
                  </div>
                  <span>01:14:00</span>
                </div>
              </div>

              {/* Extraction Bridge / Pipeline Connector */}
              <div className="my-5 flex items-center justify-between px-2">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-500 dark:text-slate-400">
                  <Video className="w-4 h-4 text-stripe-orange" />
                  <span>Demuxing AVC/HEVC Container</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-0.5 w-16 bg-gradient-to-r from-stripe-orange to-stripe-coral" />
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-stripe-coral bg-stripe-coral/10 px-2 py-0.5 rounded-full border border-stripe-coral/20">
                    Lossless Extraction
                  </span>
                </div>
              </div>

              {/* Extracted Audio Track & LIVE ANIMATED WAVEFORM (Requirement 5) */}
              <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-stripe-coral/10 text-stripe-coral flex items-center justify-center font-bold">
                      <Music className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-slate-900 dark:text-white">
                        Keynote_Opening_Isolated.wav
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Linear PCM • 24-bit • 48 kHz
                      </div>
                    </div>
                  </div>

                  <span className="text-[10px] font-semibold text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Ready for Transcribe
                  </span>
                </div>

                {/* Live Animated Audio Waveform */}
                <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200/60 dark:border-slate-800/80">
                  <AudioWaveform
                    isPlaying={isPlaying}
                    barCount={38}
                    heightClass="h-12"
                    colorScheme="orange-coral"
                  />
                </div>

                <div className="mt-3 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                  <div className="flex items-center gap-2">
                    <Sliders className="w-3.5 h-3.5" />
                    <span>Dynamic Range Compression: Active</span>
                  </div>
                  <span className="font-mono text-slate-700 dark:text-slate-300">
                    File Size: 124 MB (down from 2.8 GB)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Editorial Copy (Matching Screenshot 1 typography) */}
          <div className="lg:col-span-5 order-1 lg:order-2 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-stripe-orange/10 text-stripe-orange border border-stripe-orange/20">
              <Video className="w-3.5 h-3.5" />
              <span>Module 01 • Video to Audio</span>
            </div>

            <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-[-0.03em] text-slate-900 dark:text-white leading-tight">
              Hear the important parts.
            </h2>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
              Strip out multi-gigabyte video overhead in seconds. Extract studio-grade,
              isolated audio streams with pristine frequency clarity ready for immediate review or downstream transcription.
            </p>

            <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-center gap-2.5">
                <div className="w-5 h-5 rounded-full bg-stripe-orange/10 text-stripe-orange flex items-center justify-center font-bold text-xs">
                  ✓
                </div>
                <span>Direct stream copy extraction without generational compression loss</span>
              </li>
              <li className="flex items-center gap-2.5">
                <div className="w-5 h-5 rounded-full bg-stripe-orange/10 text-stripe-orange flex items-center justify-center font-bold text-xs">
                  ✓
                </div>
                <span>Export directly to MP3, AAC, FLAC, or uncompressed WAV</span>
              </li>
              <li className="flex items-center gap-2.5">
                <div className="w-5 h-5 rounded-full bg-stripe-orange/10 text-stripe-orange flex items-center justify-center font-bold text-xs">
                  ✓
                </div>
                <span>Automated audio normalization and speech frequency enhancement</span>
              </li>
            </ul>

            <div className="pt-2">
              <a
                href="#audio-to-text"
                className="inline-flex items-center gap-2 text-sm font-medium text-stripe-orange hover:text-amber-600 dark:hover:text-amber-400 transition-colors"
              >
                <span>Explore downstream audio transcription</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
