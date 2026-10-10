"use client";

import React, { useState } from "react";
import { AudioWaveform } from "@/components/ui/AudioWaveform";
import { FileAudio, Search, Clock, User, ArrowRight, Filter, Volume2 } from "lucide-react";

export function AudioToTextSection() {
  const [filterSpeaker, setFilterSpeaker] = useState<string>("All");
  const [searchTerm, setSearchTerm] = useState("eigenvalues");
  const [isWavePlaying, setIsWavePlaying] = useState(true);

  const segments = [
    {
      time: "02:14",
      speaker: "Dr. Vance",
      role: "Speaker 1",
      text: "When we compute the principal components of the covariance matrix, the highest eigenvalues represent maximal variance directions.",
      highlight: "eigenvalues",
    },
    {
      time: "02:45",
      speaker: "Marcus",
      role: "Student",
      text: "So the corresponding eigenvector becomes the projection vector for dimensional reduction?",
      highlight: "eigenvector",
    },
    {
      time: "03:10",
      speaker: "Dr. Vance",
      role: "Speaker 1",
      text: "Exactly. By discarding smaller eigenvalues, we eliminate noise while preserving signal integrity.",
      highlight: "eigenvalues",
    },
    {
      time: "03:40",
      speaker: "Dr. Vance",
      role: "Speaker 1",
      text: "This geometric intuition underpins modern spectral embeddings in multimedia clustering.",
      highlight: null,
    },
  ];

  const filtered = segments.filter((seg) => {
    const matchSpeaker = filterSpeaker === "All" || seg.speaker === filterSpeaker;
    const matchSearch = searchTerm === "" || seg.text.toLowerCase().includes(searchTerm.toLowerCase());
    return matchSpeaker && matchSearch;
  });

  return (
    <section id="audio-to-text" className="relative py-20 md:py-28 overflow-hidden">
      {/* Violet & Coral Ambient Light */}
      <div className="absolute top-1/2 -right-40 w-[600px] h-[600px] bg-gradient-to-bl from-stripe-coral/20 via-stripe-pink/15 to-transparent blur-[130px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          {/* Left Column: Editorial Copy (Matching Screenshot 1 typography) */}
          <div className="lg:col-span-5 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-stripe-coral/10 text-stripe-coral border border-stripe-coral/20">
              <FileAudio className="w-3.5 h-3.5" />
              <span>Module 02 • Audio to Text</span>
            </div>

            <h2 className="text-3xl sm:text-4xl md:text-5xl font-normal tracking-[-0.03em] text-slate-900 dark:text-white leading-tight">
              Find the words that matter.
            </h2>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
              Transform hours of speech into an indexed, searchable textual record.
              Timestamp-accurate transcription with automated speaker diarization and instant keyword navigation.
            </p>

            <div className="space-y-4 pt-1">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-stripe-coral/10 text-stripe-coral flex items-center justify-center shrink-0 mt-0.5">
                  <Clock className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                    Millisecond-Precision Timestamps
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Click any sentence or keyword to jump directly to that exact moment in playback.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-stripe-pink/10 text-stripe-pink flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                    Multi-Speaker Diarization
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Separates professors, interviewees, and student questions automatically.
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-2">
              <a
                href="#image-to-text"
                className="inline-flex items-center gap-2 text-sm font-medium text-stripe-coral hover:text-stripe-orange transition-colors"
              >
                <span>See how document OCR extracts visual slides</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Right Column: Visual Composition (Live Waveform morphing into transcript) */}
          <div className="lg:col-span-7">
            <div className="relative rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xl overflow-hidden">
              {/* Header Visual: LIVE Waveform Morphing Ribbon (Requirement 5) */}
              <div className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 mb-5">
                <div className="flex items-center justify-between text-xs mb-2.5">
                  <span className="font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <Volume2 className="w-3.5 h-3.5 text-stripe-coral" />
                    Acoustic Waveform Analysis
                  </span>
                  <span className="text-[10px] text-stripe-coral font-mono font-semibold">
                    Confidence: 99.4%
                  </span>
                </div>

                {/* LIVE Waveform Visualizer */}
                <div className="p-2.5 bg-white dark:bg-slate-900 rounded-lg border border-slate-200/60 dark:border-slate-800 flex items-center gap-3">
                  <div className="flex-1">
                    <AudioWaveform
                      isPlaying={isWavePlaying}
                      barCount={26}
                      heightClass="h-7"
                      colorScheme="coral-pink"
                    />
                  </div>
                  <div className="text-slate-300 dark:text-slate-600 font-mono text-xs">
                    ➔
                  </div>
                  <div className="flex-1 font-mono text-xs text-stripe-coral font-medium tracking-wide truncate">
                    "When we compute principal components..."
                  </div>
                </div>
              </div>

              {/* Interactive Searchable Transcript Interface */}
              <div className="space-y-4">
                {/* Search & Speaker Filter Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
                  <div className="relative flex-1">
                    <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      placeholder="Search within speech..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-stripe-coral"
                    />
                  </div>

                  <div className="flex items-center gap-1.5 text-xs">
                    <Filter className="w-3 h-3 text-slate-400" />
                    <span className="text-slate-400 text-[11px]">Speaker:</span>
                    {["All", "Dr. Vance", "Marcus"].map((spk) => (
                      <button
                        key={spk}
                        onClick={() => setFilterSpeaker(spk)}
                        className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                          filterSpeaker === spk
                            ? "bg-stripe-coral text-white"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                        }`}
                      >
                        {spk}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Transcript Sentences */}
                <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
                  {filtered.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50/60 dark:bg-slate-950/40 hover:border-stripe-coral/40 transition-colors"
                    >
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900 dark:text-white">
                            {item.speaker}
                          </span>
                          <span className="text-[10px] text-slate-400 px-1.5 py-0.2 rounded bg-slate-200/60 dark:bg-slate-800">
                            {item.role}
                          </span>
                        </div>
                        <span className="font-mono text-xs font-semibold text-stripe-coral bg-stripe-coral/10 px-2 py-0.5 rounded">
                          {item.time}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                        {item.text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
