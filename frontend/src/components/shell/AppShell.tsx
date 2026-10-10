"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Layers,
  LayoutDashboard,
  Grid,
  FolderKanban,
  Activity,
  ChevronLeft,
  ChevronRight,
  Server,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { ApiClient } from "@/services/apiClient";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let isMounted = true;
    ApiClient.getHealth()
      .then((res) => {
        if (isMounted) {
          setBackendStatus(res.status === "ok" ? "online" : "offline");
        }
      })
      .catch(() => {
        if (isMounted) {
          setBackendStatus("offline");
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const navItems = [
    { label: "Dashboard", href: "/", icon: LayoutDashboard },
    { label: "Idea & Creation Studio", href: "/workspace", icon: Sparkles },
    { label: "20 Modules Directory", href: "/modules", icon: Grid },
    { label: "Projects & Assets", href: "/projects", icon: FolderKanban },
    { label: "Job Monitor & Export", href: "/jobs", icon: Activity },
  ];

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100 antialiased selection:bg-orange-500 selection:text-white">
      {/* Sidebar */}
      <aside
        className={`transition-all duration-300 border-r border-slate-800 bg-slate-900/60 backdrop-blur-xl flex flex-col z-40 ${
          collapsed ? "w-20" : "w-64"
        }`}
      >
        {/* Brand header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80">
          <Link href="/" className="flex items-center gap-3 overflow-hidden">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-orange-500 via-amber-500 to-rose-500 flex items-center justify-center shadow-lg shadow-orange-500/20 shrink-0">
              <Layers className="h-5 w-5 text-white" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-semibold text-sm tracking-tight text-white">MultimediaToolKit</span>
                <span className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">PPT Architecture</span>
              </div>
            )}
          </Link>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-orange-500/20 to-amber-500/10 text-orange-400 border border-orange-500/30 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon className={`h-5 w-5 shrink-0 ${isActive ? "text-orange-400" : "text-slate-400"}`} />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Backend Connectivity Status Widget */}
        <div className="p-3 border-t border-slate-800/80">
          <div
            className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs ${
              backendStatus === "online"
                ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/50"
                : backendStatus === "checking"
                ? "bg-amber-950/40 text-amber-400 border border-amber-800/50"
                : "bg-rose-950/40 text-rose-400 border border-rose-800/50"
            }`}
          >
            <Server className="h-3.5 w-3.5 shrink-0" />
            {!collapsed && (
              <div className="flex-1 flex items-center justify-between">
                <span>FastAPI API</span>
                <span className="font-mono text-[10px] uppercase font-semibold">
                  {backendStatus === "online" ? "● Online" : backendStatus === "checking" ? "Checking" : "Offline"}
                </span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main content frame */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 border-b border-slate-800 bg-slate-900/40 backdrop-blur-md flex items-center justify-between px-6 z-30">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-orange-500/10 text-orange-400 border border-orange-500/20">
              IDEA → UNDERSTAND → CREATE → POLISH → DELIVER
            </span>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-slate-400 hover:text-orange-400 transition-colors flex items-center gap-1 font-mono"
            >
              <span>Swagger API Docs</span>
              <ExternalLink className="h-3 w-3" />
            </a>
            <div className="h-4 w-px bg-slate-800" />
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-medium text-slate-300">
                ME
              </div>
              <span className="text-xs text-slate-300 font-medium hidden sm:inline">Engineer</span>
            </div>
          </div>
        </header>

        {/* Page body */}
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
