"use client";

import React, { useEffect, useState } from "react";

interface AudioWaveformProps {
  isPlaying?: boolean;
  barCount?: number;
  heightClass?: string;
  className?: string;
  colorScheme?: "orange-coral" | "coral-pink" | "cyan-violet";
}

export function AudioWaveform({
  isPlaying = true,
  barCount = 36,
  heightClass = "h-8 sm:h-10",
  className = "",
  colorScheme = "orange-coral",
}: AudioWaveformProps) {
  // Baseline static aesthetic heights for when paused
  const baseHeights = [
    25, 45, 65, 30, 85, 55, 40, 95, 70, 35, 60, 80, 50, 90, 65, 30, 75, 100,
    45, 70, 85, 55, 35, 90, 60, 40, 75, 50, 95, 65, 30, 80, 55, 40, 70, 35,
  ];

  const [dynamicHeights, setDynamicHeights] = useState<number[]>(baseHeights);

  useEffect(() => {
    if (!isPlaying) {
      setDynamicHeights(baseHeights.slice(0, barCount));
      return;
    }

    const interval = setInterval(() => {
      setDynamicHeights((prev) =>
        prev.map((val, idx) => {
          // Natural organic variation around base heights
          const base = baseHeights[idx % baseHeights.length];
          const jitter = Math.sin(Date.now() / 200 + idx * 0.4) * 35;
          const newH = Math.min(100, Math.max(18, base + jitter));
          return Math.round(newH);
        })
      );
    }, 120);

    return () => clearInterval(interval);
  }, [isPlaying, barCount]);

  const getGradient = (scheme: string) => {
    switch (scheme) {
      case "coral-pink":
        return "bg-gradient-to-t from-stripe-coral via-stripe-pink to-stripe-magenta";
      case "cyan-violet":
        return "bg-gradient-to-t from-stripe-cyan via-stripe-violet to-stripe-pink";
      case "orange-coral":
      default:
        return "bg-gradient-to-t from-stripe-orange via-stripe-coral to-stripe-pink";
    }
  };

  const gradientClass = getGradient(colorScheme);

  return (
    <div
      className={`flex items-center justify-between gap-0.5 sm:gap-1 ${heightClass} ${className}`}
      aria-label="Live animated audio waveform"
    >
      {dynamicHeights.slice(0, barCount).map((h, i) => (
        <div
          key={i}
          style={{
            height: `${isPlaying ? h : Math.max(20, h * 0.4)}%`,
            transition: "height 130ms cubic-bezier(0.4, 0, 0.2, 1)",
          }}
          className={`w-1 sm:w-1.5 rounded-full ${gradientClass} opacity-90`}
        />
      ))}
    </div>
  );
}
