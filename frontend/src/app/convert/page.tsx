"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, AlertCircle, Loader2, RefreshCw, Shuffle } from "lucide-react";
import { ApiClient, BackendStatus, describeError } from "@/services/apiClient";
import { Conversion, MediaFormat } from "@/types";
import { FormatIcon, FORMAT_LABELS, StatusBadge } from "@/components/convert/ConvertUi";

const FORMATS: MediaFormat[] = ["text", "image", "audio", "video", "animation"];

export default function ConvertCatalogPage() {
  const [conversions, setConversions] = useState<Conversion[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [waking, setWaking] = useState(false);

  const load = React.useCallback(() => {
    setError(null);
    ApiClient.listConversions()
      .then((list) => {
        setConversions(list);
        setError(null);
      })
      .catch((e) => setError(describeError(e)));
  }, []);

  useEffect(() => {
    load();
    // Requests are retried automatically while the server wakes up; reload as soon as it is back.
    const onStatus = (e: Event) => {
      const status = (e as CustomEvent<BackendStatus>).detail;
      setWaking(status === "waking");
      if (status === "online") setConversions((current) => {
        if (!current) load();
        return current;
      });
    };
    window.addEventListener("mtk:backend-status", onStatus);
    return () => window.removeEventListener("mtk:backend-status", onStatus);
  }, [load]);

  const bySource = useMemo(() => {
    const map: Record<string, Conversion[]> = {};
    (conversions || []).forEach((c) => {
      (map[c.source] = map[c.source] || []).push(c);
    });
    return map;
  }, [conversions]);

  const availableCount = (conversions || []).filter((c) => c.status === "available").length;

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Shuffle className="h-6 w-6 text-orange-400" />
          <span>Convert Media</span>
        </h1>
        <p className="text-sm text-slate-400 max-w-3xl">
          Five formats, twenty directed conversions. Status comes live from the processing server: only
          conversions marked <span className="text-emerald-400 font-medium">Available</span> run real engines.
          Everything else is honestly marked <span className="text-slate-300 font-medium">Coming soon</span>.
        </p>
        {conversions && (
          <p className="text-xs text-slate-500 font-mono">
            {availableCount} of {conversions.length} conversions available on this server
          </p>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0" />
          <span className="flex-1">{error}</span>
          <button
            onClick={load}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-900/50 hover:bg-rose-900 text-rose-100 text-xs font-medium"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Retry
          </button>
        </div>
      )}

      {!conversions && !error && (
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <Loader2 className="h-4 w-4 animate-spin" />{" "}
          {waking ? "Waking up the processing server (free hosting sleeps when idle, about a minute)…" : "Loading conversions…"}
        </div>
      )}

      {conversions &&
        FORMATS.map((source) => (
          <section key={source} className="space-y-3">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <FormatIcon format={source} className="h-4 w-4 text-orange-400" />
              <span>From {FORMAT_LABELS[source]}</span>
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              {(bySource[source] || []).map((c) => {
                const runnable = c.status !== "coming_soon";
                const card = (
                  <div
                    className={`h-full p-5 rounded-2xl border space-y-3 transition-all ${
                      runnable
                        ? "bg-slate-900/60 border-slate-800 hover:border-orange-500/50 hover:bg-slate-900"
                        : "bg-slate-900/30 border-slate-800/60 opacity-70"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 text-white font-semibold text-sm">
                        <FormatIcon format={c.source} className="h-4 w-4 text-slate-400" />
                        <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
                        <FormatIcon format={c.target} className="h-4 w-4 text-orange-400" />
                        <span>{c.title}</span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{c.description}</p>
                    <StatusBadge status={c.status} />
                  </div>
                );
                return runnable ? (
                  <Link key={c.id} href={`/convert/${c.id}`}>
                    {card}
                  </Link>
                ) : (
                  <div key={c.id}>{card}</div>
                );
              })}
            </div>
          </section>
        ))}
    </div>
  );
}
