"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MyOrganization, User } from "@/lib/types";

interface OrgContextValue {
  user: User | null;
  orgs: MyOrganization[];
  orgId: number | null;
  setOrgId: (id: number) => void;
  loading: boolean;
  refreshOrgs: () => void;
}

const OrgContext = createContext<OrgContextValue>({
  user: null,
  orgs: [],
  orgId: null,
  setOrgId: () => {},
  loading: true,
  refreshOrgs: () => {},
});

const ORG_KEY = "jhinku_org_id";

export function OrgProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [orgs, setOrgs] = useState<MyOrganization[]>([]);
  const [orgId, setOrgIdState] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    Promise.all([
      api<User>("/auth/me"),
      api<MyOrganization[]>("/organizations"),
    ])
      .then(([u, o]) => {
        setUser(u);
        setOrgs(o);
        const saved = Number(localStorage.getItem(ORG_KEY));
        const chosen = o.find((x) => x.id === saved)?.id ?? o[0]?.id ?? null;
        setOrgIdState(chosen);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  function setOrgId(id: number) {
    setOrgIdState(id);
    localStorage.setItem(ORG_KEY, String(id));
  }

  return (
    <OrgContext.Provider
      value={{ user, orgs, orgId, setOrgId, loading, refreshOrgs: load }}
    >
      {children}
    </OrgContext.Provider>
  );
}

export function useOrg() {
  return useContext(OrgContext);
}
