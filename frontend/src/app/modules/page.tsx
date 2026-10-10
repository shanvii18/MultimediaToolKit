"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Search, Filter, ArrowUpRight, CheckCircle2, Clock, Sparkles } from "lucide-react";
import { TOOLKIT_MODULES } from "@/services/modulesCatalog";
import { ModuleGroup } from "@/types";

export default function ModulesDirectoryPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedGroup, setSelectedGroup] = useState<string>("All");

  const groups: string[] = [
    "All",
    "Conversion & Utilities",
    "Audio, Video & Media Understanding",
    "Generative AI Creative Studio",
    "Idea-to-Content Workflow",
    "Workspace & Delivery",
  ];

  const filteredModules = TOOLKIT_MODULES.filter((mod) => {
    const matchesSearch =
      mod.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      mod.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      mod.id.includes(searchQuery);
    const matchesGroup = selectedGroup === "All" || mod.group === selectedGroup;
    return matchesSearch && matchesGroup;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-mono">
          <span>Complete Platform Roadmap</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">The 20 Modules Directory</h1>
        <p className="text-sm text-slate-400 max-w-2xl">
          Direct implementation of all 20 modules defined in the PowerPoint Blueprint. Explore operational tools, integrated utilities, and upcoming cloud roadmap engines.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by module name, id, or feature..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 transition-colors"
          />
        </div>

        {/* Group Filter pills */}
        <div className="flex flex-wrap gap-2">
          {groups.map((grp) => (
            <button
              key={grp}
              onClick={() => setSelectedGroup(grp)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedGroup === grp
                  ? "bg-orange-500 text-white shadow-md shadow-orange-500/20"
                  : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {grp}
            </button>
          ))}
        </div>
      </div>

      {/* Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredModules.map((mod) => (
          <div
            key={mod.id}
            className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between space-y-4 group"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-orange-400">MODULE #{mod.id}</span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-md ${
                    mod.status === "operational"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : mod.status === "integrated"
                      ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                      : "bg-slate-800 text-slate-400 border border-slate-700"
                  }`}
                >
                  {mod.statusLabel}
                </span>
              </div>

              <h3 className="text-base font-bold text-white group-hover:text-orange-400 transition-colors">
                {mod.name}
              </h3>

              <p className="text-xs text-slate-400 leading-relaxed">{mod.description}</p>
            </div>

            <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs">
              <span className="text-[11px] text-slate-500 font-medium">{mod.group}</span>
              <Link
                href={`/workspace?tool=${mod.slug}`}
                className="inline-flex items-center gap-1 text-orange-400 hover:text-orange-300 font-medium"
              >
                <span>Launch</span>
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
