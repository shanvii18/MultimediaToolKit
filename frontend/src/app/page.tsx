"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  FolderKanban,
  Activity,
  Layers,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Upload,
} from "lucide-react";
import { TOOLKIT_MODULES } from "@/services/modulesCatalog";
import { ApiClient } from "@/services/apiClient";
import { Project, Job } from "@/types";

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [projRes, jobRes] = await Promise.all([
          ApiClient.listProjects().catch(() => []),
          ApiClient.listJobs().catch(() => []),
        ]);
        setProjects(projRes);
        setRecentJobs(jobRes);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const operationalModules = TOOLKIT_MODULES.filter((m) => m.status === "operational");

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10">
      {/* Hero Welcome banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-orange-950/40 via-amber-950/20 to-slate-900 border border-orange-500/30 p-8 shadow-2xl">
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/30 text-orange-400 text-xs font-mono">
            <Sparkles className="h-3.5 w-3.5" />
            <span>AI-First Multimedia Platform</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Transform ideas and media into finished content.
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Execute the complete blueprint lifecycle:{" "}
            <span className="text-orange-400 font-medium">IDEA → UNDERSTAND → CREATE → POLISH → DELIVER</span>. Process media with native FFmpeg, generate structured storyboards, and monitor background tasks.
          </p>
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              href="/workspace"
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-orange-500/25 transition-all"
            >
              <span>Open Creation Studio</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/modules"
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-sm flex items-center gap-2 transition-all"
            >
              <span>View All 20 Modules</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Access to Operational Modules */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Featured Operational Modules</h2>
            <p className="text-xs text-slate-400">Core capabilities deployed and ready for immediate execution</p>
          </div>
          <Link href="/modules" className="text-xs text-orange-400 hover:text-orange-300 flex items-center gap-1">
            <span>Explore full catalog</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {operationalModules.map((module) => (
            <Link
              key={module.id}
              href={module.route || `/workspace?tool=${module.slug}`}
              className="group p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-orange-500/40 hover:bg-slate-800/60 transition-all duration-200 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-orange-400 font-semibold">#{module.id}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Live
                  </span>
                </div>
                <h3 className="font-semibold text-white group-hover:text-orange-400 transition-colors text-sm">
                  {module.name}
                </h3>
                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{module.description}</p>
              </div>
              <div className="pt-4 flex items-center text-xs text-orange-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                <span>
                  {module.slug === "project-workspace-media-library"
                    ? "Open Projects"
                    : module.slug === "job-monitor-export-center"
                    ? "Open Monitor"
                    : "Launch Studio"}
                </span>
                <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Projects and Jobs Two-Column Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Projects Card */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FolderKanban className="h-5 w-5 text-orange-400" />
              <h3 className="font-bold text-white text-base">Projects & Workspaces</h3>
            </div>
            <Link href="/projects" className="text-xs text-slate-400 hover:text-white">
              View all
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading projects...</div>
          ) : projects.length === 0 ? (
            <div className="py-8 text-center space-y-3">
              <p className="text-xs text-slate-400">No projects created yet.</p>
              <Link
                href="/projects"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-orange-500/10 border border-orange-500/30 text-orange-400 text-xs"
              >
                Create initial project
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {projects.slice(0, 4).map((p) => (
                <Link
                  key={p.id}
                  href={`/projects?id=${p.id}`}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
                >
                  <div className="space-y-0.5">
                    <h4 className="text-sm font-medium text-slate-200">{p.title}</h4>
                    <p className="text-[11px] text-slate-400">{p.description || "No description"}</p>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">
                    {new Date(p.created_at).toLocaleDateString()}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Live Jobs Card */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-amber-400" />
              <h3 className="font-bold text-white text-base">Job Monitor & Tasks</h3>
            </div>
            <Link href="/jobs" className="text-xs text-slate-400 hover:text-white">
              View monitor
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading recent tasks...</div>
          ) : recentJobs.length === 0 ? (
            <div className="py-8 text-center space-y-3">
              <p className="text-xs text-slate-400">No background jobs executed yet.</p>
              <Link
                href="/workspace"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs"
              >
                Run first task
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {recentJobs.slice(0, 4).map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-200">{job.tool}</span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-md ${
                          job.status === "succeeded"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : job.status === "failed"
                            ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}
                      >
                        {job.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono">Job ID: {job.id.slice(0, 8)}...</p>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">
                    {new Date(job.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
