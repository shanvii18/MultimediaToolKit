"use client";

import React from "react";
import { Layers, Activity, ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/80 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10">
          {/* Brand Col */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg stripe-gradient-mesh flex items-center justify-center text-white font-bold text-sm shadow-md shadow-stripe-orange/20">
                <Layers className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold text-lg text-slate-900 dark:text-white">
                Multimedia<span className="text-stripe-orange">ToolKit</span>
              </span>
            </div>

            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm leading-relaxed font-normal">
              A production-style multimedia processing platform. Ingests video, audio, image, and text formats to create synchronized study material and searchable knowledge units.
            </p>

            <div className="pt-2 flex items-center gap-2">
              <a
                href="http://localhost:8000/health"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors"
              >
                <Activity className="w-3 h-3 text-emerald-500 animate-pulse" />
                <span>Backend API: /health OK</span>
                <ExternalLink className="w-2.5 h-2.5 opacity-60" />
              </a>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              >
                <span>Swagger Docs</span>
                <ExternalLink className="w-2.5 h-2.5 opacity-60" />
              </a>
            </div>
          </div>

          {/* Col 2: Products */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
              Products
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400 font-normal">
              <li>
                <a href="#video-to-audio" className="hover:text-stripe-orange transition-colors">
                  Video to Audio
                </a>
              </li>
              <li>
                <a href="#audio-to-text" className="hover:text-stripe-orange transition-colors">
                  Audio to Text
                </a>
              </li>
              <li>
                <a href="#image-to-text" className="hover:text-stripe-orange transition-colors">
                  Image to Text
                </a>
              </li>
              <li>
                <a href="#study-mode" className="hover:text-stripe-orange transition-colors">
                  AI Study Mode
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3: Platform */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
              Platform
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400 font-normal">
              <li>
                <a href="#workspace-preview" className="hover:text-stripe-orange transition-colors">
                  Workspace Mockup
                </a>
              </li>
              <li>
                <a href="#workflow" className="hover:text-stripe-orange transition-colors">
                  Unified Pipeline
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-stripe-orange transition-colors">
                  Feature Highlights
                </a>
              </li>
              <li>
                <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="hover:text-stripe-orange transition-colors">
                  FastAPI OpenAPI Spec
                </a>
              </li>
            </ul>
          </div>

          {/* Col 4: Project Info */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
              Project
            </h4>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400 font-normal">
              <li>
                <span className="text-slate-500">Semester Milestone: Day 1</span>
              </li>
              <li>
                <span className="text-slate-500">FastAPI + Redis + Next.js</span>
              </li>
              <li>
                <span className="text-slate-500">Docker Containerized</span>
              </li>
              <li>
                <span className="text-slate-500">MIT Open Source</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-6 border-t border-slate-200/80 dark:border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500 dark:text-slate-400 font-normal">
          <p>© {new Date().getFullYear()} MultimediaToolKit. Built with Next.js 14, Tailwind CSS & FastAPI.</p>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-stripe-orange transition-colors">Privacy</a>
            <a href="#" className="hover:text-stripe-orange transition-colors">Terms</a>
            <a href="#" className="hover:text-stripe-orange transition-colors">Security</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
