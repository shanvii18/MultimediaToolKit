"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, CheckCircle2, Loader2, LogIn, Sparkles, UserPlus } from "lucide-react";
import { ApiClient, Me, describeError } from "@/services/apiClient";

type Mode = "signin" | "signup";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    try {
      if (new URLSearchParams(window.location.search).get("mode") === "signup") setMode("signup");
    } catch (_) {}
    if (ApiClient.isSignedIn()) {
      ApiClient.getMe()
        .then((user) => user.auth_mode === "access_key" && setMe(user))
        .catch(() => undefined);
    }
  }, []);

  const switchMode = (next: Mode) => {
    setMode(next);
    setError(null);
    setConfirm("");
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setError("Please enter your email and password.");
      return;
    }
    if (mode === "signup") {
      if (password.length < 8) {
        setError("Password must be at least 8 characters.");
        return;
      }
      if (password !== confirm) {
        setError("The two passwords do not match.");
        return;
      }
    }
    setBusy(true);
    try {
      if (mode === "signup") await ApiClient.signUp(cleanEmail, password);
      else await ApiClient.signIn(cleanEmail, password);
      setMe(await ApiClient.getMe());
      window.dispatchEvent(new CustomEvent("mtk:signed-in"));
      router.push("/convert");
    } catch (err: any) {
      setError(describeError(err));
    } finally {
      setBusy(false);
    }
  };

  const tab = (value: Mode, label: string) => (
    <button
      type="button"
      onClick={() => switchMode(value)}
      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
        mode === value ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
      }`}
      aria-pressed={mode === value}
    >
      {label}
    </button>
  );

  const input =
    "w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-orange-500";

  return (
    <div className="p-4 sm:p-8 max-w-md mx-auto space-y-6 pt-16">
      <div className="text-center space-y-3">
        <div className="mx-auto h-12 w-12 rounded-2xl bg-gradient-to-tr from-orange-500 via-amber-500 to-rose-500 flex items-center justify-center shadow-lg shadow-orange-500/25">
          <Sparkles className="h-6 w-6 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-white">{mode === "signup" ? "Create your free account" : "Welcome back"}</h1>
        <p className="text-sm text-slate-400">
          {mode === "signup"
            ? "Sign up with your email to use all 20 conversions. Your files and history are private to your account."
            : "Sign in to convert files and see your private history and media library."}
        </p>
      </div>

      {me && (
        <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" /> Signed in as {me.email}
        </div>
      )}

      <form onSubmit={submit} className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex gap-1 p-1 rounded-xl bg-slate-950 border border-slate-800">
          {tab("signin", "Sign in")}
          {tab("signup", "Create account")}
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className={input}
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete={mode === "signup" ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={mode === "signup" ? "At least 8 characters" : "Your password"}
            className={input}
          />
        </div>
        {mode === "signup" && (
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="confirm">
              Confirm password
            </label>
            <input
              id="confirm"
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Repeat your password"
              className={input}
            />
          </div>
        )}

        {error && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-sm flex items-start gap-2">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        <button
          type="submit"
          disabled={busy}
          className="w-full px-6 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 disabled:opacity-50 text-white font-medium text-sm inline-flex items-center justify-center gap-2"
        >
          {busy ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : mode === "signup" ? (
            <UserPlus className="h-4 w-4" />
          ) : (
            <LogIn className="h-4 w-4" />
          )}
          <span>{busy ? "Please wait…" : mode === "signup" ? "Create account" : "Sign in"}</span>
        </button>
      </form>
      <p className="text-xs text-slate-500 text-center">
        {mode === "signup" ? "Already have an account? " : "New here? "}
        <button
          type="button"
          onClick={() => switchMode(mode === "signup" ? "signin" : "signup")}
          className="text-orange-400 hover:text-orange-300 font-medium"
        >
          {mode === "signup" ? "Sign in" : "Create a free account"}
        </button>
      </p>
    </div>
  );
}
