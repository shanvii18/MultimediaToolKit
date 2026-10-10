"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Wand2,
  FileVideo,
  Mic,
  Upload,
  ArrowRight,
  CheckCircle,
  AlertCircle,
  Play,
  Download,
  Film,
  Sparkles,
  Loader2,
} from "lucide-react";
import { ApiClient } from "@/services/apiClient";
import { Job, Asset } from "@/types";

function WorkspaceStudioContent() {
  const searchParams = useSearchParams();
  const initialTool = searchParams.get("tool") || "idea-to-storyboard";

  const [activeTab, setActiveTab] = useState<"storyboard" | "media-extract" | "speech-transcribe">(
    initialTool === "media-extractor" ? "media-extract" : initialTool === "speech-to-text" ? "speech-transcribe" : "storyboard"
  );

  // Storyboard form state
  const [concept, setConcept] = useState(
    "A deep-sea autonomous rover glides through bioluminescent trench caverns and uncovers an ancient alien artifact."
  );
  const [style, setStyle] = useState("Cinematic Sci-Fi");
  const [duration, setDuration] = useState(60);

  // Media extraction / Video-to-audio state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedAsset, setUploadedAsset] = useState<Asset | null>(null);

  // Job execution state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeJob, setActiveJob] = useState<Job | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Poll active job status
  useEffect(() => {
    if (!activeJob || activeJob.status === "succeeded" || activeJob.status === "failed") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await ApiClient.getJob(activeJob.id);
        setActiveJob(updated);
      } catch (err) {
        console.error("Job poll error:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [activeJob]);

  // Handle Idea-to-Storyboard execution
  const handleGenerateStoryboard = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const job = await ApiClient.createJob("idea_to_storyboard", [], {
        concept,
        style,
        duration,
      });
      setActiveJob(job);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit storyboard task.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle file upload for media extraction
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setSelectedFile(file);
    setUploading(true);
    setErrorMsg(null);
    try {
      const asset = await ApiClient.uploadMedia(file);
      setUploadedAsset(asset);
    } catch (err: any) {
      setErrorMsg(err.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  // Handle Video-to-Audio task
  const handleExtractAudio = async () => {
    if (!uploadedAsset) {
      setErrorMsg("Please upload a media file first.");
      return;
    }
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const job = await ApiClient.createJob("video_to_audio", [uploadedAsset.id], {
        audio_format: "mp3",
      });
      setActiveJob(job);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit extraction task.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Studio Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-mono">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Multimodal Creation & Processing Studio</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Active Creation Studio</h1>
        <p className="text-sm text-slate-400">
          Execute real blueprint pipelines. Generate structured multi-scene storyboards or process media with backend workers.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-6">
        <button
          onClick={() => {
            setActiveTab("storyboard");
            setActiveJob(null);
          }}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === "storyboard"
              ? "border-orange-500 text-orange-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Wand2 className="h-4 w-4" />
          <span>Idea-to-Storyboard Studio (Module #17)</span>
        </button>

        <button
          onClick={() => {
            setActiveTab("media-extract");
            setActiveJob(null);
          }}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === "media-extract"
              ? "border-orange-500 text-orange-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileVideo className="h-4 w-4" />
          <span>Media Extractor / Video → Audio (Module #06)</span>
        </button>
      </div>

      {/* Error alert */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Tab 1: Idea to Storyboard */}
      {activeTab === "storyboard" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
          {/* Form */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-orange-400" />
              <span>Input Concept & Directorial Brief</span>
            </h3>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Creative Idea / Narrative
              </label>
              <textarea
                rows={5}
                value={concept}
                onChange={(e) => setConcept(e.target.value)}
                placeholder="Describe your creative concept or narrative pitch..."
                className="w-full p-3.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 transition-colors"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Visual Style</label>
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-orange-500"
                >
                  <option value="Cinematic Sci-Fi">Cinematic Sci-Fi</option>
                  <option value="Documentary Realism">Documentary Realism</option>
                  <option value="Anime Cyberpunk">Anime Cyberpunk</option>
                  <option value="Commercial 3D">Commercial 3D</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Target Duration (sec)</label>
                <input
                  type="number"
                  min={15}
                  max={180}
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-orange-500"
                />
              </div>
            </div>

            <button
              onClick={handleGenerateStoryboard}
              disabled={Boolean(isSubmitting || activeJob?.status === "running")}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 disabled:opacity-50 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-orange-500/20 transition-all"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Submitting to Worker...</span>
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4" />
                  <span>Synthesize Multi-Scene Storyboard</span>
                </>
              )}
            </button>
          </div>

          {/* Real output display */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center justify-between">
              <span>Storyboard Output</span>
              {activeJob && (
                <span
                  className={`text-xs font-mono px-2 py-0.5 rounded-md ${
                    activeJob.status === "succeeded"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  }`}
                >
                  {activeJob.status} ({activeJob.progress}%)
                </span>
              )}
            </h3>

            {!activeJob ? (
              <div className="py-16 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                Submit an idea brief to generate and preview the scene breakdown.
              </div>
            ) : activeJob.status === "running" || activeJob.status === "queued" ? (
              <div className="py-16 text-center space-y-3">
                <Loader2 className="h-8 w-8 text-orange-400 animate-spin mx-auto" />
                <p className="text-sm font-medium text-slate-300">Structuring storyboard scenes...</p>
                <p className="text-xs text-slate-500 font-mono">Job ID: {activeJob.id}</p>
              </div>
            ) : activeJob.status === "succeeded" ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-emerald-400">Generation Complete</span>
                    <p className="text-[11px] text-slate-400">Structured multi-scene script ready for download</p>
                  </div>
                  {activeJob.outputs && activeJob.outputs.length > 0 && (
                    <a
                      href={ApiClient.getDownloadUrl(activeJob.outputs[0].asset_id)}
                      download
                      className="px-3 py-1.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white text-xs font-medium flex items-center gap-1.5 transition-colors"
                    >
                      <Download className="h-3.5 w-3.5" />
                      <span>Download JSON</span>
                    </a>
                  )}
                </div>

                {/* Render scenes preview */}
                <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                  {activeJob.outputs?.[0]?.asset?.metadata_json?.storyboard_data?.scenes?.map(
                    (scene: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-orange-400">{scene.title}</span>
                          <span className="font-mono text-[10px] text-slate-500">{scene.duration_seconds}s</span>
                        </div>
                        <p className="text-slate-300">
                          <strong className="text-slate-400">Visual:</strong> {scene.visual_prompt}
                        </p>
                        <p className="text-slate-400">
                          <strong className="text-slate-500">VO:</strong> {scene.voiceover_script}
                        </p>
                      </div>
                    )
                  )}
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
                Failed: {activeJob.error_message || "Unknown error"}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Media Extractor / Video to Audio */}
      {activeTab === "media-extract" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FileVideo className="h-4 w-4 text-orange-400" />
              <span>Upload Video for Extraction</span>
            </h3>

            <div className="border-2 border-dashed border-slate-800 rounded-2xl p-6 text-center hover:border-slate-700 transition-colors">
              <input
                type="file"
                id="file-upload"
                onChange={handleFileUpload}
                accept="video/*,audio/*"
                className="hidden"
              />
              <label htmlFor="file-upload" className="cursor-pointer space-y-3 block">
                <Upload className="h-8 w-8 text-orange-400 mx-auto" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-slate-200">
                    {selectedFile ? selectedFile.name : "Click to browse media file"}
                  </p>
                  <p className="text-xs text-slate-500">Supports MP4, MOV, MKV, AVI (Max 100MB)</p>
                </div>
              </label>
            </div>

            {uploadedAsset && (
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                <div className="flex justify-between text-slate-300">
                  <span>File registered:</span>
                  <span className="font-mono text-white font-medium">{uploadedAsset.filename}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Asset ID:</span>
                  <span className="font-mono">{uploadedAsset.id.slice(0, 12)}...</span>
                </div>
              </div>
            )}

            <button
              onClick={handleExtractAudio}
              disabled={Boolean(!uploadedAsset || isSubmitting || activeJob?.status === "running")}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 disabled:opacity-50 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-orange-500/20 transition-all"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Submitting extraction task...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  <span>Extract Lossless MP3 Audio</span>
                </>
              )}
            </button>
          </div>

          {/* Result view */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white">Extraction Status & Download</h3>

            {!activeJob ? (
              <div className="py-16 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                Upload a video and start extraction to preview the result.
              </div>
            ) : activeJob.status === "running" ? (
              <div className="py-16 text-center space-y-3">
                <Loader2 className="h-8 w-8 text-amber-400 animate-spin mx-auto" />
                <p className="text-sm font-medium text-slate-300">FFmpeg worker extracting audio track...</p>
                <p className="text-xs text-slate-500 font-mono">Job ID: {activeJob.id}</p>
              </div>
            ) : activeJob.status === "succeeded" ? (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                    <CheckCircle className="h-4 w-4" />
                    <span>Audio Track Extracted Successfully</span>
                  </div>
                  <p className="text-xs text-slate-300">
                    Audio stream separated and saved into project storage.
                  </p>
                </div>

                {activeJob.outputs && activeJob.outputs.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                    <div className="space-y-0.5">
                      <span className="text-sm font-medium text-white">
                        {activeJob.outputs[0].asset?.filename || "extracted_audio.mp3"}
                      </span>
                      <p className="text-xs text-slate-500 font-mono">
                        {activeJob.outputs[0].asset?.media_type || "audio/mpeg"}
                      </p>
                    </div>

                    <a
                      href={ApiClient.getDownloadUrl(activeJob.outputs[0].asset_id)}
                      download
                      className="px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-xs font-semibold flex items-center gap-2 transition-colors"
                    >
                      <Download className="h-4 w-4" />
                      <span>Download MP3</span>
                    </a>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
                Failed: {activeJob.error_message || "Extraction task failed"}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function WorkspaceStudioPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Loading Creation Studio...</div>}>
      <WorkspaceStudioContent />
    </Suspense>
  );
}
