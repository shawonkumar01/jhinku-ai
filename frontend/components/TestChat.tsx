"use client";

import { useEffect, useRef, useState } from "react";
import type { Chatbot } from "@/lib/types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type ChatMessage = {
  id: number;
  sender_type: "customer" | "ai" | "agent" | "system";
  content: string;
};

type PublicConfig = {
  name: string;
  welcome_message: string | null;
  branding: Record<string, unknown> | null;
};

async function publicApi<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export function TestChat({
  bot,
  onClose,
}: {
  bot: Chatbot;
  onClose: () => void;
}) {
  const [config, setConfig] = useState<PublicConfig | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [customerId] = useState(
    () => `dashboard-test-${crypto.randomUUID().slice(0, 8)}`
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [handoffDone, setHandoffDone] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load public config + start a conversation.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const cfg = await publicApi<PublicConfig>(
          `/public/chatbots/${bot.public_widget_id}`
        );
        if (cancelled) return;
        setConfig(cfg);
        const conv = await publicApi<{ public_id: string }>(
          `/public/chatbots/${bot.public_widget_id}/conversations`,
          {
            method: "POST",
            body: JSON.stringify({ customer_identifier: customerId }),
          }
        );
        if (cancelled) return;
        setConversationId(conv.public_id);
        if (cfg.welcome_message) {
          setMessages([
            {
              id: -1,
              sender_type: "ai",
              content: cfg.welcome_message,
            },
          ]);
        }
      } catch (e) {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Failed to start chat");
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bot.public_widget_id]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages.length, sending]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || !conversationId || sending) return;
    setInput("");
    setSending(true);
    setError("");
    setMessages((m) => [
      ...m,
      {
        id: Date.now(),
        sender_type: "customer",
        content: text,
      },
    ]);
    try {
      const reply = await publicApi<ChatMessage>(
        `/public/conversations/${conversationId}/messages`,
        {
          method: "POST",
          body: JSON.stringify({
            customer_identifier: customerId,
            content: text,
          }),
        }
      );
      setMessages((m) => [...m, reply]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send");
    } finally {
      setSending(false);
    }
  }

  async function handoff() {
    if (!conversationId) return;
    try {
      await publicApi(`/public/conversations/${conversationId}/handoff`, {
        method: "POST",
        body: JSON.stringify({ customer_identifier: customerId }),
      });
      setHandoffDone(true);
      setMessages((m) => [
        ...m,
        {
          id: Date.now(),
          sender_type: "system",
          content: "You requested a human agent — someone will join soon.",
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Handoff failed");
    }
  }

  const accent =
    (config?.branding?.primary_color as string | undefined) ?? "#4f46e5";

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div
        className="absolute inset-0 bg-slate-950/30"
        onClick={onClose}
      />
      <div className="relative flex h-full w-full max-w-md flex-col bg-white shadow-2xl">
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-4 text-white"
          style={{ backgroundColor: accent }}
        >
          <div>
            <p className="font-semibold">{config?.name ?? bot.name}</p>
            <p className="text-xs opacity-80">Test chat — preview mode</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 transition hover:bg-white/20"
            aria-label="Close"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18 18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 space-y-2.5 overflow-y-auto bg-slate-50 p-4">
          {messages.map((m) =>
            m.sender_type === "system" ? (
              <p
                key={m.id}
                className="py-1 text-center text-[11px] italic text-slate-400"
              >
                {m.content}
              </p>
            ) : (
              <div
                key={m.id}
                className={`flex ${m.sender_type === "customer" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-sm shadow-sm ${
                    m.sender_type === "customer"
                      ? "rounded-br-md text-white"
                      : "rounded-bl-md border border-slate-200 bg-white text-slate-800"
                  }`}
                  style={
                    m.sender_type === "customer"
                      ? { backgroundColor: accent }
                      : undefined
                  }
                >
                  {m.content}
                </div>
              </div>
            )
          )}
          {sending && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-400 shadow-sm">
                <span className="inline-flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
                </span>
              </div>
            </div>
          )}
          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
              {error}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 bg-white p-3.5">
          {!handoffDone && conversationId && (
            <button
              onClick={handoff}
              className="mb-2.5 text-xs font-medium text-slate-500 transition hover:text-indigo-600"
            >
              Talk to a human agent →
            </button>
          )}
          <form onSubmit={send} className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message…"
              disabled={!conversationId}
              className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={sending || !input.trim() || !conversationId}
              className="rounded-xl px-4 py-2.5 text-sm font-medium text-white transition disabled:opacity-50"
              style={{ backgroundColor: accent }}
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
