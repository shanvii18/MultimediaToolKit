"use client";

import React from "react";
import { ArrowRight, ArrowDownRight, Sparkles, Check } from "lucide-react";

interface FinalCtaProps {
  onOpenUpload: () => void;
}

export function FinalCta({ onOpenUpload }: FinalCtaProps) {
  return (
    <section className="relative py-24 md:py-36 overflow-hidden">
      {/* Stripe-Inspired Radiant Orange-Coral-Pink Ambient Ribbon Field */}
      <div className="absolute inset-x-0 top-0 bottom-0 pointer-events-none -z-10 flex items-center justify-center overflow-hidden">
        <div className="w-[850px] lg:w-[1200px] h-[550px] rounded-full bg-gradient-to-tr from-stripe-amber/35 via-stripe-orange/40 to-stripe-coral/40 blur-[150px] opacity-80" />
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-stripe-orange/10 text-stripe-orange border border-stripe-orange/20 backdrop-blur mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Ready to Transform Your Media?</span>
        </div>

        <h2 className="text-4xl sm:text-5xl md:text-6xl font-normal tracking-[-0.03em] text-slate-900 dark:text-white leading-[1.08]">
          Turn your content into <br />
          <span className="stripe-text-gradient font-medium">something useful.</span>
        </h2>

        <p className="mt-6 text-base sm:text-lg md:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
          From unindexed lectures and scattered voice notes to searchable, structured academic companion materials in minutes.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={onOpenUpload}
            className="w-full sm:w-auto px-8 py-3.5 rounded-lg text-sm font-medium text-white bg-gradient-to-r from-stripe-orange via-stripe-coral to-stripe-pink hover:brightness-105 transition-all shadow-lg shadow-stripe-orange/25 flex items-center justify-center gap-2 group cursor-pointer"
          >
            <span>Start creating</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>

          <a
            href="#workspace-preview"
            className="w-full sm:w-auto px-6 py-3.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-stripe-orange transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <span>Explore workspace</span>
            <ArrowDownRight className="w-4 h-4" />
          </a>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1.5">
            <Check className="w-3.5 h-3.5 text-emerald-500" />
            No credit card or setup required
          </span>
          <span className="flex items-center gap-1.5">
            <Check className="w-3.5 h-3.5 text-emerald-500" />
            Instant browser workspace preview
          </span>
          <span className="flex items-center gap-1.5">
            <Check className="w-3.5 h-3.5 text-emerald-500" />
            Exportable to Anki & Notion
          </span>
        </div>
      </div>
    </section>
  );
}
