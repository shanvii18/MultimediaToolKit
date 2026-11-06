"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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
  Shuffle,
  Menu,
  X,
  Sun,
  Moon,
  LogIn,
  LogOut,
  KeyRound,
} from "lucide-react";
import { ApiClient, API_BASE, Me } from "@/services/apiClient";

interface AppShellProps {
  children: React.ReactNode;
}

type Theme = "dark" | "light";

function currentTheme(): Theme {
  if (typeof document === "undefined") return "dark";
  return document.documentElement.classList.contains("light") ? "light" : "dark";
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>("dark");
  const [me, setMe] = useState<Me | null>(null);
  const [needsSignIn, setNeedsSignIn] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  const loadMe = useCallback(() => {
    ApiClient.getMe()
      .then((user) => {
        setMe(user);
        setNeedsSignIn(false);
      })
      .catch(() => setMe(null));
  }, []);

  useEffect(() => {
    setTheme(currentTheme());
    let isMounted = true;
    ApiClient.getHealth()
      .then((res) => isMounted && setBackendStatus(res.status === "ok" ? "online" : "offline"))
      .catch(() => isMounted && setBackendStatus("offline"));
    loadMe();

    const onUnauthorized = () => setNeedsSignIn(true);
    const onSignedIn = () => loadMe();
    window.addEventListener("mtk:unauthorized", onUnauthorized);
    window.addEventListener("mtk:signed-in", onSignedIn);
    return () => {
      isMounted = false;
      window.removeEventListener("mtk:unauthorized", onUnauthorized);
      window.removeEventListener("mtk:signed-in", onSignedIn);
    };
  }, [loadMe]);

  useEffect(() => setMobileOpen(false), [pathname]);

  const toggleTheme = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    const cl = document.documentElement.classList;
    cl.remove("dark", "light");
    cl.add(next);
    try {
      localStorage.setItem("mtk_theme", next);
    } catch (_) {}
    setTheme(next);
  };

  const signOut = () => {
    ApiClient.clearAccessKey();
    setMe(null);
    router.push("/login");
  };

  const navItems = [
    { label: "Dashboard", href: "/", icon: LayoutDashboard },
    { label: "Convert Media", href: "/convert", icon: Shuffle },
    { label: "Idea & Creation Studio", href: "/workspace", icon: Sparkles },
    { label: "Modules Directory", href: "/modules", icon: Grid },
    { label: "Projects & Media Library", href: "/projects", icon: FolderKanban },
    { label: "Conversion History", href: "/jobs", icon: Activity },
  ];

  const isDevUser = me?.auth_mode === "dev_open" && me.email.endsWith("@localhost");
  const sidebarWide = !collapsed || mobileOpen;

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100 antialiased selection:bg-orange-500 selection:text-white">
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setMobileOpen(false)} aria-hidden />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 transition-all duration-300 border-r border-slate-800 bg-slate-900/95 lg:bg-slate-900/60 backdrop-blur-xl flex flex-col z-50 ${
          sidebarWide ? "w-64" : "w-20"
        } ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80">
          <Link href="/" className="flex items-center gap-3 overflow-hidden">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-orange-500 via-amber-500 to-rose-500 flex items-center justify-center shadow-lg shadow-orange-500/20 shrink-0">
              <Layers className="h-5 w-5 text-white" />
            </div>
            {sidebarWide && (
              <div className="flex flex-col">
                <span className="font-semibold text-sm tracking-tight text-white">MultimediaToolKit</span>
                <span className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">20 conversions</span>
              </div>
            )}
          </Link>
          <button
            onClick={() => (mobileOpen ? setMobileOpen(false) : setCollapsed(!collapsed))}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
            title={mobileOpen ? "Close menu" : collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {mobileOpen ? <X className="h-4 w-4" /> : collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href + "/"));
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
                title={!sidebarWide ? item.label : undefined}
              >
                <Icon className={`h-5 w-5 shrink-0 ${isActive ? "text-orange-400" : "text-slate-400"}`} />
                {sidebarWide && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

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
            {sidebarWide && (
              <div className="flex-1 flex items-center justify-between">
                <span>Processing API</span>
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
        <header className="h-16 border-b border-slate-800 bg-slate-900/40 backdrop-blur-md flex items-center justify-between px-4 sm:px-6 z-30 gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <button
              className="lg:hidden p-2 rounded-lg text-slate-300 hover:bg-slate-800/60"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="hidden md:inline text-xs font-mono px-2.5 py-1 rounded-md bg-orange-500/10 text-orange-400 border border-orange-500/20 truncate">
              TEXT · IMAGE · AUDIO · VIDEO · ANIMATION
            </span>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <a
              href={`${API_BASE}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:flex text-xs text-slate-400 hover:text-orange-400 transition-colors items-center gap-1 font-mono"
            >
              <span>API Docs</span>
              <ExternalLink className="h-3 w-3" />
            </a>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              aria-label="Toggle colour theme"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <div className="h-4 w-px bg-slate-800" />
            {me ? (
              <div className="flex items-center gap-2">
                <div className="h-7 w-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-medium text-slate-300 uppercase">
                  {me.email.slice(0, 2)}
                </div>
                <span className="text-xs text-slate-300 font-medium hidden sm:inline max-w-[12rem] truncate" title={me.email}>
                  {isDevUser ? "Local developer" : me.email}
                </span>
                {!isDevUser && (
                  <button onClick={signOut} className="p-1.5 rounded-lg text-slate-400 hover:text-white" title="Sign out">
                    <LogOut className="h-4 w-4" />
                  </button>
                )}
              </div>
            ) : (
              <Link href="/login" className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white">
                <LogIn className="h-4 w-4" />
                <span>Sign in</span>
              </Link>
            )}
          </div>
        </header>

        {needsSignIn && pathname !== "/login" && (
          <div className="px-4 sm:px-6 py-3 bg-amber-950/40 border-b border-amber-800/50 text-amber-300 text-sm flex flex-wrap items-center gap-3">
            <KeyRound className="h-4 w-4 shrink-0" />
            <span>MultimediaToolKit is invite-only. Sign in with your personal access key to see your files.</span>
            <Link href="/login" className="underline font-medium">
              Sign in
            </Link>
          </div>
        )}

        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
