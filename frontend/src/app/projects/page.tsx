"use client";

import React, { useState, useEffect } from "react";
import {
  FolderKanban,
  Plus,
  File,
  Download,
  Calendar,
  Layers,
  Sparkles,
} from "lucide-react";
import { ApiClient } from "@/services/apiClient";
import { Project, Asset } from "@/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);

  // New project modal/form state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);

  const loadData = async () => {
    try {
      const [projList, assetList] = await Promise.all([
        ApiClient.listProjects().catch(() => []),
        ApiClient.listAssets().catch(() => []),
      ]);
      setProjects(projList);
      setAssets(assetList);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      await ApiClient.createProject(newTitle, newDesc);
      setNewTitle("");
      setNewDesc("");
      setShowCreateModal(false);
      loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-mono">
            <span>Module #19</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Project Workspace & Media Library
          </h1>
          <p className="text-sm text-slate-400">
            Organize production workspaces, original uploaded media, and generated outputs.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-medium text-xs flex items-center gap-2 shadow-lg shadow-orange-500/20 transition-all"
        >
          <Plus className="h-4 w-4" />
          <span>New Project</span>
        </button>
      </div>

      {/* Projects Section */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <FolderKanban className="h-4 w-4 text-orange-400" />
          <span>Workspaces</span>
        </h2>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500">Loading workspaces...</div>
        ) : projects.length === 0 ? (
          <div className="p-8 border border-dashed border-slate-800 rounded-2xl text-center space-y-3">
            <p className="text-xs text-slate-400">No project workspaces created yet.</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-3 py-1.5 rounded-lg bg-orange-500/10 border border-orange-500/30 text-orange-400 text-xs font-medium"
            >
              Create first workspace
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((proj) => (
              <div
                key={proj.id}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-slate-500">
                    ID: {proj.id.slice(0, 8)}...
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {new Date(proj.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="font-bold text-white text-sm">{proj.title}</h3>
                <p className="text-xs text-slate-400 line-clamp-2">{proj.description || "No description provided."}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Assets / Media Library Section */}
      <div className="space-y-4 pt-4 border-t border-slate-800">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Layers className="h-4 w-4 text-amber-400" />
          <span>Media Library Assets</span>
        </h2>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500">Loading assets...</div>
        ) : assets.length === 0 ? (
          <div className="p-8 border border-dashed border-slate-800 rounded-2xl text-center text-xs text-slate-500">
            No media assets registered in storage yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {assets.map((asset) => (
              <div
                key={asset.id}
                className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 flex flex-col justify-between"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-slate-400">
                    <File className="h-4 w-4 text-orange-400" />
                    <span className="font-mono text-[10px] text-slate-500">
                      {(asset.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                  <h4 className="font-semibold text-white text-xs truncate" title={asset.filename}>
                    {asset.filename}
                  </h4>
                  <p className="text-[10px] font-mono text-slate-500">{asset.media_type}</p>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex justify-end">
                  <a
                    href={ApiClient.getDownloadUrl(asset.id)}
                    download
                    className="inline-flex items-center gap-1 text-[11px] text-orange-400 hover:text-orange-300 font-medium"
                  >
                    <Download className="h-3 w-3" />
                    <span>Download</span>
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-2xl">
            <h3 className="text-base font-bold text-white">Create New Project</h3>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Project Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., Autumn Cinematic Trailer"
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-orange-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Description</label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Brief summary of creative objectives..."
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-orange-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-medium text-xs transition-colors"
                >
                  {creating ? "Creating..." : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
