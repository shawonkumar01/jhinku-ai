"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useOrg } from "@/components/OrgContext";
import type {
  AgentMessage,
  Conversation,
  ConversationDetail,
  ConversationStatus,
} from "@/lib/types";

const STATUSES: (ConversationStatus | "")[] = [
  "",
  "active",
  "waiting_human",
  "human",
  "closed",
];

const STATUS_STYLE: Record<string, string> = {
  active: "bg-blue-100 text-blue-700",
  waiting_human: "bg-yellow-100 text-yellow-700",
  human: "bg-purple-100 text-purple-700",
  closed: "bg-gray-100 text-gray-500",
};

function Bubble({ m }: { m: AgentMessage }) {
  const mine = m.sender_type === "agent";
  const isSystem = m.sender_type === "system";
  if (isSystem) {
    return (
      <p className="py-1 text-center text-xs italic text-gray-400">
        {m.content}
      </p>
    );
  }
  return (
    <div
      className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
        mine
          ? "self-end bg-indigo-600 text-white"
          : m.sender_type === "ai"
            ? "self-start border bg-white"
            : "self-start bg-gray-200"
      } ${m.is_internal ? "opacity-70" : ""}`}
    >
      {m.is_internal && (
        <span className="mb-1 block text-[10px] uppercase text-amber-300">
          internal note
        </span>
      )}
      {m.sender_type === "agent" && !mine && (
        <span className="mb-1 block text-[10px] uppercase text-gray-400">
          agent
        </span>
      )}
      <p className="whitespace-pre-wrap">{m.content}</p>
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

  const load = useCallback(() => {
    if (!orgId) return;
    const params = statusFilter ? `?status=${statusFilter}` : "";
    api<Conversation[]>(`/organizations/${orgId}/conversations${params}`)
      .then(setConvs)
      .catch((e) => setError(e.message));
  }, [orgId, statusFilter]);

  useEffect(load, [load]);

  async function openConversation(id: number) {
    if (!orgId) return;
    const detail = await api<ConversationDetail>(
      `/organizations/${orgId}/conversations/${id}`
    );
    setSelected(detail);
    setReply("");
    setInternal(false);
  }

  async function sendReply(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId || !selected || !reply.trim()) return;
    await api(
      `/organizations/${orgId}/conversations/${selected.id}/messages`,
      {
        method: "POST",
        body: JSON.stringify({ content: reply, is_internal: internal }),
      }
    );
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
    return <p className="text-gray-500">Create an organization first.</p>;
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Inbox list */}
      <div className="flex w-80 flex-col rounded-xl border bg-white">
        <div className="border-b p-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full rounded-lg border px-2 py-1.5 text-sm"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s === "" ? "All statuses" : s.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1 overflow-y-auto">
          {convs.map((c) => (
            <button
              key={c.id}
              onClick={() => openConversation(c.id)}
              className={`block w-full border-b p-3 text-left hover:bg-gray-50 ${
                selected?.id === c.id ? "bg-indigo-50" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-gray-500">
                  {c.customer_identifier.slice(0, 16)}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] ${STATUS_STYLE[c.status]}`}
                >
                  {c.status.replace("_", " ")}
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-400">
                {new Date(c.updated_at).toLocaleString()}
              </p>
            </button>
          ))}
          {convs.length === 0 && (
            <p className="p-4 text-sm text-gray-500">No conversations.</p>
          )}
        </div>
      </div>

      {/* Chat pane */}
      <div className="flex flex-1 flex-col rounded-xl border bg-white">
        {!selected ? (
          <div className="flex flex-1 items-center justify-center text-sm text-gray-400">
            Select a conversation
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between border-b p-3">
              <div className="text-sm">
                <span className="font-mono">{selected.customer_identifier}</span>
                {selected.assigned_agent_id && (
                  <span className="ml-2 text-xs text-gray-400">
                    agent #{selected.assigned_agent_id}
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={assign}
                  className="rounded-lg border px-3 py-1 text-xs hover:bg-gray-50"
                >
                  Assign to me
                </button>
                <select
                  value={selected.status}
                  onChange={(e) =>
                    setStatus(e.target.value as ConversationStatus)
                  }
                  className="rounded-lg border px-2 py-1 text-xs"
                >
                  {STATUSES.filter(Boolean).map((s) => (
                    <option key={s} value={s}>
                      {s?.replace("_", " ")}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex flex-1 flex-col gap-2 overflow-y-auto bg-gray-50 p-4">
              {selected.messages.map((m) => (
                <Bubble key={m.id} m={m} />
              ))}
            </div>

            <form
              onSubmit={sendReply}
              className="border-t p-3"
            >
              <div className="mb-2 flex items-center gap-2 text-xs">
                <label className="flex items-center gap-1 text-gray-500">
                  <input
                    type="checkbox"
                    checked={internal}
                    onChange={(e) => setInternal(e.target.checked)}
                  />
                  Internal note (customer can't see)
                </label>
              </div>
              <div className="flex gap-2">
                <input
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  placeholder={
                    internal ? "Write a private note…" : "Reply to customer…"
                  }
                  className="flex-1 rounded-lg border px-3 py-2 text-sm"
                />
                <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
                  Send
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
