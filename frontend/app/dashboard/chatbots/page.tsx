"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useOrg } from "@/components/OrgContext";
import { Badge, Button, Card, EmptyState, Input, PageHeader } from "@/components/ui";
import { TestChat } from "@/components/TestChat";
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
  const [testing, setTesting] = useState<Chatbot | null>(null);

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
        body: JSON.stringify({ name, welcome_message: welcome || null }),
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
    return <EmptyState title="Create an organization first" />;
  }

  return (
    <div className="max-w-4xl">
      <PageHeader
        title="Chatbots"
        description="Each chatbot gets a widget ID — paste the snippet on any website to embed it."
      />

      <Card className="mb-6 p-5">
        <form onSubmit={create} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <Input
            required
            placeholder="Chatbot name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Input
            placeholder="Welcome message (optional)"
            value={welcome}
            onChange={(e) => setWelcome(e.target.value)}
          />
          <Button type="submit" disabled={busy}>
            {busy ? "Creating…" : "Create"}
          </Button>
        </form>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </Card>

      {bots.length === 0 ? (
        <EmptyState
          title="No chatbots yet"
          hint="Create one above, then upload knowledge documents."
        />
      ) : (
        <div className="space-y-4">
          {bots.map((b) => (
            <Card key={b.id} className="p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2.5">
                    <h3 className="font-semibold text-slate-900">{b.name}</h3>
                    <Badge tone={b.is_active ? "green" : "gray"}>
                      {b.is_active ? "active" : "inactive"}
                    </Badge>
                  </div>
                  <p className="mt-1 font-mono text-xs text-slate-400">
                    {b.public_widget_id}
                  </p>
                  {b.welcome_message && (
                    <p className="mt-2 text-sm text-slate-500">
                      “{b.welcome_message}”
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-4">
                <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-slate-400">
                  Embed snippet
                </p>
                <div className="flex items-start gap-2">
                  <pre className="flex-1 overflow-x-auto rounded-lg bg-slate-900 px-3.5 py-2.5 font-mono text-xs leading-relaxed text-slate-300">
                    {snippet(b.public_widget_id)}
                  </pre>
                  <Button
                    variant="secondary"
                    onClick={() => copy(b.id, snippet(b.public_widget_id))}
                    className="shrink-0 px-3 py-1.5 text-xs"
                  >
                    {copied === b.id ? "Copied ✓" : "Copy"}
                  </Button>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
                <span className="text-xs text-slate-400">
                  Chatbot ID: {b.id}
                </span>
                <Button
                  variant="secondary"
                  onClick={() => setTesting(b)}
                  className="px-3.5 py-1.5 text-xs"
                >
                  <svg
                    className="h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"
                    />
                  </svg>
                  Test chat
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {testing && <TestChat bot={testing} onClose={() => setTesting(null)} />}
    </div>
  );
}
