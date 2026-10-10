import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        stripe: {
          orange: "#FF5E00",
          amber: "#FFA726",
          peach: "#FF9066",
          coral: "#FF6584",
          pink: "#FF2E93",
          magenta: "#E639A2",
          violet: "#635BFF",
          purple: "#7928CA",
          cyan: "#00D4FF",
          sky: "#80D8FF",
          navy: "#0A1020",
          "navy-light": "#151F38",
          dark: "#060911",
          slate: "#425466",
          cream: "#FAF9F6",
        },
      },
      fontFamily: {
        sans: [
          '"Plus Jakarta Sans"',
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          '"Helvetica Neue"',
          "sans-serif",
        ],
      },
      animation: {
        "ribbon-wave": "ribbonWave 16s ease-in-out infinite",
        "ribbon-float-slow": "ribbonFloatSlow 18s ease-in-out infinite",
        "gradient-drift": "gradientDrift 14s ease infinite",
        "float-gentle": "floatGentle 6s ease-in-out infinite",
        "float-delayed": "floatGentle 7s ease-in-out 2s infinite",
        "float-reverse": "floatReverse 8s ease-in-out 1s infinite",
        "scan-line": "scanLine 3s ease-in-out infinite",
        "pulse-subtle": "pulseSubtle 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "text-fade": "textFade 4.5s ease-in-out infinite",
      },
      keyframes: {
        ribbonWave: {
          "0%, 100%": {
            transform: "translate3d(0, 0, 0) rotate(-6deg) scale(1.05)",
          },
          "50%": {
            transform: "translate3d(-18px, -20px, 0) rotate(-3.5deg) scale(1.1)",
          },
        },
        ribbonFloatSlow: {
          "0%, 100%": {
            transform: "translateY(0px) scale(1)",
          },
          "50%": {
            transform: "translateY(-14px) scale(1.03)",
          },
        },
        gradientDrift: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        floatGentle: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        floatReverse: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(10px)" },
        },
        scanLine: {
          "0%": { top: "0%" },
          "50%": { top: "96%" },
          "100%": { top: "0%" },
        },
        pulseSubtle: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.65" },
        },
        textFade: {
          "0%, 8%": { opacity: "0", transform: "translateY(12px)" },
          "15%, 85%": { opacity: "1", transform: "translateY(0px)" },
          "92%, 100%": { opacity: "0", transform: "translateY(-12px)" },
        },
      },
      boxShadow: {
        subtle: "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)",
        stripe: "0 13px 27px -5px rgba(50,50,93,0.18), 0 8px 16px -8px rgba(0,0,0,0.22)",
        "stripe-lg": "0 30px 60px -12px rgba(50,50,93,0.2), 0 18px 36px -18px rgba(0,0,0,0.25)",
        "stripe-orange": "0 20px 40px -12px rgba(255, 94, 0, 0.35)",
        "stripe-coral": "0 20px 40px -12px rgba(255, 101, 132, 0.35)",
        "stripe-dark": "0 20px 40px -15px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
