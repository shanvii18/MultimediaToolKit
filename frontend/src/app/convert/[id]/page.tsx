"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Download,
  Loader2,
  Play,
  Upload,
} from "lucide-react";
import { ApiClient } from "@/services/apiClient";
import { Asset, Conversion, ConversionParam, Job } from "@/types";
import { FormatIcon, StatusBadge, formatBytes } from "@/components/convert/ConvertUi";

const TERMINAL = new Set(["succeeded", "failed", "cancelled"]);
const VIDEO_EXT = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"];

function extOf(name: string): string {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i).toLowerCase() : "";
}

function initialValues(conversion: Conversion): Record<string, any> {
  const values: Record<string, any> = {};
  conversion.params.forEach((p) => {
    values[p.name] = p.default ?? (p.type === "boolean" ? false : "");
  });
  return values;
}

export default function ConversionWorkspacePage() {
  const params = useParams<{ id: string }>();
  const conversionId = params?.id;

  const [conversion, setConversion] = useState<Conversion | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [modeId, setModeId] = useState<string>("");
  const [values, setValues] = useState<Record<string, any>>({});
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Load the conversion spec from the backend registry
  useEffect(() => {
    if (!conversionId) return;
    ApiClient.listConversions()
      .then((all) => {
        const found = all.find((c) => c.id === conversionId);
        if (!found) {
          setLoadError(`Unknown conversion "${conversionId}".`);
          return;
        }
        setConversion(found);
        setValues(initialValues(found));
        const firstRunnable = found.modes.find((m) => m.status === "available") || found.modes[0];
        setModeId(firstRunnable?.id || "");
      })
      .catch((e) => setLoadError(e.message || "Could not load conversion."));
  }, [conversionId]);

  // Local preview (video scrubbing for frame picking, image preview)
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // Poll the running job
  useEffect(() => {
    if (!job || TERMINAL.has(job.status)) return;
    const timer = setInterval(async () => {
      try {
        setJob(await ApiClient.getJob(job.id));
      } catch (e: any) {
        setError(e.message);
      }
    }, 1500);
    return () => clearInterval(timer);
  }, [job]);

  const mode = conversion?.modes.find((m) => m.id === modeId);
  const visibleParams = useMemo(
    () => (conversion?.params || []).filter((p) => !p.modes || p.modes.includes(modeId)),
    [conversion, modeId]
  );
  const textParam = visibleParams.find((p) => p.name === "text");
  const otherParams = visibleParams.filter((p) => p.name !== "text");
  const needsFile = conversion?.input_kind === "file";
  const allowsFile = conversion?.input_kind !== "text";
  const isVideoFile = file ? VIDEO_EXT.includes(extOf(file.name)) : false;
  const isImageFile = file ? file.type.startsWith("image/") : false;
  const running = submitting || (job !== null && !TERMINAL.has(job.status));

  const setValue = (name: string, value: any) => setValues((v) => ({ ...v, [name]: value }));

  const handleFile = (f: File | null) => {
    setError(null);
    if (f && conversion && conversion.accepted_extensions.length > 0) {
      const ext = extOf(f.name);
      if (!conversion.accepted_extensions.includes(ext)) {
        setError(`This conversion accepts ${conversion.accepted_extensions.join(", ")} files.`);
        setFile(null);
        return;
      }
    }
    setFile(f);
  };

  const submit = async () => {
    if (!conversion || !mode) return;
    setError(null);
    setJob(null);
    if (needsFile && !file) {
      setError("Choose an input file first.");
      return;
    }
    setSubmitting(true);
    try {
      const inputIds: string[] = [];
      if (file && allowsFile) {
        const asset = await ApiClient.uploadMedia(file);
        inputIds.push(asset.id);
      }
      const payload: Record<string, any> = { mode: mode.id };
      visibleParams.forEach((p) => {
        if (p.name === "text" && file) return; // the uploaded file wins over the text box
        payload[p.name] = values[p.name];
      });
      setJob(await ApiClient.createJob(conversion.id, inputIds, payload));
    } catch (e: any) {
      setError(e.message || "Could not start the conversion.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loadError) {
    return (
      <div className="space-y-4">
        <Link href="/convert" className="text-xs text-slate-400 hover:text-white inline-flex items-center gap-1">
          <ArrowLeft className="h-3.5 w-3.5" /> All conversions
        </Link>
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm">{loadError}</div>
      </div>
    );
  }

  if (!conversion) {
    return (
      <div className="flex items-center gap-2 text-slate-400 text-sm">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading…
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-6">
      <Link href="/convert" className="text-xs text-slate-400 hover:text-white inline-flex items-center gap-1">
        <ArrowLeft className="h-3.5 w-3.5" /> All conversions
      </Link>

      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <FormatIcon format={conversion.source} className="h-6 w-6 text-slate-400" />
          <ArrowRight className="h-5 w-5 text-slate-500" />
          <FormatIcon format={conversion.target} className="h-6 w-6 text-orange-400" />
          <span>{conversion.title}</span>
        </h1>
        <p className="text-sm text-slate-400">{conversion.description}</p>
      </div>

      {conversion.status === "coming_soon" && (
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-300 text-sm">
          This conversion is coming soon. It is not implemented yet, so it cannot be run.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* ---------------- Input form ---------------- */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
          {/* Modes */}
          {conversion.modes.length > 1 && (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Mode</label>
              <div className="grid grid-cols-1 gap-2">
                {conversion.modes.map((m) => {
                  const selectable = m.status === "available";
                  return (
                    <button
                      key={m.id}
                      type="button"
                      disabled={!selectable || running}
                      onClick={() => setModeId(m.id)}
                      className={`text-left p-3 rounded-xl border transition-colors ${
                        modeId === m.id
                          ? "border-orange-500 bg-orange-500/10"
                          : "border-slate-800 bg-slate-950 hover:border-slate-700"
                      } ${!selectable ? "opacity-60 cursor-not-allowed" : ""}`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-white">{m.label}</span>
                        <StatusBadge status={m.status} reason={m.reason} />
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1">{m.description}</p>
                      {m.status === "unavailable" && m.reason && (
                        <p className="text-[11px] text-amber-300 mt-1">{m.reason}</p>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
          {conversion.modes.length === 1 && mode && mode.status === "unavailable" && (
            <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-800/50 text-amber-300 text-xs">
              {mode.reason}
            </div>
          )}

          {/* Text input */}
          {textParam && (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">{textParam.label}</label>
              <textarea
                rows={6}
                value={values.text || ""}
                maxLength={textParam.max_length || undefined}
                disabled={!!file || running}
                onChange={(e) => setValue("text", e.target.value)}
                placeholder="Type or paste text…"
                className="w-full p-3.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 disabled:opacity-50"
              />
              <p className="text-[11px] text-slate-500">
                {(values.text || "").length}/{textParam.max_length} characters. {textParam.help}
              </p>
            </div>
          )}

          {/* File input */}
          {allowsFile && conversion.accepted_extensions.length > 0 && (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                {conversion.input_kind === "file_or_text" ? "Or upload a file" : "Input file"}
              </label>
              <label
                onDragOver={(e) => {
                  e.preventDefault();
                  if (!running) setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragging(false);
                  if (!running) handleFile(e.dataTransfer.files?.[0] || null);
                }}
                className={`flex flex-col sm:flex-row items-center gap-3 p-6 rounded-xl border-2 border-dashed cursor-pointer transition-colors ${
                  dragging ? "border-orange-500 bg-orange-500/10" : "border-slate-700 bg-slate-950 hover:border-orange-500/60"
                }`}
              >
                <Upload className="h-6 w-6 text-orange-400 shrink-0" />
                <span className="text-sm text-slate-300 truncate text-center sm:text-left">
                  {file ? (
                    `${file.name} (${formatBytes(file.size)})`
                  ) : (
                    <>
                      <span className="font-medium text-white">Drop a file here</span> or click to browse
                      <span className="block text-[11px] text-slate-500 mt-0.5">{conversion.accepted_extensions.join(", ")}</span>
                    </>
                  )}
                </span>
                <input
                  type="file"
                  className="hidden"
                  disabled={running}
                  accept={conversion.accepted_extensions.join(",")}
                  onChange={(e) => handleFile(e.target.files?.[0] || null)}
                />
              </label>
              {file && conversion.input_kind === "file_or_text" && (
                <button type="button" className="text-[11px] text-slate-400 hover:text-white" onClick={() => setFile(null)}>
                  Remove file and use the text box
                </button>
              )}
            </div>
          )}

          {/* Local previews */}
          {previewUrl && isVideoFile && (
            <div className="space-y-2">
              <video ref={videoRef} src={previewUrl} controls className="w-full rounded-xl bg-black max-h-72" />
              {visibleParams.some((p) => p.name === "timestamp") && (
                <button
                  type="button"
                  onClick={() => setValue("timestamp", Number((videoRef.current?.currentTime || 0).toFixed(2)))}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-white"
                >
                  Use current frame ({Number(values.timestamp || 0).toFixed(2)}s selected)
                </button>
              )}
            </div>
          )}
          {previewUrl && isImageFile && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={previewUrl} alt="Input preview" className="w-full rounded-xl max-h-72 object-contain bg-slate-950" />
          )}

          {/* Parameters */}
          {otherParams.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {otherParams.map((p) => (
                <ParamField key={p.name} param={p} value={values[p.name]} disabled={running} onChange={(v) => setValue(p.name, v)} />
              ))}
            </div>
          )}

          {error && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm flex items-start gap-2">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="button"
            onClick={submit}
            disabled={running || !mode || mode.status !== "available"}
            className="w-full px-6 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm inline-flex items-center justify-center gap-2 shadow-lg shadow-orange-500/25"
          >
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            <span>{running ? "Processing…" : `Run ${conversion.title}`}</span>
          </button>
        </div>

        {/* ---------------- Job progress & outputs ---------------- */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 min-h-[16rem]">
          <h3 className="text-base font-bold text-white">Result</h3>
          {!job && <p className="text-sm text-slate-500">Run the conversion to see real output files here.</p>}

          {job && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-mono">{job.status}</span>
                <span>{job.progress}%</span>
              </div>
              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`h-full transition-all ${job.status === "failed" ? "bg-rose-500" : "bg-gradient-to-r from-orange-500 to-amber-500"}`}
                  style={{ width: `${job.status === "failed" ? 100 : job.progress}%` }}
                />
              </div>
              {job.progress_message && <p className="text-xs text-slate-400">{job.progress_message}</p>}
            </div>
          )}

          {job?.status === "failed" && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm">
              <p className="font-medium">Conversion failed{job.error_code ? ` (${job.error_code})` : ""}</p>
              <p className="text-xs mt-1">{job.error_message}</p>
            </div>
          )}

          {job?.status === "succeeded" && (
            <div className="space-y-4">
              <p className="text-sm text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" /> Done. {job.outputs?.length || 0} file(s) produced.
              </p>
              {(job.outputs || []).map((o) => o.asset && <OutputCard key={o.id} asset={o.asset} outputType={o.output_type} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ParamField({
  param,
  value,
  disabled,
  onChange,
}: {
  param: ConversionParam;
  value: any;
  disabled: boolean;
  onChange: (v: any) => void;
}) {
  const base =
    "w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-orange-500 disabled:opacity-50";
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-semibold text-slate-300">{param.label}</label>
      {param.type === "select" && (
        <select className={base} value={value ?? ""} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
          {(param.choices || []).map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      )}
      {param.type === "number" && (
        <input
          type="number"
          className={base}
          value={value ?? ""}
          min={param.min ?? undefined}
          max={param.max ?? undefined}
          step={param.step ?? "any"}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))}
        />
      )}
      {param.type === "boolean" && (
        <label className="flex items-center gap-2 text-sm text-slate-300 p-2.5">
          <input type="checkbox" checked={!!value} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
          <span>Enabled</span>
        </label>
      )}
      {(param.type === "text" || param.type === "textarea") && (
        <input className={base} value={value ?? ""} disabled={disabled} onChange={(e) => onChange(e.target.value)} />
      )}
      {param.help && <p className="text-[11px] text-slate-500">{param.help}</p>}
    </div>
  );
}

function OutputCard({ asset, outputType }: { asset: Asset; outputType: string }) {
  const url = ApiClient.getDownloadUrl(asset);
  const preview: string | undefined = asset.metadata_json?.preview_text;
  return (
    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm text-white truncate">{asset.filename}</p>
          <p className="text-[11px] text-slate-500 font-mono">
            {outputType} · {formatBytes(asset.size)}
          </p>
        </div>
        <a
          href={url}
          className="px-3 py-1.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white text-xs font-medium inline-flex items-center gap-1.5 shrink-0"
        >
          <Download className="h-3.5 w-3.5" /> Download
        </a>
      </div>
      {asset.media_type.startsWith("audio/") && <audio controls src={url} className="w-full h-10" />}
      {asset.media_type.startsWith("image/") && asset.media_type !== "image/svg+xml" && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={url} alt={asset.filename} className="w-full rounded-lg max-h-80 object-contain bg-black" />
      )}
      {preview && (
        <pre className="max-h-64 overflow-auto whitespace-pre-wrap text-xs text-slate-300 bg-slate-900 p-3 rounded-lg">
          {preview}
        </pre>
      )}
    </div>
  );
}
