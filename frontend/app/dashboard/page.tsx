"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useOrg } from "@/components/OrgContext";

export default function OrganizationsPage() {
  const { orgs, orgId, refreshOrgs } = useOrg();
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/organizations", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      setName("");
      refreshOrgs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-xl font-bold">Organizations</h1>

      <form
        onSubmit={create}
        className="flex gap-2 rounded-xl border bg-white p-4"
      >
        <input
          required
          minLength={2}
          placeholder="New organization name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="flex-1 rounded-lg border px-3 py-2 text-sm"
        />
        <button
          disabled={busy}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Create
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-2">
        {orgs.length === 0 && (
          <p className="text-sm text-gray-500">
            No organizations yet — create one above. You become its owner.
          </p>
        )}
        {orgs.map((o) => (
          <div
            key={o.id}
            className={`flex items-center justify-between rounded-xl border bg-white p-4 ${
              o.id === orgId ? "border-indigo-400 ring-1 ring-indigo-200" : ""
            }`}
          >
            <div>
              <p className="font-medium">{o.name}</p>
              <p className="text-xs text-gray-500">Role: {o.role}</p>
            </div>
            <span className="text-xs text-gray-400">ID: {o.id}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
