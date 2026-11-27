"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, apiUpload } from "@/lib/api";
import { useOrg } from "@/components/OrgContext";
import { Badge, Button, Card, EmptyState, PageHeader } from "@/components/ui";
import type { KnowledgeSource, ProcessingStatus } from "@/lib/types";

const STATUS_TONE: Record<ProcessingStatus, "gray" | "blue" | "green" | "red" | "yellow"> = {
  pending: "yellow",
  processing: "blue",
  completed: "green",
  failed: "red",
};

export default function KnowledgePage() {
  const { orgId } = useOrg();
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    if (!orgId) return;
    api<KnowledgeSource[]>(`/organizations/${orgId}/knowledge-sources`)
      .then(setSources)
      .catch((e) => setError(e.message));
  }, [orgId]);

  useEffect(load, [load]);

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
      setFileName("");
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
    return <EmptyState title="Create an organization first" />;
  }

  return (
    <div className="max-w-4xl">
      <PageHeader
        title="Knowledge Base"
        description="Upload PDFs, TXT or DOCX files (max 10MB). The AI answers only from what you upload."
      />

      <Card className="mb-6 p-5">
        <form onSubmit={upload} className="flex items-center gap-3">
          <label className="flex flex-1 cursor-pointer items-center gap-3 rounded-lg border border-dashed border-slate-300 px-4 py-3 transition hover:border-indigo-400 hover:bg-indigo-50/40">
            <svg
              className="h-5 w-5 shrink-0 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.8}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"
              />
            </svg>
            <span className="truncate text-sm text-slate-500">
              {fileName || "Choose a file…"}
            </span>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.txt,.docx"
              required
              className="hidden"
              onChange={(e) => setFileName(e.target.files?.[0]?.name ?? "")}
            />
          </label>
          <Button type="submit" disabled={uploading}>
            {uploading ? "Uploading…" : "Upload"}
          </Button>
        </form>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </Card>

      {sources.length === 0 ? (
        <EmptyState
          title="No documents yet"
          hint="Upload your first document — processing takes a few seconds."
        />
      ) : (
        <Card className="divide-y divide-slate-100">
          {sources.map((s) => (
            <div key={s.id} className="flex items-center gap-4 px-5 py-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.8}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                  />
                </svg>
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-slate-900">{s.title}</p>
                <p className="text-xs text-slate-400">
                  {s.original_filename} · {(s.file_size / 1024).toFixed(0)} KB ·{" "}
                  {s.chunk_count} chunks
                </p>
                {s.error_message && (
                  <p className="mt-0.5 text-xs text-red-500">{s.error_message}</p>
                )}
              </div>
              <Badge tone={STATUS_TONE[s.processing_status]}>
                {s.processing_status}
              </Badge>
              <Button variant="ghost" onClick={() => remove(s.id)} className="px-2.5 text-xs text-red-600 hover:bg-red-50">
                Delete
              </Button>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
