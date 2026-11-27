"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getAccessToken, clearTokens } from "@/lib/api";
import { OrgProvider, useOrg } from "@/components/OrgContext";

const NAV = [
  {
    href: "/dashboard",
    label: "Organizations",
    icon: (
      <path d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
    ),
  },
  {
    href: "/dashboard/chatbots",
    label: "Chatbots",
    icon: (
      <path d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" />
    ),
  },
  {
    href: "/dashboard/knowledge",
    label: "Knowledge Base",
    icon: (
      <path d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
    ),
  },
  {
    href: "/dashboard/conversations",
    label: "Inbox",
    icon: (
      <path d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 1 1.68 2.432l-.72 13.84a2.125 2.125 0 0 1-2.432 1.68l-1.88-.393a48.29 48.29 0 0 0-9.349-.682 48.56 48.56 0 0 0-12.08.331l-1.92.392A2.125 2.125 0 0 1 3.93 21l-.72-13.84a2.126 2.126 0 0 1 1.68-2.432l18.36-4.79Z" />
    ),
  },
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
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600" />
      </div>
    );
  }

  const currentOrg = orgs.find((o) => o.id === orgId);

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 flex w-60 flex-col bg-slate-950">
        <Link
          href="/dashboard"
          className="flex items-center gap-2.5 px-5 pb-6 pt-6"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500 text-base font-bold text-white">
            J
          </div>
          <span className="text-[15px] font-semibold tracking-tight text-white">
            Jhinku AI
          </span>
        </Link>

        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((item) => {
            const active =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-white/10 text-white"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`}
              >
                <svg
                  className="h-4.5 w-4.5 shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.8}
                  stroke="currentColor"
                >
                  {item.icon}
                </svg>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-white/10 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-500/20 text-xs font-semibold text-indigo-300">
              {(user?.full_name || user?.email || "?")
                .slice(0, 1)
                .toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-white">
                {user?.full_name || user?.email}
              </p>
              <p className="truncate text-[11px] text-slate-500">{user?.email}</p>
            </div>
            <button
              title="Sign out"
              onClick={() => {
                clearTokens();
                router.replace("/login");
              }}
              className="rounded-md p-1.5 text-slate-500 transition hover:bg-white/10 hover:text-white"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.8}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9"
                />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="ml-60 flex min-h-screen flex-1 flex-col">
        {/* Top bar */}
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-slate-200/70 bg-[#f6f7f9]/80 px-8 backdrop-blur">
          {orgs.length > 0 ? (
            <div className="flex items-center gap-2.5">
              <span className="text-sm text-slate-500">Workspace</span>
              <div className="relative">
                <select
                  value={orgId ?? ""}
                  onChange={(e) => setOrgId(Number(e.target.value))}
                  className="appearance-none rounded-lg border border-slate-200 bg-white py-1.5 pl-3 pr-8 text-sm font-medium text-slate-800 shadow-sm outline-none transition hover:border-slate-300 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                >
                  {orgs.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.name}
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
              {currentOrg && (
                <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] font-medium capitalize text-indigo-600">
                  {currentOrg.role}
                </span>
              )}
            </div>
          ) : (
            <span className="text-sm text-slate-400">
              Create an organization to get started
            </span>
          )}
        </header>

        <main className="flex-1 px-8 py-7">{children}</main>
      </div>
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
