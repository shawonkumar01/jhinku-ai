"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, apiUpload } from "@/lib/api";
import { useOrg } from "@/components/OrgContext";
import type { KnowledgeSource } from "@/lib/types";

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export default function KnowledgePage() {
  const { orgId } = useOrg();
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    if (!orgId) return;
    api<KnowledgeSource[]>(`/organizations/${orgId}/knowledge-sources`)
      .then(setSources)
      .catch((e) => setError(e.message));
  }, [orgId]);

  useEffect(load, [load]);

  // Poll while anything is still processing.
  useEffect(() => {
    const active = sources.some(
      (s) => s.processing_status === "pending" || s.processing_status === "processing"
    );
    if (!active) return;
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [sources, load]);

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file || !orgId) return;
    setUploading(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      await apiUpload(`/organizations/${orgId}/knowledge-sources`, form);
      if (fileRef.current) fileRef.current.value = "";
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function remove(id: number) {
    if (!orgId) return;
    if (!confirm("Delete this document and its chunks?")) return;
    await api(`/organizations/${orgId}/knowledge-sources/${id}`, {
      method: "DELETE",
    });
    load();
  }

  if (!orgId) {
    return <p className="text-gray-500">Create an organization first.</p>;
  }

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-xl font-bold">Knowledge Base</h1>
      <p className="text-sm text-gray-500">
        Upload PDFs, TXT or DOCX files (max 10MB). The AI learns from them.
      </p>

      <form
        onSubmit={upload}
        className="flex items-center gap-3 rounded-xl border bg-white p-4"
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.txt,.docx"
          required
          className="text-sm"
        />
        <button
          disabled={uploading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {uploading ? "Uploading…" : "Upload"}
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-2">
        {sources.map((s) => (
          <div
            key={s.id}
            className="flex items-center justify-between rounded-xl border bg-white p-4"
          >
            <div>
              <p className="font-medium">{s.title}</p>
              <p className="text-xs text-gray-500">
                {s.original_filename} · {(s.file_size / 1024).toFixed(0)} KB ·{" "}
                {s.chunk_count} chunks
              </p>
              {s.error_message && (
                <p className="text-xs text-red-500">{s.error_message}</p>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`rounded-full px-2 py-0.5 text-xs ${STATUS_STYLE[s.processing_status]}`}
              >
                {s.processing_status}
              </span>
              <button
                onClick={() => remove(s.id)}
                className="text-xs text-red-600 hover:underline"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        {sources.length === 0 && (
          <p className="text-sm text-gray-500">No documents uploaded yet.</p>
        )}
      </div>
    </div>
  );
}
