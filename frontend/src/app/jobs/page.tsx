"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Activity, AlertCircle, CheckCircle2, Clock, Download, Loader2, RefreshCw, Repeat } from "lucide-react";
import { ApiClient } from "@/services/apiClient";
import { Conversion, Job } from "@/types";
import { formatBytes } from "@/components/convert/ConvertUi";

type Filter = "all" | "active" | "succeeded" | "failed";

const STATUS_STYLE: Record<string, string> = {
  succeeded: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  failed: "bg-rose-500/10 text-rose-300 border-rose-500/30",
  running: "bg-orange-500/10 text-orange-300 border-orange-500/30",
  queued: "bg-slate-700/30 text-slate-300 border-slate-700",
  cancelled: "bg-slate-700/30 text-slate-400 border-slate-700",
};

function when(iso: string): string {
  const d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function ConversionHistoryPage() {
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [titles, setTitles] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");

  const fetchJobs = useCallback(async () => {
    try {
      setJobs(await ApiClient.listJobs());
      setError(null);
    } catch (err: any) {
      setError(err.message || "Could not load your history.");
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    ApiClient.listConversions()
      .then((all: Conversion[]) => setTitles(Object.fromEntries(all.map((c) => [c.id, c.title]))))
      .catch(() => undefined);
    const interval = setInterval(fetchJobs, 4000);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  const visible = useMemo(() => {
    const list = jobs || [];
    if (filter === "active") return list.filter((j) => j.status === "queued" || j.status === "running");
    if (filter === "all") return list;
    return list.filter((j) => j.status === filter);
  }, [jobs, filter]);

  const counts = useMemo(() => {
    const list = jobs || [];
    return {
      all: list.length,
      active: list.filter((j) => j.status === "queued" || j.status === "running").length,
      succeeded: list.filter((j) => j.status === "succeeded").length,
      failed: list.filter((j) => j.status === "failed").length,
    };
  }, [jobs]);

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Conversion History</h1>
          <p className="text-sm text-slate-400">Every conversion you have run, with live progress and all output files.</p>
        </div>
        <button
          onClick={() => {
            setRefreshing(true);
            fetchJobs();
          }}
          disabled={refreshing}
          className="px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-xl text-xs font-medium flex items-center gap-2"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-orange-400" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {(["all", "active", "succeeded", "failed"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border capitalize ${
              filter === f ? "border-orange-500 bg-orange-500/10 text-orange-300" : "border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            {f} ({counts[f]})
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {jobs === null && !error && (
        <div className="py-20 flex items-center justify-center gap-2 text-sm text-slate-400">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading history…
        </div>
      )}

      {jobs !== null && visible.length === 0 && (
        <div className="py-20 text-center space-y-3 rounded-2xl border border-slate-800 bg-slate-900/60">
          <Activity className="h-10 w-10 text-slate-600 mx-auto" />
          <p className="text-sm font-medium text-slate-400">
            {jobs.length === 0 ? "No conversions yet." : "Nothing matches this filter."}
          </p>
          {jobs.length === 0 && (
            <Link href="/convert" className="text-xs text-orange-400 hover:text-orange-300 font-medium">
              Start your first conversion →
            </Link>
          )}
        </div>
      )}

      <div className="space-y-3">
        {visible.map((job) => (
          <div key={job.id} className="p-4 sm:p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white">
                  {titles[job.tool] || job.tool}
                  {job.params_json?.mode && (
                    <span className="ml-2 text-[11px] font-mono text-slate-500">{String(job.params_json.mode)}</span>
                  )}
                </p>
                <p className="text-[11px] text-slate-500 flex items-center gap-1">
                  <Clock className="h-3 w-3" /> {when(job.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded-md border text-[11px] font-medium ${STATUS_STYLE[job.status] || ""}`}>
                  {job.status === "succeeded" && <CheckCircle2 className="inline h-3 w-3 mr-1" />}
                  {job.status}
                </span>
                {titles[job.tool] && (
                  <Link href={`/convert/${job.tool}`} className="p-1.5 rounded-lg text-slate-400 hover:text-white" title="Run again">
                    <Repeat className="h-4 w-4" />
                  </Link>
                )}
              </div>
            </div>

            {(job.status === "queued" || job.status === "running") && (
              <div className="space-y-1">
                <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-orange-500 to-amber-500 transition-all" style={{ width: `${job.progress}%` }} />
                </div>
                <p className="text-[11px] text-slate-400">
                  {job.progress}% {job.progress_message ? `· ${job.progress_message}` : job.status === "queued" ? "· waiting for a worker" : ""}
                </p>
              </div>
            )}

            {job.status === "failed" && (
              <p className="text-xs text-rose-300">
                {job.error_code && <span className="font-mono mr-1">[{job.error_code}]</span>}
                {job.error_message}
              </p>
            )}

            {job.outputs && job.outputs.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {job.outputs.map(
                  (o) =>
                    o.asset && (
                      <a
                        key={o.id}
                        href={ApiClient.getDownloadUrl(o.asset)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-orange-500/60 text-xs text-slate-300"
                        title={o.output_type}
                      >
                        <Download className="h-3.5 w-3.5 text-orange-400" />
                        <span className="truncate max-w-[14rem]">{o.asset.filename}</span>
                        <span className="text-slate-500">{formatBytes(o.asset.size)}</span>
                      </a>
                    )
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
