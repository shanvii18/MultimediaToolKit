"use client";

import React, { useRef, useState } from "react";
import { X, UploadCloud, FileVideo, FileAudio, FileText, CheckCircle2, Loader2, ArrowRight } from "lucide-react";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processed, setProcessed] = useState(false);
  const [processStep, setProcessStep] = useState("");

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (file: File) => {
    setSelectedFile(file);
    setIsProcessing(true);
    setProcessed(false);
    setProcessStep("Analyzing file structure & codecs...");

    // Simulated multi-stage workflow pipeline for interactive prototype
    setTimeout(() => {
      setProcessStep("Extracting audio channels & segmenting...");
    }, 900);

    setTimeout(() => {
      setProcessStep("Transcribing speech timestamps...");
    }, 1800);

    setTimeout(() => {
      setProcessStep("Structuring intelligent study concepts...");
    }, 2600);

    setTimeout(() => {
      setIsProcessing(false);
      setProcessed(true);
      setProcessStep("Ready in workspace!");
    }, 3200);
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setIsProcessing(false);
    setProcessed(false);
    setProcessStep("");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div
        className="relative w-full max-w-xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 md:p-8 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Decorative Top Accent Stripe */}
        <div className="absolute top-0 left-0 right-0 h-1.5 stripe-gradient-mesh" />

        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800/80">
          <div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
              Upload Media or Document
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 font-normal">
              Supports MP4, MOV, MP3, WAV, PDF, PNG, JPG (Interactive Workspace Prototype)
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="mt-6">
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept="video/*,audio/*,image/*,.pdf"
            onChange={handleFileInputChange}
          />

          {!selectedFile ? (
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                dragActive
                  ? "border-stripe-orange bg-stripe-orange/5 scale-[0.99]"
                  : "border-slate-200 dark:border-slate-700/80 hover:border-stripe-orange dark:hover:border-stripe-orange bg-slate-50/50 dark:bg-slate-950/40"
              }`}
            >
              <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-stripe-orange/10 text-stripe-orange flex items-center justify-center">
                <UploadCloud className="w-7 h-7" />
              </div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                Drag and drop files here, or <span className="text-stripe-orange underline">browse</span>
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 font-normal">
                Drop lecture recordings, podcasts, whiteboards, or document scans
              </p>

              <div className="flex items-center justify-center gap-4 mt-6 text-xs text-slate-400 dark:text-slate-500 font-normal">
                <span className="flex items-center gap-1">
                  <FileVideo className="w-3.5 h-3.5 text-stripe-orange" /> Video
                </span>
                <span className="flex items-center gap-1">
                  <FileAudio className="w-3.5 h-3.5 text-stripe-coral" /> Audio
                </span>
                <span className="flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5 text-stripe-cyan" /> PDF & OCR
                </span>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-5 bg-slate-50 dark:bg-slate-950/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-stripe-orange/10 text-stripe-orange flex items-center justify-center font-bold">
                    {selectedFile.type.includes("video") ? (
                      <FileVideo className="w-5 h-5 text-stripe-orange" />
                    ) : selectedFile.type.includes("audio") ? (
                      <FileAudio className="w-5 h-5 text-stripe-coral" />
                    ) : (
                      <FileText className="w-5 h-5 text-stripe-cyan" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-white truncate max-w-xs">
                      {selectedFile.name}
                    </h4>
                    <span className="text-xs text-slate-400">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type || "Document"}
                    </span>
                  </div>
                </div>

                {processed ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Ready
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-stripe-orange/10 text-stripe-orange">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" /> Processing
                  </span>
                )}
              </div>

              {/* Progress bar / Pipeline status */}
              <div className="mt-5 pt-4 border-t border-slate-200 dark:border-slate-800/80">
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">
                    {processStep}
                  </span>
                  <span className="text-stripe-orange font-semibold">
                    {processed ? "100%" : isProcessing ? "75%" : "0%"}
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      processed
                        ? "bg-emerald-500 w-full"
                        : "stripe-gradient-mesh w-3/4 animate-pulse"
                    }`}
                  />
                </div>
                <p className="mt-2 text-[11px] text-slate-400 dark:text-slate-500 italic">
                  Note: Client-side interactive pipeline demonstration. Real backend pipelines will connect in Phase 2.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
          {selectedFile ? (
            <button
              onClick={resetUpload}
              className="text-xs text-slate-500 hover:text-slate-900 dark:hover:text-white underline cursor-pointer"
            >
              Upload another file
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Close
            </button>
            <button
              onClick={() => {
                onClose();
                const workspaceElem = document.getElementById("workspace-preview");
                workspaceElem?.scrollIntoView({ behavior: "smooth" });
              }}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-gradient-to-r from-stripe-orange to-stripe-coral text-white hover:brightness-105 transition-all shadow-md shadow-stripe-orange/20 flex items-center gap-1.5 cursor-pointer"
            >
              <span>View In Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
