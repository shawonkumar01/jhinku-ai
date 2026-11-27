"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useOrg } from "@/components/OrgContext";
import type { Chatbot } from "@/lib/types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const BACKEND_ORIGIN = API_URL.replace(/\/api\/v1$/, "");

export default function ChatbotsPage() {
  const { orgId } = useOrg();
  const [bots, setBots] = useState<Chatbot[]>([]);
  const [name, setName] = useState("");
  const [welcome, setWelcome] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState<number | null>(null);

  const load = useCallback(() => {
    if (!orgId) return;
    api<Chatbot[]>(`/organizations/${orgId}/chatbots`)
      .then(setBots)
      .catch((e) => setError(e.message));
  }, [orgId]);

  useEffect(load, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId) return;
    setBusy(true);
    setError("");
    try {
      await api(`/organizations/${orgId}/chatbots`, {
        method: "POST",
        body: JSON.stringify({
          name,
          welcome_message: welcome || null,
        }),
      });
      setName("");
      setWelcome("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  function snippet(widgetId: string) {
    return `<script src="${BACKEND_ORIGIN}/widget.js"\n        data-chatbot-id="${widgetId}" async></script>`;
  }

  function copy(id: number, text: string) {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 1500);
  }

  if (!orgId) {
    return <p className="text-gray-500">Create an organization first.</p>;
  }

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-xl font-bold">Chatbots</h1>

      <form
        onSubmit={create}
        className="space-y-2 rounded-xl border bg-white p-4"
      >
        <input
          required
          placeholder="Chatbot name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-lg border px-3 py-2 text-sm"
        />
        <input
          placeholder="Welcome message (optional)"
          value={welcome}
          onChange={(e) => setWelcome(e.target.value)}
          className="w-full rounded-lg border px-3 py-2 text-sm"
        />
        <button
          disabled={busy}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Create chatbot
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {bots.map((b) => (
          <div key={b.id} className="rounded-xl border bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{b.name}</p>
                <p className="font-mono text-xs text-gray-500">
                  {b.public_widget_id}
                </p>
              </div>
              <span
                className={`rounded-full px-2 py-0.5 text-xs ${
                  b.is_active
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-500"
                }`}
              >
                {b.is_active ? "active" : "inactive"}
              </span>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <code className="flex-1 overflow-x-auto rounded bg-gray-100 p-2 text-xs">
                {snippet(b.public_widget_id)}
              </code>
              <button
                onClick={() => copy(b.id, snippet(b.public_widget_id))}
                className="shrink-0 rounded-lg border px-3 py-1.5 text-xs hover:bg-gray-50"
              >
                {copied === b.id ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>
        ))}
        {bots.length === 0 && (
          <p className="text-sm text-gray-500">No chatbots yet.</p>
        )}
      </div>
    </div>
  );
}
