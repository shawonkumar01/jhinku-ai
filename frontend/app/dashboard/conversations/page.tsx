"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useOrg } from "@/components/OrgContext";
import { Badge, Button, Card, EmptyState, PageHeader } from "@/components/ui";
import type {
  AgentMessage,
  Conversation,
  ConversationDetail,
  ConversationStatus,
} from "@/lib/types";

const STATUSES: (ConversationStatus | "")[] = [
  "",
  "waiting_human",
  "active",
  "human",
  "closed",
];

const STATUS_TONE: Record<ConversationStatus, "yellow" | "blue" | "purple" | "gray"> = {
  active: "blue",
  waiting_human: "yellow",
  human: "purple",
  closed: "gray",
};

function Bubble({ m }: { m: AgentMessage }) {
  if (m.sender_type === "system") {
    return (
      <p className="py-1 text-center text-[11px] italic text-slate-400">
        {m.content}
      </p>
    );
  }
  const mine = m.sender_type === "agent";
  const ai = m.sender_type === "ai";
  return (
    <div
      className={`flex ${mine ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[75%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed shadow-sm ${
          mine
            ? "rounded-br-md bg-indigo-600 text-white"
            : ai
              ? "rounded-bl-md border border-slate-200 bg-white text-slate-800"
              : "rounded-bl-md bg-slate-100 text-slate-800"
        } ${m.is_internal ? "opacity-75" : ""}`}
      >
        <div className="mb-0.5 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wide opacity-70">
          {m.is_internal ? "internal note" : m.sender_type}
        </div>
        <p className="whitespace-pre-wrap">{m.content}</p>
        <p
          className={`mt-1 text-right text-[10px] ${
            mine ? "text-indigo-200" : "text-slate-400"
          }`}
        >
          {new Date(m.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}

export default function ConversationsPage() {
  const { orgId } = useOrg();
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [selected, setSelected] = useState<ConversationDetail | null>(null);
  const [reply, setReply] = useState("");
  const [internal, setInternal] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const load = useCallback(() => {
    if (!orgId) return;
    const params = statusFilter ? `?status=${statusFilter}` : "";
    api<Conversation[]>(`/organizations/${orgId}/conversations${params}`)
      .then(setConvs)
      .catch((e) => setError(e.message));
  }, [orgId, statusFilter]);

  useEffect(load, [load]);

  const openConversation = useCallback(
    async (id: number) => {
      if (!orgId) return;
      const detail = await api<ConversationDetail>(
        `/organizations/${orgId}/conversations/${id}`
      );
      setSelected(detail);
      setReply("");
      setInternal(false);
    },
    [orgId]
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [selected?.messages.length]);

  async function sendReply(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId || !selected || !reply.trim()) return;
    await api(`/organizations/${orgId}/conversations/${selected.id}/messages`, {
      method: "POST",
      body: JSON.stringify({ content: reply, is_internal: internal }),
    });
    setReply("");
    openConversation(selected.id);
    load();
  }

  async function assign() {
    if (!orgId || !selected) return;
    await api(`/organizations/${orgId}/conversations/${selected.id}/assign`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    openConversation(selected.id);
    load();
  }

  async function setStatus(status: ConversationStatus) {
    if (!orgId || !selected) return;
    await api(`/organizations/${orgId}/conversations/${selected.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    openConversation(selected.id);
    load();
  }

  if (!orgId) {
    return <EmptyState title="Create an organization first" />;
  }

  return (
    <div className="-mx-8 -my-7 flex h-[calc(100vh-3.5rem)]">
      {/* Inbox list */}
      <div className="flex w-80 shrink-0 flex-col border-r border-slate-200/70 bg-white">
        <div className="border-b border-slate-100 p-3.5">
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full appearance-none rounded-lg border border-slate-200 bg-white py-2 pl-3 pr-8 text-sm text-slate-700 outline-none transition hover:border-slate-300 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s === "" ? "All conversations" : s.replace("_", " ")}
                </option>
              ))}
            </select>
            <svg
              className="pointer-events-none absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m19.5 8.25-7.5 7.5-7.5-7.5"
              />
            </svg>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {convs.map((c) => (
            <button
              key={c.id}
              onClick={() => openConversation(c.id)}
              className={`block w-full border-b border-slate-50 px-4 py-3.5 text-left transition hover:bg-slate-50 ${
                selected?.id === c.id ? "bg-indigo-50/60" : ""
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-mono text-xs text-slate-500">
                  {c.customer_identifier.slice(0, 18)}
                </span>
                <Badge tone={STATUS_TONE[c.status]}>
                  {c.status.replace("_", " ")}
                </Badge>
              </div>
              <p className="mt-1.5 text-xs text-slate-400">
                {new Date(c.updated_at).toLocaleString([], {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </button>
          ))}
          {convs.length === 0 && !error && (
            <p className="p-6 text-center text-sm text-slate-400">
              No conversations match this filter.
            </p>
          )}
        </div>
      </div>

      {/* Chat pane */}
      <div className="flex min-w-0 flex-1 flex-col bg-[#f6f7f9]">
        {!selected ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-2 text-slate-400">
            <svg
              className="h-10 w-10 text-slate-300"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"
              />
            </svg>
            <p className="text-sm">Select a conversation to view it</p>
          </div>
        ) : (
          <>
            {/* Chat header */}
            <div className="flex items-center justify-between border-b border-slate-200/70 bg-white px-5 py-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-600">
                  {selected.customer_identifier.slice(0, 1).toUpperCase()}
                </div>
                <div>
                  <p className="font-mono text-sm text-slate-800">
                    {selected.customer_identifier}
                  </p>
                  <p className="text-xs text-slate-400">
                    {selected.assigned_agent_id
                      ? `Assigned to agent #${selected.assigned_agent_id}`
                      : "Unassigned"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="secondary" onClick={assign} className="px-3 py-1.5 text-xs">
                  Assign to me
                </Button>
                <div className="relative">
                  <select
                    value={selected.status}
                    onChange={(e) =>
                      setStatus(e.target.value as ConversationStatus)
                    }
                    className="appearance-none rounded-lg border border-slate-200 bg-white py-1.5 pl-3 pr-7 text-xs font-medium text-slate-700 outline-none transition hover:border-slate-300 focus:border-indigo-400"
                  >
                    {STATUSES.filter(Boolean).map((s) => (
                      <option key={s} value={s}>
                        {s?.replace("_", " ")}
                      </option>
                    ))}
                  </select>
                  <svg
                    className="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-slate-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="m19.5 8.25-7.5 7.5-7.5-7.5"
                    />
                  </svg>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div
              ref={scrollRef}
              className="flex flex-1 flex-col gap-2.5 overflow-y-auto px-6 py-5"
            >
              {selected.messages.map((m) => (
                <Bubble key={m.id} m={m} />
              ))}
            </div>

            {/* Composer */}
            <form
              onSubmit={sendReply}
              className="border-t border-slate-200/70 bg-white px-5 py-3.5"
            >
              <div className="mb-2.5 flex items-center justify-between">
                <label className="flex cursor-pointer items-center gap-2 text-xs text-slate-500">
                  <input
                    type="checkbox"
                    checked={internal}
                    onChange={(e) => setInternal(e.target.checked)}
                    className="h-3.5 w-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  Internal note — hidden from customer
                </label>
                {internal && <Badge tone="yellow">private</Badge>}
              </div>
              <div className="flex gap-2.5">
                <input
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  placeholder={
                    internal
                      ? "Write a note for your team…"
                      : "Type a reply… (Enter to send)"
                  }
                  className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100"
                />
                <Button type="submit" disabled={!reply.trim()} className="px-5">
                  Send
                </Button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
