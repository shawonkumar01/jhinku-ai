"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, clearTokens } from "@/lib/api";
import { OrgProvider, useOrg } from "@/components/OrgContext";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Organizations" },
  { href: "/dashboard/chatbots", label: "Chatbots" },
  { href: "/dashboard/knowledge", label: "Knowledge Base" },
  { href: "/dashboard/conversations", label: "Inbox" },
];

function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, orgs, orgId, setOrgId, loading } = useOrg();

  useEffect(() => {
    if (!getAccessToken()) router.replace("/login");
  }, [router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-gray-500">
        Loading…
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 flex-col border-r bg-gray-50">
        <div className="border-b px-4 py-4">
          <span className="text-lg font-bold text-indigo-600">Jhinku AI</span>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-3 py-2 text-sm font-medium ${
                pathname === item.href
                  ? "bg-indigo-100 text-indigo-700"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="border-t p-3 text-xs text-gray-500">
          {user?.email}
          <button
            className="mt-2 block text-indigo-600 hover:underline"
            onClick={() => {
              clearTokens();
              router.replace("/login");
            }}
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8">
        {orgs.length > 0 && (
          <div className="mb-6 flex items-center gap-3">
            <label className="text-sm font-medium text-gray-600">
              Organization:
            </label>
            <select
              className="rounded-lg border px-3 py-1.5 text-sm"
              value={orgId ?? ""}
              onChange={(e) => setOrgId(Number(e.target.value))}
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name} ({o.role})
                </option>
              ))}
            </select>
          </div>
        )}
        {children}
      </main>
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <OrgProvider>
      <Shell>{children}</Shell>
    </OrgProvider>
  );
}
