"use client";

import React, { useState } from "react";
import { Scan, CheckCircle2, ArrowRight, Copy, Check } from "lucide-react";

export function ImageToTextSection() {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="image-to-text" className="relative py-20 md:py-28 overflow-hidden">
      {/* Sky Blue & Coral Ambient Glow */}
      <div className="absolute top-1/2 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-stripe-cyan/15 via-stripe-coral/15 to-transparent blur-[130px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          {/* Left Column: Visual Scanner Mockup (Document with laser scan + Extracted text) */}
          <div className="lg:col-span-7 order-2 lg:order-1">
            <div className="relative rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xl">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5 items-stretch">
                {/* 1. Source Document with Corner Markers & Laser Scan */}
                <div className="relative rounded-xl border border-slate-200 dark:border-slate-700/80 bg-slate-100 dark:bg-slate-950 p-4 overflow-hidden min-h-[300px] flex flex-col justify-between shadow-inner">
                  {/* Four Corner Optical Bounding Markers */}
                  <div className="absolute top-2 left-2 w-3.5 h-3.5 border-t-2 border-l-2 border-stripe-coral" />
                  <div className="absolute top-2 right-2 w-3.5 h-3.5 border-t-2 border-r-2 border-stripe-coral" />
                  <div className="absolute bottom-2 left-2 w-3.5 h-3.5 border-b-2 border-l-2 border-stripe-coral" />
                  <div className="absolute bottom-2 right-2 w-3.5 h-3.5 border-b-2 border-r-2 border-stripe-coral" />

                  {/* Laser Scan Line Animation (Smooth Light Blue / Coral) */}
                  <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-stripe-cyan to-transparent shadow-[0_0_12px_#00D4FF] animate-scan-line pointer-events-none z-10" />

                  {/* Document Content Simulation */}
                  <div className="space-y-3 z-0">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
                      <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                        SOURCE: Lecture_Handout_P3.png
                      </span>
                      <span className="text-[10px] text-stripe-coral font-semibold bg-stripe-coral/10 px-1.5 py-0.5 rounded">
                        Scanning
                      </span>
                    </div>

                    <div className="text-xs font-serif text-slate-800 dark:text-slate-200 leading-relaxed space-y-2">
                      <div className="font-semibold text-sm">
                        Theorem 4.2: Singular Value Decomposition
                      </div>
                      <p className="text-[11px] text-slate-600 dark:text-slate-400">
                        Let A be an m x n real matrix. Then there exists a factorization of the form:
                      </p>
                      <div className="p-2 rounded bg-white/70 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 font-mono text-[11px] text-center text-stripe-coral dark:text-stripe-peach">
                        A = U · Σ · V^T
                      </div>
                      <p className="text-[11px] text-slate-600 dark:text-slate-400">
                        Where U is an m x m orthogonal matrix, Σ is an m x n diagonal matrix of singular values, and V is n x n orthogonal.
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 pt-2 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                    <span>Optical Resolution: 300 DPI</span>
                    <span className="text-stripe-coral">Orientation: 0° Auto</span>
                  </div>
                </div>

                {/* 2. Structured Extracted Text Panel */}
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-950/80 p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800 mb-3">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-900 dark:text-white">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        <span>Extracted Text</span>
                      </div>
                      <button
                        onClick={handleCopy}
                        className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors cursor-pointer"
                        title="Copy text"
                      >
                        {copied ? (
                          <Check className="w-3.5 h-3.5 text-emerald-500" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>

                    <div className="space-y-2 text-xs text-slate-700 dark:text-slate-300 font-sans">
                      <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span className="text-[10px] font-semibold uppercase text-stripe-coral block mb-0.5">
                          Extracted Heading
                        </span>
                        <div className="font-medium text-slate-900 dark:text-white text-xs">
                          Theorem 4.2: Singular Value Decomposition
                        </div>
                      </div>

                      <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span className="text-[10px] font-semibold uppercase text-stripe-coral block mb-0.5">
                          Mathematical Formula (LaTeX)
                        </span>
                        <code className="font-mono text-xs text-stripe-coral block">
                          A = U \Sigma V^T
                        </code>
                      </div>

                      <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                        <span className="text-[10px] font-semibold uppercase text-stripe-coral block mb-0.5">
                          Body Text
                        </span>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
                          Where U is m×m orthogonal, Σ is m×n diagonal singular values, and V is n×n orthogonal.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 pt-2 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Accuracy: 99.8%</span>
                    <span className="text-stripe-coral font-medium">
                      Export to Markdown
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Editorial Copy (Matching Screenshot 1 typography) */}
          <div className="lg:col-span-5 order-1 lg:order-2 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-stripe-cyan/10 text-stripe-cyan border border-stripe-cyan/20">
              <Scan className="w-3.5 h-3.5" />
              <span>Module 03 • Image to Text</span>
            </div>

            <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-[-0.03em] text-slate-900 dark:text-white leading-tight">
              A clearer read, from any page.
            </h2>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
              Unlock handwritten chalkboard scribbles, dense textbook diagrams,
              and photograph slides. Automatically deskew, denoise, and parse typography into clean, selectable markdown.
            </p>

            <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-center gap-2.5">
                <div className="w-5 h-5 rounded-full bg-stripe-cyan/10 text-stripe-cyan flex items-center justify-center font-bold text-xs">
                  ✓
                </div>
                <span>Automatic perspective correction and border cropping</span>
              </li>
              <li className="flex items-center gap-2.5">
                <div className="w-5 h-5 rounded-full bg-stripe-cyan/10 text-stripe-cyan flex items-center justify-center font-bold text-xs">
                  ✓
                </div>
                <span>Math equation formatting into standard LaTeX syntax</span>
              </li>
              <li className="flex items-center gap-2.5">
                <div className="w-5 h-5 rounded-full bg-stripe-cyan/10 text-stripe-cyan flex items-center justify-center font-bold text-xs">
                  ✓
                </div>
                <span>Multi-column layout detection and table row preservation</span>
              </li>
            </ul>

            <div className="pt-2">
              <a
                href="#study-mode"
                className="inline-flex items-center gap-2 text-sm font-medium text-stripe-coral hover:text-stripe-orange transition-colors"
              >
                <span>Combine all formats in the AI Study Companion</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
