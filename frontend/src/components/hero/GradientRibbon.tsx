"use client";

import React from "react";

export function GradientRibbon() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden select-none -z-10">
      {/* Luminous Ambient Diffusion Glows (Orange, Amber & Coral-Pink) */}
      <div className="absolute -top-[12%] right-[-5%] w-[680px] lg:w-[1080px] h-[680px] lg:h-[980px] rounded-full bg-gradient-to-br from-stripe-amber/40 via-stripe-orange/45 to-stripe-coral/40 blur-[140px] dark:opacity-85 opacity-70 animate-gradient-drift" />
      <div className="absolute top-[25%] -right-[12%] w-[520px] lg:w-[820px] h-[520px] lg:h-[820px] rounded-full bg-gradient-to-tr from-stripe-pink/35 via-stripe-magenta/30 to-stripe-violet/20 blur-[120px] dark:opacity-75 opacity-60" />
      <div className="absolute top-[60%] right-[10%] w-[380px] lg:w-[580px] h-[380px] lg:h-[580px] rounded-full bg-gradient-to-r from-stripe-coral/25 to-stripe-peach/25 blur-[95px] dark:opacity-50 opacity-40" />

      {/* Stripe-Inspired Striated Fabric Ribbon Composition (Matching Screenshot 2) */}
      <div className="absolute -top-16 -right-12 w-[110%] lg:w-[82%] h-[125%] flex items-start justify-end opacity-95 dark:opacity-90">
        <svg
          viewBox="0 0 1300 950"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full object-cover transform -rotate-6 scale-110 lg:scale-120 animate-ribbon-wave"
          aria-hidden="true"
        >
          <defs>
            {/* Primary Ribbon Gradient: Amber -> Vivid Orange -> Coral -> Hot Pink */}
            <linearGradient id="ribbonAmberOrange" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FFA726" stopOpacity="0.95" />
              <stop offset="28%" stopColor="#FF5E00" stopOpacity="0.92" />
              <stop offset="62%" stopColor="#FF6584" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#FF2E93" stopOpacity="0.85" />
            </linearGradient>

            {/* Middle Ribbon Gradient: Orange -> Coral -> Pink -> Magenta */}
            <linearGradient id="ribbonCoralPink" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#FF5E00" stopOpacity="0.88" />
              <stop offset="38%" stopColor="#FF6584" stopOpacity="0.9" />
              <stop offset="72%" stopColor="#FF2E93" stopOpacity="0.88" />
              <stop offset="100%" stopColor="#E639A2" stopOpacity="0.82" />
            </linearGradient>

            {/* Deep Harmonic Layer: Pink -> Magenta -> Supporting Violet with Cyan edge */}
            <linearGradient id="ribbonDeepViolet" x1="0%" y1="50%" x2="100%" y2="50%">
              <stop offset="0%" stopColor="#FF2E93" stopOpacity="0.75" />
              <stop offset="45%" stopColor="#E639A2" stopOpacity="0.8" />
              <stop offset="85%" stopColor="#7928CA" stopOpacity="0.75" />
              <stop offset="100%" stopColor="#00D4FF" stopOpacity="0.7" />
            </linearGradient>

            {/* Luminous Razor Edge Gradient */}
            <linearGradient id="luminousHighlight" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.85" />
              <stop offset="35%" stopColor="#FFA726" stopOpacity="0.7" />
              <stop offset="65%" stopColor="#FF6584" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#FF2E93" stopOpacity="0.1" />
            </linearGradient>

            {/* Atmospheric Depth Filter */}
            <filter id="ribbonDepthBlur" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="30" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* LAYER 1: Deep Translucent Magenta/Violet Shadow Ribbon */}
          <path
            d="M 380 -180 C 580 100, 750 360, 1220 620 L 1340 500 C 900 240, 740 40, 500 -240 Z"
            fill="url(#ribbonDeepViolet)"
            opacity="0.72"
            filter="url(#ribbonDepthBlur)"
          />

          {/* LAYER 2: Middle Swirling Coral & Pink Wave Ribbon */}
          <path
            d="M 270 -110 C 490 160, 660 420, 1160 710 L 1280 580 C 820 300, 650 70, 400 -180 Z"
            fill="url(#ribbonCoralPink)"
            opacity="0.88"
          />

          {/* LAYER 3: Primary Bold Orange-Amber Sweeping Ribbon (The Main Stripe Fold) */}
          <path
            d="M 160 -60 C 390 210, 570 480, 1090 800 L 1220 670 C 720 360, 540 100, 290 -140 Z"
            fill="url(#ribbonAmberOrange)"
            opacity="0.95"
          />

          {/* LAYER 4: Secondary Curvature Ridge Layer (Creates the 3D twist seen in Stripe) */}
          <path
            d="M 290 -140 C 540 100, 720 360, 1220 670 L 1180 720 C 680 400, 500 140, 250 -100 Z"
            fill="url(#ribbonCoralPink)"
            opacity="0.65"
          />

          {/* LAYER 5: Sharp Luminous Crest Line */}
          <path
            d="M 160 -60 C 390 210, 570 480, 1090 800"
            stroke="url(#luminousHighlight)"
            strokeWidth="3.5"
            strokeLinecap="round"
            opacity="0.9"
          />

          {/* LAYER 6: Fine Fabric Contours / Isometric Coordinate Lines */}
          <g stroke="rgba(255,255,255,0.22)" strokeWidth="1" strokeDasharray="5 7">
            <line x1="220" y1="0" x2="1140" y2="750" />
            <line x1="300" y1="-40" x2="1200" y2="700" />
            <line x1="380" y1="-80" x2="1260" y2="650" />
          </g>
        </svg>
      </div>

      {/* Tactile Texture */}
      <div className="absolute inset-0 ribbon-grain pointer-events-none opacity-40 dark:opacity-55" />

      {/* Seamless Base Feathering */}
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[var(--bg-page)] to-transparent" />
    </div>
  );
}
