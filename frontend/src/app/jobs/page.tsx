"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  CheckCircle2,
  AlertCircle,
  Clock,
  Download,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { ApiClient } from "@/services/apiClient";
import { Job } from "@/types";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchJobs = async () => {
    try {
      const data = await ApiClient.listJobs();
      setJobs(data);
    } catch (err) {
      console.error("Failed to fetch jobs:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-mono">
            <span>Module #20</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Job Monitor & Export Center</h1>
          <p className="text-sm text-slate-400">
            Track asynchronous processing tasks, worker queue lifecycles, and download generated artifacts.
          </p>
        </div>

        <button
          onClick={() => {
            setRefreshing(true);
            fetchJobs();
          }}
          disabled={refreshing}
          className="px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-xl text-xs font-medium flex items-center gap-2 transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-orange-400" : ""}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Jobs Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
        {loading ? (
          <div className="py-20 text-center text-xs text-slate-500">Loading tasks queue...</div>
        ) : jobs.length === 0 ? (
          <div className="py-20 text-center space-y-3">
            <Activity className="h-10 w-10 text-slate-600 mx-auto" />
            <p className="text-sm font-medium text-slate-400">No processing jobs registered yet.</p>
            <p className="text-xs text-slate-500">
              Trigger a task from the Creation Studio or 20 Modules Directory to monitor progress here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-mono">
                <tr>
                  <th className="py-3 px-4">Job ID</th>
                  <th className="py-3 px-4">Tool / Module</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Progress</th>
                  <th className="py-3 px-4">Created At</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-slate-400">
                      {job.id.slice(0, 10)}...
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-white">
                      {job.tool}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono font-medium ${
                          job.status === "succeeded"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : job.status === "failed"
                            ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}
                      >
                        {job.status === "succeeded" ? (
                          <CheckCircle2 className="h-3 w-3" />
                        ) : job.status === "failed" ? (
                          <AlertCircle className="h-3 w-3" />
                        ) : (
                          <Clock className="h-3 w-3 animate-spin" />
                        )}
                        <span>{job.status}</span>
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="w-24 bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            job.status === "succeeded"
                              ? "bg-emerald-500"
                              : job.status === "failed"
                              ? "bg-rose-500"
                              : "bg-orange-500"
                          }`}
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-500">
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {job.outputs && job.outputs.length > 0 ? (
                        <a
                          href={ApiClient.getDownloadUrl(job.outputs[0].asset_id)}
                          download
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-medium transition-colors"
                        >
                          <Download className="h-3 w-3" />
                          <span>Download</span>
                        </a>
                      ) : (
                        <span className="text-slate-600 font-mono text-[11px]">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
