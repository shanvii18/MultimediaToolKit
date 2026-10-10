"use client";

import React, { useState, useEffect } from "react";
import { useTheme } from "@/components/theme/ThemeProvider";
import {
  Sun,
  Moon,
  Menu,
  X,
  ChevronDown,
  Video,
  FileAudio,
  FileText,
  Sparkles,
  Layers,
  ArrowRight,
} from "lucide-react";

interface NavbarProps {
  onOpenUpload: () => void;
  onOpenSignIn: () => void;
}

export function Navbar({ onOpenUpload, onOpenSignIn }: NavbarProps) {
  const { theme, toggleTheme } = useTheme();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [productsOpen, setProductsOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
        scrolled
          ? "bg-white/90 dark:bg-slate-950/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 shadow-sm"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Brand Logo matching Screenshot 1 editorial typography */}
          <a href="#" className="flex items-center gap-2.5 group focus:outline-none focus:ring-2 focus:ring-stripe-orange rounded-lg">
            <div className="w-8 h-8 rounded-lg stripe-gradient-mesh flex items-center justify-center text-white font-bold text-sm shadow-md shadow-stripe-orange/20 transition-transform group-hover:scale-105">
              <Layers className="w-4 h-4 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-base md:text-lg tracking-tight text-slate-900 dark:text-white leading-tight">
                Multimedia<span className="text-stripe-orange font-medium">ToolKit</span>
              </span>
            </div>
          </a>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 lg:gap-2">
            {/* Products Dropdown */}
            <div
              className="relative"
              onMouseEnter={() => setProductsOpen(true)}
              onMouseLeave={() => setProductsOpen(false)}
            >
              <button
                className="px-3.5 py-2 text-sm font-normal text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white rounded-lg hover:bg-slate-100/60 dark:hover:bg-slate-900/60 inline-flex items-center gap-1.5 transition-colors cursor-pointer"
                onClick={() => setProductsOpen(!productsOpen)}
              >
                <span>Products</span>
                <ChevronDown
                  className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${
                    productsOpen ? "rotate-180" : ""
                  }`}
                />
              </button>

              {/* Products Dropdown Menu */}
              {productsOpen && (
                <div className="absolute top-full left-0 w-72 pt-2 animate-fade-in">
                  <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl shadow-2xl p-2 space-y-1">
                    <a
                      href="#video-to-audio"
                      onClick={() => setProductsOpen(false)}
                      className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors group"
                    >
                      <div className="p-2 rounded-lg bg-orange-500/10 text-stripe-orange group-hover:scale-105 transition-transform">
                        <Video className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-slate-900 dark:text-white">
                          Video to Audio
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400">
                          Extract crystal-clear audio tracks & waveforms
                        </div>
                      </div>
                    </a>

                    <a
                      href="#audio-to-text"
                      onClick={() => setProductsOpen(false)}
                      className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors group"
                    >
                      <div className="p-2 rounded-lg bg-pink-500/10 text-stripe-coral group-hover:scale-105 transition-transform">
                        <FileAudio className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-slate-900 dark:text-white">
                          Audio to Text
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400">
                          Searchable timestamped transcription
                        </div>
                      </div>
                    </a>

                    <a
                      href="#image-to-text"
                      onClick={() => setProductsOpen(false)}
                      className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors group"
                    >
                      <div className="p-2 rounded-lg bg-sky-500/10 text-stripe-cyan group-hover:scale-105 transition-transform">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-slate-900 dark:text-white">
                          Image to Text
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400">
                          Structured OCR document & board extraction
                        </div>
                      </div>
                    </a>

                    <a
                      href="#study-mode"
                      onClick={() => setProductsOpen(false)}
                      className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors group"
                    >
                      <div className="p-2 rounded-lg bg-pink-500/10 text-stripe-pink group-hover:scale-105 transition-transform">
                        <Sparkles className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-slate-900 dark:text-white">
                          AI Study Mode
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400">
                          Interactive notes, flashcards & exam questions
                        </div>
                      </div>
                    </a>
                  </div>
                </div>
              )}
            </div>

            <a
              href="#study-mode"
              className="px-3.5 py-2 text-sm font-normal text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white rounded-lg hover:bg-slate-100/60 dark:hover:bg-slate-900/60 transition-colors"
            >
              Study Mode
            </a>
            <a
              href="#workflow"
              className="px-3.5 py-2 text-sm font-normal text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white rounded-lg hover:bg-slate-100/60 dark:hover:bg-slate-900/60 transition-colors"
            >
              Workflow
            </a>
            <a
              href="#features"
              className="px-3.5 py-2 text-sm font-normal text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white rounded-lg hover:bg-slate-100/60 dark:hover:bg-slate-900/60 transition-colors"
            >
              Features
            </a>
          </nav>

          {/* Action CTAs & Controls */}
          <div className="flex items-center gap-2.5 sm:gap-3">
            {/* Theme Toggle Button */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800 transition-colors cursor-pointer"
              aria-label="Toggle light and dark theme"
            >
              {theme === "dark" ? (
                <Sun className="w-4 h-4 text-amber-400 transition-transform hover:rotate-45" />
              ) : (
                <Moon className="w-4 h-4 text-stripe-orange transition-transform hover:-rotate-12" />
              )}
            </button>

            {/* Sign in Button */}
            <button
              onClick={onOpenSignIn}
              className="hidden sm:inline-flex px-3 py-2 text-sm font-normal text-slate-700 dark:text-slate-200 hover:text-slate-950 dark:hover:text-white transition-colors cursor-pointer"
            >
              Sign in
            </button>

            {/* Get Started Button */}
            <button
              onClick={onOpenUpload}
              className="px-4.5 py-2 rounded-lg text-xs sm:text-sm font-medium text-white bg-gradient-to-r from-stripe-orange to-stripe-coral hover:brightness-105 transition-all shadow-md shadow-stripe-orange/15 flex items-center gap-1.5 cursor-pointer"
            >
              <span>Start creating</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            {/* Mobile menu trigger */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors cursor-pointer"
              aria-label="Toggle mobile menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 px-6 py-6 space-y-4 animate-fade-in shadow-xl">
          <nav className="flex flex-col space-y-2">
            <a
              href="#video-to-audio"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-stripe-orange rounded-lg"
            >
              Video to Audio
            </a>
            <a
              href="#audio-to-text"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-stripe-orange rounded-lg"
            >
              Audio to Text
            </a>
            <a
              href="#image-to-text"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-stripe-orange rounded-lg"
            >
              Image to Text
            </a>
            <a
              href="#study-mode"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-stripe-orange rounded-lg"
            >
              Study Mode
            </a>
            <a
              href="#workflow"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-stripe-orange rounded-lg"
            >
              Workflow
            </a>
            <a
              href="#features"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-stripe-orange rounded-lg"
            >
              Features
            </a>
          </nav>

          <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenSignIn();
              }}
              className="text-sm font-medium text-slate-700 dark:text-slate-200 hover:text-stripe-orange"
            >
              Sign in
            </button>
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenUpload();
              }}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-gradient-to-r from-stripe-orange to-stripe-coral text-white shadow-md"
            >
              Start creating
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
