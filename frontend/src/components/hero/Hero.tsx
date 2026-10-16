"use client";

import React, { useState, useEffect } from "react";
import { GradientRibbon } from "./GradientRibbon";
import { AudioWaveform } from "@/components/ui/AudioWaveform";
import {
  ArrowRight,
  ArrowDownRight,
  Play,
  Volume2,
  Sparkles,
  Check,
  CheckCircle2,
  Clock,
  MoreHorizontal,
} from "lucide-react";

interface HeroProps {
  onOpenUpload: () => void;
}

export function Hero({ onOpenUpload }: HeroProps) {
  // Sequential Animated Headline Messages (Requirement 4: Exactly one at a time)
  const headlines = [
    {
      prefix: "Every format.",
      highlight: "One intelligent workspace.",
    },
    {
      prefix: "Video to audio.",
      highlight: "Studio-grade extraction.",
    },
    {
      prefix: "Speech to text.",
      highlight: "Searchable in milliseconds.",
    },
    {
      prefix: "Raw recordings.",
      highlight: "Synthesized study companion.",
    },
  ];

  const [currentHeadlineIdx, setCurrentHeadlineIdx] = useState(0);
  const [isFading, setIsFading] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(true);

  useEffect(() => {
    const timer = setInterval(() => {
      setIsFading(true);
      setTimeout(() => {
        setCurrentHeadlineIdx((prev) => (prev + 1) % headlines.length);
        setIsFading(false);
      }, 400); // 400ms transition time
    }, 4500); // 4.5s reading duration

    return () => clearInterval(timer);
  }, [headlines.length]);

  const scrollToWorkspace = () => {
    const el = document.getElementById("workspace-preview");
    el?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="relative pt-24 pb-20 md:pt-36 md:pb-32 overflow-hidden">
      {/* Signature Stripe-Inspired Ribbon (Screenshot 2 Reference) */}
      <GradientRibbon />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column: Editorial Typography matching Screenshot 1 */}
          <div className="lg:col-span-6 z-10 space-y-6 md:space-y-8 text-left">
            {/* Eyebrow Label matching Screenshot 1: dot + tracked uppercase */}
            <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-700 dark:text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
              <span>YOUR CONTENT, IN A NEW LIGHT</span>
            </div>

            {/* Sequential Animated Headline with fixed container to eliminate jumping */}
            <div className="min-h-[140px] sm:min-h-[170px] md:min-h-[200px] flex items-center">
              <h1
                className={`text-4xl sm:text-5xl md:text-6xl font-normal tracking-[-0.03em] text-slate-900 dark:text-white leading-[1.08] transition-all duration-400 ${
                  isFading
                    ? "opacity-0 translate-y-3"
                    : "opacity-100 translate-y-0"
                }`}
              >
                {headlines[currentHeadlineIdx].prefix} <br />
                <span className="stripe-text-gradient font-medium">
                  {headlines[currentHeadlineIdx].highlight}
                </span>
              </h1>
            </div>

            {/* Supporting Copy */}
            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-xl font-normal leading-relaxed">
              Transform videos, audio, images and documents into searchable text
              and powerful study material—all in one place.
            </p>

            {/* CTAs matching Screenshot 1 */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-5 pt-1">
              <button
                onClick={onOpenUpload}
                className="px-7 py-3.5 rounded-lg text-sm font-medium text-white bg-gradient-to-r from-stripe-orange via-stripe-coral to-stripe-pink hover:brightness-105 transition-all shadow-lg shadow-stripe-orange/20 flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>Start creating</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={scrollToWorkspace}
                className="px-2 py-3.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-stripe-orange transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <span>Explore the workspace</span>
                <ArrowDownRight className="w-4 h-4" />
              </button>
            </div>

            {/* Feature Checkpoints */}
            <div className="pt-2 flex flex-wrap items-center gap-6 text-xs text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5 text-emerald-500" />
                Zero setup required
              </span>
              <span className="flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5 text-emerald-500" />
                Lossless stream extraction
              </span>
              <span className="flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5 text-emerald-500" />
                Spaced repetition ready
              </span>
            </div>
          </div>

          {/* Right Column: Architectural Blueprint Layout with Floating Cards matching Screenshot 1 */}
          <div className="lg:col-span-6 relative h-[500px] sm:h-[540px] md:h-[580px] w-full flex items-center justify-center">
            {/* Blueprint Grid Frame matching Screenshot 1 */}
            <div className="absolute inset-0 rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white/40 dark:bg-slate-900/40 backdrop-blur-md blueprint-grid p-6 flex flex-col justify-between overflow-hidden shadow-sm">
              {/* Header Coordinates */}
              <div className="flex items-center justify-between text-[10px] font-mono tracking-widest text-slate-400 dark:text-slate-500 uppercase">
                <span>ONE SOURCE, MANY POSSIBILITIES</span>
                <span>MMK / 01</span>
              </div>

              {/* Diagonal trajectory guidelines */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40 dark:opacity-20" aria-hidden="true">
                <line x1="20%" y1="90%" x2="90%" y2="20%" stroke="#FF6584" strokeWidth="1" strokeDasharray="3 3" />
                <line x1="10%" y1="70%" x2="85%" y2="10%" stroke="#FF9066" strokeWidth="1" strokeDasharray="4 4" />
              </svg>

              <div />
            </div>

            {/* CARD 1: VIDEO (Top-Center / Left matching Screenshot 1) */}
            <div className="absolute top-8 sm:top-10 left-3 sm:left-8 w-64 sm:w-72 rounded-xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl p-3.5 z-20 animate-float-gentle">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800/80 mb-2.5">
                <span className="text-[10px] font-bold tracking-wider uppercase text-slate-500 dark:text-slate-400">
                  VIDEO
                </span>
                <MoreHorizontal className="w-3.5 h-3.5 text-slate-400" />
              </div>

              {/* Video Preview thumbnail with geometric diamond overlay (Screenshot 1) */}
              <div className="relative rounded-lg overflow-hidden bg-slate-950 aspect-[16/9] flex items-center justify-center">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-950 opacity-90" />

                {/* Geometrical Rotated Diamond Frame */}
                <div className="absolute w-20 h-20 border border-stripe-coral/40 rotate-45 pointer-events-none" />
                <div className="absolute w-24 h-24 border border-stripe-amber/30 rotate-12 pointer-events-none" />

                {/* Play Button */}
                <div className="w-10 h-10 rounded-full bg-white/20 border border-white/40 backdrop-blur-md flex items-center justify-center text-white shadow-lg cursor-pointer hover:scale-105 transition-transform z-10">
                  <Play className="w-4 h-4 fill-white ml-0.5" />
                </div>
              </div>

              <div className="mt-2.5 flex items-center justify-between text-xs px-0.5">
                <span className="text-slate-600 dark:text-slate-300 text-[11px] font-medium">
                  Cellular biology - lecture 04
                </span>
                <span className="text-[10px] text-stripe-orange font-semibold">
                  1080p
                </span>
              </div>
            </div>

            {/* CARD 2: AUDIO TRANSCRIPT with LIVE ANIMATED WAVEFORM (Right-Center matching Screenshot 1) */}
            <div className="absolute top-28 sm:top-32 right-2 sm:right-6 w-72 sm:w-80 rounded-xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-4 z-30 animate-float-reverse">
              <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 dark:border-slate-800/80 mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold tracking-wider uppercase text-slate-600 dark:text-slate-400">
                    AUDIO TRANSCRIPT
                  </span>
                </div>
                <button
                  onClick={() => setIsPlayingAudio(!isPlayingAudio)}
                  className="p-1 rounded text-slate-400 hover:text-stripe-orange transition-colors"
                  title="Toggle waveform audio animation"
                >
                  <Volume2 className="w-3.5 h-3.5 text-stripe-coral" />
                </button>
              </div>

              {/* LIVE ANIMATED MULTI-BAR AUDIO WAVEFORM (Requirement 5) */}
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950/70 border border-slate-100 dark:border-slate-800/80">
                <AudioWaveform
                  isPlaying={isPlayingAudio}
                  barCount={28}
                  heightClass="h-9"
                  colorScheme="orange-coral"
                />
              </div>

              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-mono">

                <span>&quot;...the signal&quot;</span>

                <span className="text-stripe-orange font-semibold">00:14 - 18:42</span>
              </div>
            </div>

            {/* CARD 3: STUDY NOTES (Bottom-Right matching Screenshot 1) */}
            <div className="absolute bottom-6 sm:bottom-8 right-4 sm:right-12 w-64 sm:w-72 rounded-xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl p-4 z-40 animate-float-delayed">
              <div className="flex items-center gap-2 pb-2 border-b border-slate-100 dark:border-slate-800/80 mb-2.5">
                <div className="p-1 rounded bg-emerald-500/10 text-emerald-500">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
                <span className="text-[10px] font-bold tracking-wider uppercase text-slate-700 dark:text-slate-300">
                  STUDY NOTES
                </span>
              </div>

              {/* Visual Summary Representation (Screenshot 1) */}
              <div className="space-y-1.5 my-2">
                <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-700 w-full" />
                <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-700 w-4/5" />
                <div className="h-2 rounded-full bg-stripe-coral/40 w-3/5" />
              </div>

              <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                  <Check className="w-3 h-3" /> Ready to review
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  12 Key Concepts
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
