"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, setTokens } from "@/lib/api";
import { AuthShell } from "@/components/AuthShell";
import { Button, Input } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api<{ access_token: string; refresh_token: string }>(
        "/auth/login",
        { method: "POST", body: JSON.stringify({ email, password }) }
      );
      setTokens(data.access_token, data.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell>
      <div className="mb-8 lg:hidden">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-lg font-bold text-white">
            J
          </div>
          <span className="text-lg font-semibold text-slate-900">Jhinku AI</span>
        </div>
      </div>

      <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
        Welcome back
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Sign in to manage your chatbots.
      </p>

      <form onSubmit={submit} className="mt-8 space-y-4">
        {error && (
          <p className="rounded-lg bg-red-50 px-3.5 py-2.5 text-sm text-red-600 ring-1 ring-red-600/10">
            {error}
          </p>
        )}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700">Email</label>
          <Input
            type="email"
            required
            autoComplete="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700">Password</label>
          <Input
            type="password"
            required
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <Button type="submit" disabled={busy} className="w-full py-2.5">
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500">
        No account?{" "}
        <Link href="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
          Create one free
        </Link>
      </p>
    </AuthShell>
  );
}
