"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, CheckCircle2, KeyRound, Loader2, LogIn } from "lucide-react";
import { ApiClient, Me } from "@/services/apiClient";

/** Accepts either a raw key (mtk_...) or a full invite link (...?access_key=mtk_...). */
function extractKey(input: string): string {
  const value = input.trim();
  try {
    const url = new URL(value);
    return (url.searchParams.get("access_key") || "").trim();
  } catch (_) {
    return value;
  }
}

export default function LoginPage() {
  const router = useRouter();
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    if (ApiClient.hasAccessKey()) {
      ApiClient.getMe()
        .then((user) => user.auth_mode === "access_key" && setMe(user))
        .catch(() => undefined);
    }
  }, []);

  const signIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const key = extractKey(value);
    if (!key) {
      setError("Paste your personal access key or invite link.");
      return;
    }
    setBusy(true);
    let previous: string | null = null;
    try {
      previous = window.localStorage.getItem("mtk_access_key");
    } catch (_) {}
    ApiClient.setAccessKey(key);
    try {
      const user = await ApiClient.getMe();
      setMe(user);
      window.dispatchEvent(new CustomEvent("mtk:signed-in"));
      router.push("/convert");
    } catch (err: any) {
      // Never lose a previously working key because of a typo.
      if (previous) ApiClient.setAccessKey(previous);
      else ApiClient.clearAccessKey();
      setError(err.message || "That access key was not accepted.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-4 sm:p-8 max-w-md mx-auto space-y-6 pt-16">
      <div className="text-center space-y-3">
        <div className="mx-auto h-12 w-12 rounded-2xl bg-gradient-to-tr from-orange-500 via-amber-500 to-rose-500 flex items-center justify-center shadow-lg shadow-orange-500/25">
          <KeyRound className="h-6 w-6 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-white">Sign in</h1>
        <p className="text-sm text-slate-400">
          MultimediaToolKit is invite-only. Paste the personal access key or invite link you received. Your files and
          history are private to your key.
        </p>
      </div>

      {me && (
        <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" /> Signed in as {me.email}
        </div>
      )}

      <form onSubmit={signIn} className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="key">
          Access key or invite link
        </label>
        <input
          id="key"
          type="password"
          autoComplete="off"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="mtk_…"
          className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-orange-500"
        />
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
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
          <span>{busy ? "Checking…" : "Sign in"}</span>
        </button>
      </form>
      <p className="text-xs text-slate-500 text-center">
        No key? Ask the site owner for an invite. Keys are created with <code>python -m app.cli invite</code>.
      </p>
    </div>
  );
}
