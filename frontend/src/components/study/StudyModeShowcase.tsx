"use client";

import React, { useState } from "react";
import {
  BookOpen,
  FileText,
  Key,
  HelpCircle,
  Zap,
  Clock,
  RotateCw,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

export function StudyModeShowcase() {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [flashcardFlipped, setFlashcardFlipped] = useState(false);
  const [currentFlashcardIndex, setCurrentFlashcardIndex] = useState(0);

  const tabs = [
    { id: 0, label: "Detailed Notes", icon: BookOpen },
    { id: 1, label: "Summary", icon: FileText },
    { id: 2, label: "Key Concepts", icon: Key },
    { id: 3, label: "Exam Questions", icon: HelpCircle },
    { id: 4, label: "Flashcards", icon: Zap },
    { id: 5, label: "Crash Revision", icon: Clock },
  ];

  const flashcards = [
    {
      q: "What is the primary objective of stochastic gradient descent with momentum?",
      a: "Momentum accumulates past velocity vectors to accelerate along consistent gradient directions while dampening oscillations along high-curvature ravines.",
      tag: "Optimization Core",
    },
    {
      q: "Why does mini-batch gradient noise act as implicit regularization?",
      a: "The variance introduced by sampling random sub-batches prevents gradient trajectories from getting trapped in sharp, non-generalizing local minima.",
      tag: "Generalization",
    },
    {
      q: "How does learning rate warmup stabilize early training dynamics?",
      a: "It holds weight updates modest when momentum and adaptive variance estimators (like in AdamW) are uncalibrated and volatile.",
      tag: "Hyperparameters",
    },
  ];

  const nextFlashcard = () => {
    setFlashcardFlipped(false);
    setCurrentFlashcardIndex((prev) => (prev + 1) % flashcards.length);
  };

  const prevFlashcard = () => {
    setFlashcardFlipped(false);
    setCurrentFlashcardIndex((prev) => (prev - 1 + flashcards.length) % flashcards.length);
  };

  return (
    <section id="study-mode" className="relative py-24 md:py-32 overflow-hidden">
      {/* Ambient Backdrop */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[850px] h-[550px] bg-gradient-to-tr from-stripe-orange/15 via-stripe-coral/15 to-stripe-pink/15 blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header with refined lightweight typography */}
        <div className="text-center max-w-3xl mx-auto mb-12 md:mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-stripe-coral/10 text-stripe-coral border border-stripe-coral/20 mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Interactive Module • AI Study Mode</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-[-0.03em] text-slate-900 dark:text-white">
            Meet your new study companion.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-slate-600 dark:text-slate-300 font-normal">
            Switch effortlessly between comprehensive textbook notes, high-yield summaries,
            interactive flashcards, and simulated examination questions.
          </p>
        </div>

        {/* Study Mode Interface Container */}
        <div className="rounded-2xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl overflow-hidden transition-all duration-300">
          {/* Tab Navigation Header */}
          <div className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/70 p-2 sm:p-3 overflow-x-auto">
            <div className="flex items-center gap-1.5 min-w-max">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveTab(tab.id);
                      setFlashcardFlipped(false);
                    }}
                    className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all cursor-pointer ${
                      isActive
                        ? "bg-white dark:bg-slate-900 text-stripe-coral shadow-sm border border-slate-200/80 dark:border-slate-800"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100/60 dark:hover:bg-slate-900/40"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Tab Panel Content */}
          <div className="p-6 md:p-10 min-h-[420px] flex flex-col justify-between">
            {/* TAB 0: Detailed Notes */}
            {activeTab === 0 && (
              <div className="space-y-6 animate-fade-in text-left">
                <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-stripe-coral font-semibold">
                    Section 4.1 • Optimization Fundamentals
                  </span>
                  <h3 className="text-xl sm:text-2xl font-normal tracking-[-0.02em] text-slate-900 dark:text-white mt-1">
                    Gradient Descent Dynamics in High-Dimensional Loss Landscapes
                  </h3>
                </div>

                <div className="prose dark:prose-invert max-w-none text-slate-600 dark:text-slate-300 space-y-4 text-sm leading-relaxed font-normal">
                  <p>
                    Standard gradient descent computes the exact analytical gradient over the entire training set.
                    While convergence is deterministic for convex functions, deep neural network loss surfaces feature an abundance
                    of saddle points, ravines, and plateaus where eigenvalues of the Hessian matrix take differing signs.
                  </p>

                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                    <h4 className="font-semibold text-slate-900 dark:text-white text-xs uppercase tracking-wider mb-2">
                      Key Mathematical Expression
                    </h4>
                    <code className="text-xs font-mono text-stripe-coral dark:text-stripe-peach block bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200/60 dark:border-slate-800">
                      θ_(t+1) = θ_t - η · ∇L(θ_t; x_(i:i+n), y_(i:i+n)) + β(θ_t - θ_(t-1))
                    </code>
                  </div>

                  <p>
                    By introducing a momentum parameter β (typically 0.9), updates accumulate velocity in dimensions with persistent
                    gradients while canceling out orthogonal oscillations across ravine walls.
                  </p>
                </div>
              </div>
            )}

            {/* TAB 1: Summary */}
            {activeTab === 1 && (
              <div className="space-y-5 animate-fade-in text-left">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                  <h3 className="text-xl font-normal tracking-tight text-slate-900 dark:text-white">
                    Executive 5-Minute Summary
                  </h3>
                  <span className="text-xs font-medium text-emerald-500 bg-emerald-500/10 px-2.5 py-0.5 rounded-full">
                    95% Reading Time Saved
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                  <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60">
                    <div className="text-xs font-semibold text-stripe-orange mb-1">
                      01. The Problem
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                      Standard gradient descent oscillates heavily in ill-conditioned loss ravines and stalls indefinitely at high-dimensional saddle points.
                    </p>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60">
                    <div className="text-xs font-semibold text-stripe-coral mb-1">
                      02. The Solution
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                      Momentum adds physical inertia to parameter updates, accelerating along consistent slopes and canceling high-frequency noise.
                    </p>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60">
                    <div className="text-xs font-semibold text-stripe-pink mb-1">
                      03. Best Practice
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                      Always pair with learning rate warmup (first 5–10 epochs) to prevent instability before momentum velocity vectors stabilize.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Key Concepts */}
            {activeTab === 2 && (
              <div className="space-y-4 animate-fade-in text-left">
                <h3 className="text-xl font-normal tracking-tight text-slate-900 dark:text-white mb-4">
                  High-Yield Core Concepts
                </h3>

                <div className="space-y-3">
                  {[
                    { title: "Hessian Eigenvalue Conditioning", desc: "The ratio of maximum to minimum eigenvalues determines curvature steepness. Ill-conditioned ratios cause severe zig-zagging in vanilla GD." },
                    { title: "Nesterov Accelerated Gradient (NAG)", desc: "Evaluates the gradient of the lookahead position θ + βv rather than the current position, offering predictive braking before overshooting." },
                    { title: "Implicit Batch Regularization", desc: "Mini-batch sampling injects noise that statistically prevents models from overfitting sharp minima, biasing parameters toward flat, robust basins." },
                  ].map((concept, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 flex items-start gap-3"
                    >
                      <div className="w-6 h-6 rounded-lg bg-stripe-coral/10 text-stripe-coral flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                        {idx + 1}
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                          {concept.title}
                        </h4>
                        <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed font-normal">
                          {concept.desc}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 3: Exam Questions */}
            {activeTab === 3 && (
              <div className="space-y-4 animate-fade-in text-left">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                  <h3 className="text-xl font-normal tracking-tight text-slate-900 dark:text-white">
                    Simulated Midterm & Final Questions
                  </h3>
                  <span className="text-xs text-slate-400 font-mono">
                    3 Practice Prompts Generated
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-stripe-orange bg-stripe-orange/10 px-2 py-0.5 rounded">
                      Multiple Choice (Exam Probable)
                    </span>
                    <p className="text-xs font-medium text-slate-900 dark:text-white mt-2">
                      Which of the following describes the difference between vanilla momentum and Nesterov momentum?
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      A) Nesterov evaluates gradient at predicted lookahead position.
                    </p>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-stripe-coral bg-stripe-coral/10 px-2 py-0.5 rounded">
                      Mathematical Derivation Prompt
                    </span>
                    <p className="text-xs font-medium text-slate-900 dark:text-white mt-2">
                      Derive the effective learning rate scaling factor when mini-batch size B is increased by factor k.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: Flashcards (Interactive Flip & Navigation) */}
            {activeTab === 4 && (
              <div className="flex flex-col items-center justify-center space-y-6 py-4 animate-fade-in">
                <div className="flex items-center justify-between w-full max-w-lg text-xs text-slate-400">
                  <span className="font-semibold text-stripe-coral">
                    Card {currentFlashcardIndex + 1} of {flashcards.length}
                  </span>
                  <span>{flashcards[currentFlashcardIndex].tag}</span>
                </div>

                {/* Flippable 3D Card */}
                <div
                  onClick={() => setFlashcardFlipped(!flashcardFlipped)}
                  className="w-full max-w-lg min-h-[220px] rounded-2xl border border-slate-200 dark:border-slate-700/80 bg-gradient-to-br from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 p-6 sm:p-8 shadow-lg cursor-pointer flex flex-col justify-between transition-transform duration-300 hover:scale-[1.01] text-center"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="font-mono uppercase font-semibold text-stripe-coral">
                      {flashcardFlipped ? "Answer" : "Question"}
                    </span>
                    <span className="flex items-center gap-1">
                      <RotateCw className="w-3 h-3" /> Click to flip
                    </span>
                  </div>

                  <div className="my-auto py-4">
                    <p className="text-base sm:text-lg font-medium text-slate-900 dark:text-white leading-relaxed">
                      {flashcardFlipped
                        ? flashcards[currentFlashcardIndex].a
                        : flashcards[currentFlashcardIndex].q}
                    </p>
                  </div>

                  <div className="text-[11px] text-slate-400">
                    {flashcardFlipped
                      ? "Got it right? Practice again anytime."
                      : "Think through the answer before revealing"}
                  </div>
                </div>

                {/* Flashcard Navigation Controls */}
                <div className="flex items-center gap-4">
                  <button
                    onClick={prevFlashcard}
                    className="p-2.5 rounded-full border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                    aria-label="Previous card"
                  >
                    <ChevronLeft className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                  </button>
                  <button
                    onClick={() => setFlashcardFlipped(!flashcardFlipped)}
                    className="px-5 py-2 rounded-full text-xs font-semibold bg-gradient-to-r from-stripe-orange to-stripe-coral text-white hover:brightness-105 transition-all shadow-md cursor-pointer"
                  >
                    {flashcardFlipped ? "Show Question" : "Reveal Answer"}
                  </button>
                  <button
                    onClick={nextFlashcard}
                    className="p-2.5 rounded-full border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                    aria-label="Next card"
                  >
                    <ChevronRight className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                  </button>
                </div>
              </div>
            )}

            {/* TAB 5: Crash Revision */}
            {activeTab === 5 && (
              <div className="space-y-4 animate-fade-in text-left">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                  <h3 className="text-xl font-normal tracking-tight text-slate-900 dark:text-white">
                    Crash Revision (Last 60 Minutes Pre-Exam)
                  </h3>
                  <span className="text-xs font-semibold text-stripe-coral bg-stripe-coral/10 px-2.5 py-0.5 rounded-full">
                    High Recall
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60">
                    <span className="font-semibold text-slate-900 dark:text-white block mb-1">
                      ⚡ Momentum formula:
                    </span>
                    <code className="text-stripe-coral font-mono text-[11px]">
                      v = βv + η∇L; θ = θ - v
                    </code>
                  </div>

                  <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60">
                    <span className="font-semibold text-slate-900 dark:text-white block mb-1">
                      ⚡ Best momentum factor:
                    </span>
                    <span className="text-slate-600 dark:text-slate-300">
                      β = 0.9 (or 0.99 for deep residual architectures).
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60">
                    <span className="font-semibold text-slate-900 dark:text-white block mb-1">
                      ⚡ Saddle points:
                    </span>
                    <span className="text-slate-600 dark:text-slate-300">
                      Noise from SGD pushes trajectory along negative curvature eigenvectors.
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60">
                    <span className="font-semibold text-slate-900 dark:text-white block mb-1">
                      ⚡ Warmup role:
                    </span>
                    <span className="text-slate-600 dark:text-slate-300">
                      Low initial LR stabilizes gradients before second-moment estimates converge.
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Bottom Panel Metadata */}
            <div className="mt-8 pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Generated from 45 min lecture recording & 1 whiteboard slide</span>
              </div>
              <span className="text-stripe-coral font-semibold">
                Export to Anki / Notion / Obsidian
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
