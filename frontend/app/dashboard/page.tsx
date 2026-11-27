"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useOrg } from "@/components/OrgContext";
import { Badge, Button, Card, EmptyState, Input, PageHeader } from "@/components/ui";

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
    <div className="max-w-4xl">
      <PageHeader
        title="Organizations"
        description="Each organization is a separate workspace with its own chatbots, knowledge and team."
      />

      <Card className="mb-6 p-5">
        <form onSubmit={create} className="flex items-end gap-3">
          <div className="flex-1">
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              New organization
            </label>
            <Input
              required
              minLength={2}
              placeholder="e.g. Acme Corp"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <Button type="submit" disabled={busy}>
            {busy ? "Creating…" : "Create"}
          </Button>
        </form>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </Card>

      {orgs.length === 0 ? (
        <EmptyState
          title="No organizations yet"
          hint="Create one above — you'll automatically become its owner."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {orgs.map((o) => (
            <Card
              key={o.id}
              className={`p-5 transition ${
                o.id === orgId
                  ? "ring-2 ring-indigo-500/60 border-indigo-200"
                  : "hover:border-slate-300"
              }`}
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-lg font-bold text-indigo-600">
                {o.name.slice(0, 1).toUpperCase()}
              </div>
              <p className="mt-3 font-medium text-slate-900">{o.name}</p>
              <div className="mt-2 flex items-center justify-between">
                <Badge tone="blue" >{o.role}</Badge>
                {o.id === orgId && <Badge tone="green">current</Badge>}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
