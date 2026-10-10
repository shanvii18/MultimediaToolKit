"use client";

import React, { useState } from "react";
import { X, Lock, Mail, ArrowRight, Sparkles, Layers } from "lucide-react";

interface SignInModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SignInModal({ isOpen, onClose }: SignInModalProps) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("Redirecting to your active workspace...");
    setTimeout(() => {
      onClose();
      setStatus(null);
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div
        className="relative w-full max-w-md rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 md:p-8 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="absolute top-0 left-0 right-0 h-1.5 stripe-gradient-mesh" />

        <div className="flex items-center justify-between pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg stripe-gradient-mesh flex items-center justify-center text-white font-bold text-sm shadow-md">
              <Layers className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-slate-900 dark:text-white">
              Multimedia<span className="text-stripe-orange font-medium">ToolKit</span>
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mt-4">
          <h3 className="text-xl font-semibold text-slate-900 dark:text-white tracking-tight">
            Sign in to your workspace
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-normal">
            Access your processed multimedia libraries, transcripts, and study notes.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                University / Work Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  placeholder="student@university.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-stripe-orange transition-all font-normal"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-stripe-orange transition-all font-normal"
                />
              </div>
            </div>

            {status && (
              <div className="p-2.5 rounded-lg bg-stripe-orange/10 text-stripe-orange text-xs font-medium flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5" />
                <span>{status}</span>
              </div>
            )}

            <button
              type="submit"
              className="w-full py-2.5 px-4 text-sm font-medium rounded-lg bg-gradient-to-r from-stripe-orange to-stripe-coral hover:brightness-105 text-white transition-all shadow-md shadow-stripe-orange/20 flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>Continue to Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 text-center">
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-normal">
              Day 1 Scaffolding Demo • Authentication modules connect in Phase 2
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
