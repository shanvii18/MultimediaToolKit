"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Wand2,
  FileVideo,
  Upload,
  ArrowRight,
  CheckCircle,
  AlertCircle,
  Play,
  Download,
  Film,
  Sparkles,
  Loader2,
  Music,
  Camera,
  Compass,
  Info,
} from "lucide-react";
import { ApiClient } from "@/services/apiClient";
import { getModuleBySlug } from "@/services/modulesCatalog";
import { Job, Asset } from "@/types";

function WorkspaceStudioContent() {
  const searchParams = useSearchParams();
  const toolParam = searchParams.get("tool");
  const initialTool = toolParam || "idea-to-storyboard";

  const isMediaExtractor = initialTool === "media-extractor";
  const [activeTab, setActiveTab] = useState<"storyboard" | "media-extract">(
    isMediaExtractor ? "media-extract" : "storyboard"
  );

  // Detect if user launched an un-implemented or roadmap module
  const currentModule = toolParam ? getModuleBySlug(toolParam) : null;
  const isRoadmapModule =
    currentModule && currentModule.status !== "operational" && toolParam !== "idea-to-storyboard";

  // Storyboard form state
  const [concept, setConcept] = useState(
    "A deep-sea autonomous rover glides through bioluminescent trench caverns and uncovers an ancient crystalline artifact."
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

  // Sync activeTab if tool param changes
  useEffect(() => {
    if (toolParam === "media-extractor") {
      setActiveTab("media-extract");
    } else if (toolParam === "idea-to-storyboard" || !toolParam) {
      setActiveTab("storyboard");
    }
  }, [toolParam]);

  // Poll active job status until terminal state
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
    }, 1500);

    return () => clearInterval(interval);
  }, [activeJob]);

  // Handle Idea-to-Storyboard execution
  const handleGenerateStoryboard = async () => {
    const trimmed = concept.trim();
    if (!trimmed) {
      setErrorMsg("Please enter a creative concept or narrative pitch.");
      return;
    }
    if (trimmed.split(/\s+/).length < 3 || trimmed.length < 12) {
      setErrorMsg("Concept brief is too brief. Please provide at least 3 descriptive words (min 12 characters).");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const job = await ApiClient.createJob("idea_to_storyboard", [], {
        concept: trimmed,
        style,
        duration: Number(duration),
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

    if (file.size === 0) {
      setErrorMsg("Selected file is empty (0 bytes). Please select a valid video file.");
      return;
    }

    if (file.size > 100 * 1024 * 1024) {
      setErrorMsg("File exceeds the 100 MB upload cap. Please select a smaller media file.");
      return;
    }

    setSelectedFile(file);
    setUploading(true);
    setErrorMsg(null);
    setActiveJob(null);
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

  const storyboardData = activeJob?.outputs?.[0]?.asset?.metadata_json?.storyboard_data;

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
          Execute genuinely functional multimedia workflows: direct multi-scene cinematic storyboard synthesis and native
          FFmpeg audio extraction.
        </p>
      </div>

      {/* Roadmap Navigation Banner (Honest redirection if user came from a roadmap module) */}
      {isRoadmapModule && (
        <div className="p-5 rounded-2xl bg-amber-950/20 border border-amber-800/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <Info className="h-4 w-4 shrink-0" />
              <span>
                Roadmap Module Notice: #{currentModule.id} — {currentModule.name}
              </span>
            </div>
            <p className="text-xs text-slate-300">
              This module is scheduled on the development roadmap. MultimediaToolKit does not fake cloud execution.
              You can review its architecture specs or use the operational tools below.
            </p>
          </div>
          <Link
            href={`/modules/${currentModule.slug}`}
            className="px-4 py-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 hover:text-white hover:bg-amber-500/20 text-xs font-medium whitespace-nowrap transition-colors"
          >
            <span>View Architecture Specs</span>
          </Link>
        </div>
      )}

      {/* Studio Tabs */}
      <div className="flex border-b border-slate-800 space-x-6">
        <button
          onClick={() => {
            setActiveTab("storyboard");
            setActiveJob(null);
            setErrorMsg(null);
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
            setErrorMsg(null);
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
                Creative Idea / Narrative Pitch
              </label>
              <textarea
                rows={5}
                value={concept}
                onChange={(e) => setConcept(e.target.value)}
                placeholder="Describe your creative concept, subjects, environment, and story beats..."
                className="w-full p-3.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 transition-colors"
              />
              <p className="text-[11px] text-slate-500">
                Minimum 3 descriptive words. The engine analyzes theme, tone, and pacing to construct distinct acts.
              </p>
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
                  <option value="Moody Film Noir">Moody Film Noir</option>
                  <option value="Epic Fantasy">Epic Fantasy</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Target Duration (sec)</label>
                <input
                  type="number"
                  min={15}
                  max={180}
                  step={5}
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
                  <span>Submitting to Directorial Engine...</span>
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4" />
                  <span>Synthesize Multi-Scene Storyboard</span>
                </>
              )}
            </button>
          </div>

          {/* Storyboard Output Display */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center justify-between">
              <span>Storyboard Output</span>
              {activeJob && (
                <span
                  className={`text-xs font-mono px-2.5 py-0.5 rounded-md ${
                    activeJob.status === "succeeded"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : activeJob.status === "failed"
                      ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  }`}
                >
                  {activeJob.status} ({activeJob.progress}%)
                </span>
              )}
            </h3>

            {!activeJob ? (
              <div className="py-16 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                Submit an idea brief to generate and preview the structured scene breakdown.
              </div>
            ) : activeJob.status === "running" || activeJob.status === "queued" ? (
              <div className="py-16 text-center space-y-3">
                <Loader2 className="h-8 w-8 text-orange-400 animate-spin mx-auto" />
                <p className="text-sm font-medium text-slate-300">Directorial engine synthesizing scene structure...</p>
                <p className="text-xs text-slate-500 font-mono">Job ID: {activeJob.id}</p>
              </div>
            ) : activeJob.status === "succeeded" ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-emerald-400">
                      Generation Complete ({storyboardData?.scene_count || 0} Scenes, {storyboardData?.actual_total_duration}s total)
                    </span>
                    <p className="text-[11px] text-slate-400 font-mono">
                      {storyboardData?.model_engine || "MultimediaToolKit Storyboard Engine"}
                    </p>
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
                <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
                  {storyboardData?.scenes?.map((scene: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2.5 text-xs"
                    >
                      <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                        <span className="font-bold text-orange-400 text-sm">{scene.title}</span>
                        <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                          {scene.duration_seconds}s
                        </span>
                      </div>

                      <div className="space-y-1">
                        <p className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5">
                          <Compass className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                          <span>Narrative Purpose:</span>
                        </p>
                        <p className="text-slate-300 pl-5">{scene.narrative_purpose}</p>
                      </div>

                      <div className="space-y-1">
                        <p className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5">
                          <Camera className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                          <span>Visual Action & Composition:</span>
                        </p>
                        <p className="text-slate-300 pl-5">{scene.visual_action}</p>
                        <p className="text-slate-400 text-[11px] pl-5 italic font-mono">{scene.composition}</p>
                      </div>

                      <div className="space-y-1">
                        <p className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5">
                          <Music className="h-3.5 w-3.5 text-rose-400 shrink-0" />
                          <span>Sound Design & VO:</span>
                        </p>
                        <p className="text-slate-400 text-[11px] pl-5">
                          <strong className="text-slate-300">Cue:</strong> {scene.audio_cue}
                        </p>
                        <p className="text-amber-200 text-xs pl-5 bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                          {scene.voiceover_script}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 space-y-1">
                <span className="font-semibold block text-rose-400">Execution Error:</span>
                <p>{activeJob.error_message || "Unknown error during storyboard synthesis."}</p>
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
              <span>Upload Video for FFmpeg Audio Extraction</span>
            </h3>

            <div className="border-2 border-dashed border-slate-800 rounded-2xl p-6 text-center hover:border-slate-700 transition-colors">
              <input
                type="file"
                id="file-upload"
                onChange={handleFileUpload}
                accept="video/*,audio/*,.mp4,.mov,.mkv,.avi,.webm"
                className="hidden"
              />
              <label htmlFor="file-upload" className="cursor-pointer space-y-3 block">
                <Upload className="h-8 w-8 text-orange-400 mx-auto" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-slate-200">
                    {uploading
                      ? "Uploading and validating media file..."
                      : selectedFile
                      ? selectedFile.name
                      : "Click to select video file"}
                  </p>
                  <p className="text-xs text-slate-500">Supports MP4, MOV, MKV, AVI, WEBM (Max 100MB)</p>
                </div>
              </label>
            </div>

            {uploadedAsset && (
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1.5">
                <div className="flex justify-between text-slate-300">
                  <span>File registered:</span>
                  <span className="font-mono text-white font-medium">{uploadedAsset.filename}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>File size:</span>
                  <span className="font-mono text-slate-300">{(uploadedAsset.size / 1024).toFixed(1)} KB</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Asset ID:</span>
                  <span className="font-mono text-slate-500">{uploadedAsset.id.slice(0, 12)}...</span>
                </div>
              </div>
            )}

            <button
              onClick={handleExtractAudio}
              disabled={Boolean(!uploadedAsset || uploading || isSubmitting || activeJob?.status === "running")}
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
            <h3 className="text-base font-bold text-white flex items-center justify-between">
              <span>Extraction Status & Download</span>
              {activeJob && (
                <span
                  className={`text-xs font-mono px-2.5 py-0.5 rounded-md ${
                    activeJob.status === "succeeded"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : activeJob.status === "failed"
                      ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  }`}
                >
                  {activeJob.status} ({activeJob.progress}%)
                </span>
              )}
            </h3>

            {!activeJob ? (
              <div className="py-16 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
                Upload a video and start extraction to preview the result.
              </div>
            ) : activeJob.status === "running" || activeJob.status === "queued" ? (
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
                    Audio stream separated via native FFmpeg and persisted into project storage.
                  </p>
                </div>

                {activeJob.outputs && activeJob.outputs.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <span className="text-sm font-medium text-white">
                          {activeJob.outputs[0].asset?.filename || "extracted_audio.mp3"}
                        </span>
                        <p className="text-xs text-slate-500 font-mono">
                          Format: {activeJob.outputs[0].asset?.media_type || "audio/mpeg"} • Size:{" "}
                          {activeJob.outputs[0].asset?.size
                            ? `${(activeJob.outputs[0].asset.size / 1024).toFixed(1)} KB`
                            : "Available"}
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

                    {/* Integrated In-Browser Audio Player */}
                    <div className="pt-2 border-t border-slate-800/80">
                      <p className="text-[11px] text-slate-400 mb-1.5 font-medium">In-Browser Audio Preview:</p>
                      <audio
                        controls
                        className="w-full h-10 rounded-lg bg-slate-900"
                        src={ApiClient.getDownloadUrl(activeJob.outputs[0].asset_id)}
                      />
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 space-y-1">
                <span className="font-semibold block text-rose-400">Extraction Error:</span>
                <p>{activeJob.error_message || "Extraction task failed."}</p>
                <p className="text-[11px] text-slate-400">
                  Ensure the video contains a valid audio track and FFmpeg is accessible.
                </p>
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
