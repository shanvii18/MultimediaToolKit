"use client";

import React, { useState } from "react";
import {
  Database,
  Terminal,
  Share2,
  CheckCircle2,
  ArrowRight,
  Cpu,
} from "lucide-react";

export function FeatureHighlights() {
  const [activeTab, setActiveTab] = useState<"arch" | "data" | "export">("arch");

  return (
    <section id="features" className="relative py-24 md:py-32 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          {/* Left Column: Spacious Editorial Typography matching Screenshot 1 */}
          <div className="lg:col-span-5 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-stripe-coral/10 text-stripe-coral border border-stripe-coral/20">
              <Cpu className="w-3.5 h-3.5" />
              <span>Engineered for Scale</span>
            </div>

            <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-[-0.03em] text-slate-900 dark:text-white leading-tight">
              Production-grade architecture under the hood.
            </h2>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
              Designed from Day 1 to handle resource-heavy multimedia workloads without blocking user requests or dropping background tasks.
            </p>

            <div className="space-y-3.5 pt-2">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold text-xs shrink-0">
                  ✓
                </div>
                <span className="text-sm font-normal text-slate-700 dark:text-slate-200">
                  FastAPI backend with asynchronous worker queues
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold text-xs shrink-0">
                  ✓
                </div>
                <span className="text-sm font-normal text-slate-700 dark:text-slate-200">
                  Redis-backed job scheduling with PostgreSQL persistence
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold text-xs shrink-0">
                  ✓
                </div>
                <span className="text-sm font-normal text-slate-700 dark:text-slate-200">
                  Full Docker Compose network orchestration
                </span>
              </div>
            </div>

            <div className="pt-2">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 text-sm font-medium text-stripe-orange hover:text-amber-600 dark:hover:text-amber-400 transition-colors"
              >
                <span>Inspect OpenAPI specifications</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Right Column: Architectural Terminal & Spec Inspector */}
          <div className="lg:col-span-7">
            <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl p-6 sm:p-8">
              {/* Tabs */}
              <div className="flex items-center gap-2 pb-4 border-b border-slate-200 dark:border-slate-800 mb-6">
                <button
                  onClick={() => setActiveTab("arch")}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    activeTab === "arch"
                      ? "bg-stripe-orange text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                  }`}
                >
                  <Terminal className="w-3.5 h-3.5" />
                  <span>Microservices Topology</span>
                </button>
                <button
                  onClick={() => setActiveTab("data")}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    activeTab === "data"
                      ? "bg-stripe-orange text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                  }`}
                >
                  <Database className="w-3.5 h-3.5" />
                  <span>Persistence Layer</span>
                </button>
                <button
                  onClick={() => setActiveTab("export")}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    activeTab === "export"
                      ? "bg-stripe-orange text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                  }`}
                >
                  <Share2 className="w-3.5 h-3.5" />
                  <span>Export Standards</span>
                </button>
              </div>

              {/* Panel 1: Topology */}
              {activeTab === "arch" && (
                <div className="space-y-4 animate-fade-in text-xs font-mono">
                  <div className="p-4 rounded-xl bg-slate-950 text-slate-200 space-y-2 border border-slate-800">
                    <div className="text-slate-400">{"// Docker Compose Network Topology: mtk-network"}</div>
                    <div className="text-stripe-orange">frontend:3000   → Next.js 14 App Router + Tailwind</div>
                    <div className="text-stripe-coral">backend:8000    → FastAPI Core REST API (/health)</div>
                    <div className="text-stripe-pink">worker          → Python Celery/Redis Consumer Loop</div>
                    <div className="text-stripe-amber">postgres:5432   → PostgreSQL 16 Alpine Volume</div>
                    <div className="text-sky-400">redis:6379      → Redis 7 Task Queue & Cache</div>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-sans font-normal">
                    All containers operate inside a bridge network, decoupling long-running media extraction tasks from synchronous web clients.
                  </p>
                </div>
              )}

              {/* Panel 2: Persistence */}
              {activeTab === "data" && (
                <div className="space-y-4 animate-fade-in text-xs">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                      <span className="font-semibold text-slate-900 dark:text-white block mb-1">
                        PostgreSQL 16
                      </span>
                      <p className="text-[11px] text-slate-500 font-normal">
                        Stores user libraries, course folders, metadata tags, and timestamp indexes with ACID guarantees.
                      </p>
                    </div>
                    <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                      <span className="font-semibold text-slate-900 dark:text-white block mb-1">
                        Redis 7 In-Memory
                      </span>
                      <p className="text-[11px] text-slate-500 font-normal">
                        Low-latency queue broker distributing extraction jobs to background Python worker daemons.
                      </p>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>Configured with automated healthchecks in docker-compose.yml</span>
                  </div>
                </div>
              )}

              {/* Panel 3: Export Standards */}
              {activeTab === "export" && (
                <div className="space-y-4 animate-fade-in text-xs">
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                      <div className="font-semibold text-stripe-orange mb-1">Anki .apkg</div>
                      <div className="text-[11px] text-slate-400">Spaced repetition decks</div>
                    </div>
                    <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                      <div className="font-semibold text-stripe-coral mb-1">Markdown .md</div>
                      <div className="text-[11px] text-slate-400">Notion & Obsidian ready</div>
                    </div>
                    <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                      <div className="font-semibold text-stripe-pink mb-1">Subtitles .srt</div>
                      <div className="text-[11px] text-slate-400">Timed video captions</div>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-normal">
                    No vendor lock-in. Every extracted transcript and generated study artifact is exportable into open standards.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
